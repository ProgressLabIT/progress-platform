"""Demo-twin NATS publisher — own connection, neutral-envelope, core NATS only.

This module provides the twin's OWN NATS client instance (NOT the product
API's module-level singleton at backend/api/utils/nats_client.py).  It uses
core NATS publish only (no streaming, no MQTT) — PUB-03.

Key exports:
  connect_nats(url)        — connect with reconnect callbacks
  drain_nats(nc)           — graceful drain with 5 s timeout fallback
  build_envelope(...)      — bytes: JSON {"value","unit","source","ts"}
  publish_tick(nc, ...)    — core nc.publish() per signal, one per leaf
"""
from __future__ import annotations

import asyncio
import json
import logging

import nats
from nats.aio.client import Client as NatsClient

log = logging.getLogger("demo_twin.publisher")

# Subject prefix (ADR-0013/D-01 — locked taxonomy).
BASE_SUBJECT = "progress.uns.plant1.area1.cell1.gantry1"

# Throttle the "not connected" warning so a sustained outage logs once per
# transition rather than 5×/s.  Reset to False on the first successful tick.
_publish_warned_disconnected = False


# ---------------------------------------------------------------------------
# NATS connection lifecycle
# ---------------------------------------------------------------------------

async def connect_nats(url: str) -> NatsClient:
    """Connect to NATS with reconnect callbacks mirroring the project pattern.

    Uses max_reconnect_attempts=-1 so the twin reconnects indefinitely when
    the broker restarts during a demo session.
    """
    async def error_cb(e: Exception) -> None:
        log.error("NATS error: %s", e)

    async def disconnected_cb() -> None:
        log.warning("NATS disconnected")

    async def reconnected_cb() -> None:
        log.warning("NATS reconnected")

    nc = await nats.connect(
        url,
        error_cb=error_cb,
        disconnected_cb=disconnected_cb,
        reconnected_cb=reconnected_cb,
        reconnect_time_wait=2,
        max_reconnect_attempts=-1,
    )
    log.info("Connected to NATS at %s", url)
    return nc


async def drain_nats(nc: NatsClient) -> None:
    """Gracefully drain the NATS connection with a 5 s timeout fallback."""
    try:
        if nc.is_connected:
            await asyncio.wait_for(nc.drain(), timeout=5.0)
            log.info("NATS connection drained")
        elif not nc.is_closed:
            await nc.close()
            log.info("NATS connection closed (was not connected)")
    except asyncio.TimeoutError:
        log.warning("NATS drain timed out, forcing close")
        try:
            await nc.close()
        except Exception:
            pass
    except Exception as exc:
        log.warning("NATS drain error: %s", exc)
        try:
            if not nc.is_closed:
                await nc.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Envelope builder
# ---------------------------------------------------------------------------

def build_envelope(value: float, unit: str, source: str, ts_ms: int) -> bytes:
    """Serialise a UNS telemetry envelope to JSON bytes (PUB-02 shape).

    Exactly four fields: value, unit, source, ts.  No quality field
    (D-04: source cannot define data quality at source).

    ensure_ascii=False preserves the middle-dot in 'N·m' (Pitfall 6).

    allow_nan=False makes a non-finite value raise ValueError at serialize
    time rather than emit the bare NaN/Infinity tokens (invalid JSON per
    RFC 8259) that the nats.ws panel's JSON.parse would reject. The
    physics_loop try/except then log-and-continues on a poison tick.
    """
    return json.dumps(
        {"value": value, "unit": unit, "source": source, "ts": ts_ms},
        ensure_ascii=False,
        allow_nan=False,
    ).encode()


# ---------------------------------------------------------------------------
# Tick publisher
# ---------------------------------------------------------------------------

async def publish_tick(
    nc: NatsClient | None,
    signals: dict[str, tuple[float, str]],
    source: str,
    ts_ms: int,
) -> None:
    """Publish one neutral envelope per signal to the gantry subject tree.

    Performs 12 core NATS publish calls per tick (one per D-02 signal).
    Core pub only — no streaming context, no acknowledgment.

    subjects: progress.uns.plant1.area1.cell1.gantry1.<leaf>

    Skips the tick (and logs once per transition) when the client is None
    (startup degrade, WR-03) or disconnected/reconnecting.  Core NATS buffers
    to the reconnect queue and then silently discards past the pending limit
    with no exception (at 12 msg × 5 Hz the buffer fills in seconds), so a
    stall would otherwise be invisible.  Dropping live telemetry during an
    outage is the accepted core-NATS trade-off (no JetStream redelivery) —
    this makes it observable, not silent.
    """
    global _publish_warned_disconnected
    if nc is None or not nc.is_connected:
        if not _publish_warned_disconnected:
            log.warning("NATS not connected — skipping tick publishes")
            _publish_warned_disconnected = True
        return
    if _publish_warned_disconnected:
        log.info("NATS connected — resuming tick publishes")
        _publish_warned_disconnected = False
    for leaf, (value, unit) in signals.items():
        subject = f"{BASE_SUBJECT}.{leaf}"
        await nc.publish(subject, build_envelope(value, unit, source, ts_ms))
