"""Demo-twin FastAPI service — physics loop + HTTP command endpoints.

Lifespan:
  startup  — seed RNG, connect NATS, start 5 Hz physics_loop task
  shutdown — cancel loop, drain NATS

Command endpoints (TWIN-05 — mutate the shared in-memory EngineState):
  POST /setpoints  — partial setpoint update (pydantic range-clamped → 422 on violation)
  POST /fault      — inject snap_tool (latched) or hard_spot (transient)
  POST /reset      — restore OP-20 nominal + re-seed RNG

Concurrency: no lock needed.  The physics loop and HTTP handlers both run on
the same single asyncio event loop thread.  Uvicorn MUST run with --workers 1
(see Dockerfile CMD) so there is only one EngineState copy per process.
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import get_config
from .engine import EngineState, compute_tick
from . import physics
from .publisher import connect_nats, drain_nats, publish_tick

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("demo_twin")

# ---------------------------------------------------------------------------
# Module-level shared state (read by physics_loop, mutated by HTTP handlers)
# ---------------------------------------------------------------------------

settings = get_config()
engine_state = EngineState()


# ---------------------------------------------------------------------------
# Physics loop (PUB-01: 5 Hz, 12 signals per tick)
# ---------------------------------------------------------------------------

async def physics_loop(nc, state: EngineState) -> None:  # type: ignore[type-arg]
    """Advance the engine and publish 12 neutral envelopes every tick.

    Wraps compute_tick + publish_tick in try/except so a single bad tick
    logs and continues — the loop is never allowed to exit on a transient error.
    """
    source = settings.source
    interval = settings.publish_interval_sec
    while True:
        t0 = asyncio.get_event_loop().time()
        try:
            signals = compute_tick(state, dt=interval)
            ts_ms = physics.now_ms()
            await publish_tick(nc, signals, source, ts_ms)
        except Exception:
            logger.exception("physics_loop: tick failed — continuing")
        elapsed = asyncio.get_event_loop().time() - t0
        await asyncio.sleep(max(0.0, interval - elapsed))


# ---------------------------------------------------------------------------
# FastAPI lifespan — modern asynccontextmanager form (per FastAPI >=0.93 best practice)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    physics.reset_rng(settings.rng_seed)
    # A broker that is down at startup (common docker-compose race) self-heals:
    # connect_nats uses max_reconnect_attempts=-1 so it retries indefinitely
    # until the broker is up (WR-02).  The try/except only fires on an
    # unexpected non-connection error (e.g. bad URL scheme); in that case
    # degrade gracefully — HTTP command API stays up, publishing pauses.
    # publish_tick tolerates nc=None and the physics loop keeps advancing.
    try:
        nc = await connect_nats(settings.nats_url)
    except Exception:
        logger.exception(
            "Initial NATS connect failed (%s) — starting without publisher",
            settings.nats_url,
        )
        nc = None
    task = asyncio.create_task(physics_loop(nc, engine_state))
    logger.info(
        "Twin started — 5 Hz loop running, NATS=%s (connected=%s)",
        settings.nats_url,
        nc is not None,
    )
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    if nc is not None:
        await drain_nats(nc)
    logger.info("Twin stopped")


app = FastAPI(title="Demo Twin", lifespan=lifespan)

# ---------------------------------------------------------------------------
# CORS middleware — origins are env-driven via settings.cors_allow_origins
# (B-04; defaults to Progress host + Quasar dev server; no wildcard).
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


# ---------------------------------------------------------------------------
# HTTP command endpoints (TWIN-05)
# ---------------------------------------------------------------------------

class SetpointsPayload(BaseModel):
    """Partial setpoint update.  Omitted fields are left unchanged.

    Field ranges enforce safety constraints (T-02-07):
      n  in [1000, 30000] — prevents divide-by-zero and unrealistic RPM
      fz in [0.01, 0.5]  — prevents near-zero or runaway feed
      ap in [0.1, 20]    — realistic axial depth range
      ae in [1, 100]     — realistic radial width range
      wear in [0.0, 1.0] — fraction; 0 = new tool, 1 = fully worn
      coolant_temp_sp in [0, 80] — °C; matches compose env range
    """
    n: float | None = Field(default=None, ge=1000, le=30000)
    fz: float | None = Field(default=None, ge=0.01, le=0.5)
    ap: float | None = Field(default=None, ge=0.1, le=20)
    ae: float | None = Field(default=None, ge=1, le=100)
    wear: float | None = Field(default=None, ge=0.0, le=1.0)
    coolant_temp_sp: float | None = Field(default=None, ge=0, le=80)


class FaultPayload(BaseModel):
    """Fault injection request.  Only known fault names are accepted (T-02-08)."""
    fault: Literal["snap_tool", "hard_spot"]


@app.post("/setpoints")
async def update_setpoints(payload: SetpointsPayload) -> dict:
    """Apply a partial setpoint update to the live engine state."""
    data = payload.model_dump(exclude_none=True)
    for k, v in data.items():
        setattr(engine_state, k, v)
    logger.info("Setpoints updated: %s", data)
    return {"ok": True, "applied": data}


@app.post("/fault")
async def inject_fault(payload: FaultPayload) -> dict:
    """Inject a fault into the engine state.

    snap_tool — latched; torque collapses to air-cut floor until POST /reset (D-08).
    hard_spot — transient 10-tick spike then auto-decays (D-09).
    """
    if payload.fault == "snap_tool":
        engine_state.snap_tool = True
        logger.info("Fault injected: snap_tool (latched)")
    else:
        engine_state.hard_spot_ticks = 10
        logger.info("Fault injected: hard_spot (10-tick transient)")
    return {"ok": True, "fault": payload.fault}


@app.post("/reset")
async def reset_state() -> dict:
    """Restore OP-20 nominal setpoints, clear faults, and re-seed the RNG.

    Re-seeding (Pitfall 4) ensures two rehearsals from reset produce identical
    noise streams — same seed AND same setpoint/fault timeline → same stream.
    """
    engine_state.__dict__.update(EngineState().__dict__)
    physics.reset_rng(settings.rng_seed)
    logger.info("Engine reset to OP-20 nominal; RNG re-seeded")
    return {"ok": True}


# ---------------------------------------------------------------------------
# StaticFiles mount — MUST be registered AFTER all @app.post routes (Pitfall 6).
# FastAPI matches routes before mounts; a catch-all mount registered first would
# shadow /setpoints, /fault, /reset and return 404/static instead of the handlers.
#
# html=True causes FastAPI to serve index.html for GET / (the HMI root).
# ---------------------------------------------------------------------------

class _NoCacheStaticFiles(StaticFiles):
    """Serve HMI assets with ``Cache-Control: no-cache`` so browsers always
    revalidate (ETag → cheap 304s when unchanged, fresh content when changed).
    Prevents stale CSS/JS during iteration without disabling caching outright.
    """

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache"
        return response


_STATIC_DIR = Path(__file__).resolve().parent / "static"


# config.js is served as a plain static asset — not generated. On the server,
# twinConfig.js from the shared config volume is mounted directly OVER
# static/config.js (see mill-twin.yaml), the same pattern `app` uses for
# appConfig.js in stack.yaml. So operators edit the served config.js live (change
# WO links / NATS URL, redeploy demo_twin — no image rebuild). Locally, without
# the volume, the baked static/config.js is served as the fallback.
app.mount("/", _NoCacheStaticFiles(directory=str(_STATIC_DIR), html=True), name="hmi")
