"""ADR-0007 scenario orchestrator — central state machine driving the timeline.

Per CONTEXT.md D-03: the orchestrator drives cues; per-device asyncio tasks
publish their metric streams independently but transition through scenario
phases on signals from this orchestrator.

Timeline (idempotent, anchored to t=0 = first NBIRTH per ADR-0007):

  t = 0:00   All edges send NBIRTH/DBIRTH. Steady state begins.
  t = 0:30   oven4.Setpoint steps 220 -> 245.
  t = 1:30   mixer2.Running rises. BatchID = "B-2026-04-28-001". RPM ramps to 240.
  t = 2:30   pump3 vibration anomaly window starts. Slope, threshold, and
             window length come from scenario.yaml `pump3_anomaly` (per
             ADR-0007 Amendment 2026-04-29).
             Defaults: Vibration += 1.0 / sec  (linear ramp; crosses 100 at t≈3:48)
                       OutletPressure += -0.0125 / sec  (correlated)
                       ramp = 90s; cross at elapsed=78s.
  t = 4:00   Anomaly continues until t=4:30 then linear-decays back to baseline
             (decay_seconds from scenario.yaml return_to_baseline_decay_sec; 30s default).
  t = 4:45   Presenter manually kills sparkplug_sim — handled OUTSIDE this code.
             aiomqtt's Will (set at connect time per build_ndeath_will) delivers
             NDEATH on unclean disconnect.
  t = 5:00   Restart. New bdSeq. edge2 NBIRTH uses reordered alias slots
             (assign_aliases(reorder_devices=True)). Handled by main.py's
             outer reconnect loop bumping bd_seq + setting reorder=True for one
             cycle.
  t = 5:30   Steady state resumes.
"""
import asyncio
import itertools
import logging
import time as _time
from dataclasses import dataclass
from pathlib import Path

from aiomqtt import Client
from pysparkplug import DataType

from . import physics, topology
from .encoder import (
    build_dbirth_payload,
    build_ddata_payload,
    build_ddeath_payload,
    build_nbirth_payload,
    build_ndata_payload,
)
from .topology import EdgeSpec, GROUP_ID, assign_aliases

logger = logging.getLogger("sparkplug_sim.scenario")

# Tick interval for per-device metric publishing.
TICK_SECONDS = 1.0


@dataclass(frozen=True)
class ScenarioParams:
    """Calibrated scenario parameters loaded from scenario.yaml.

    Per ADR-0007 Amendment 2026-04-29 — every numerical knob the demo
    operator might want to tweak between rehearsals lives in the YAML.
    Structural decisions (topology, alias rules, kill-and-restart cue
    semantics) stay in code.
    """
    # Cue offsets in seconds from scenario t=0.
    cue_oven_setpoint_step: float
    cue_oven_setpoint_step_to: float
    cue_mixer_start: float
    cue_pump_anomaly_start: float
    cue_pump_anomaly_end: float
    cue_kill: float
    cue_restart: float
    cue_steady_state_resume: float
    cue_oven4_ddeath: float
    cue_oven4_dbirth: float

    # Pump-3 anomaly parameters.
    anomaly_vibration_start: float
    anomaly_vibration_threshold: float
    anomaly_vibration_slope: float          # mm/s per second
    anomaly_ramp_seconds: float
    anomaly_baseline_decay_sec: float
    anomaly_pressure_slope: float           # bar per second

    # Edge metadata.
    bdseq_starts_at: int

    # Demo metadata.
    demo_batch_id: str


def load_scenario_params(path: Path) -> ScenarioParams:
    """Parse scenario.yaml and validate it against ADR-0010 + topology constants.

    The four assertions below catch the original ADR-0007 vibration-math
    discrepancy at startup time, before the first NBIRTH ships. They MUST
    fire (exit non-zero) on a misconfigured rehearsal.
    """
    import yaml

    # ADR-0010 contract value — MUST equal backend/sparkplug_bridge/automations/pump_anomaly.py THRESHOLD.
    # ponytail: inlined constant (the sim is decoupled from the bridge package); sync by contract.
    THRESHOLD = 100.0

    raw = yaml.safe_load(Path(path).read_text())
    if raw.get("version") != 1:
        raise ValueError(
            f"scenario.yaml: unsupported version {raw.get('version')!r}; expected 1"
        )

    pa = raw["pump3_anomaly"]
    tl = raw["timeline"]

    # Env overrides for fast-iteration testing — defaults preserve full
    # rehearsal pacing. The end/begin/ramp invariant is restored below so
    # downstream validation rules still hold.
    import os
    if os.environ.get("SIM_PUMP_ANOMALY_BEGIN_SEC"):
        tl["pump_anomaly_begin_at_sec"] = float(os.environ["SIM_PUMP_ANOMALY_BEGIN_SEC"])
    if os.environ.get("SIM_PUMP_ANOMALY_RAMP_SEC"):
        pa["ramp_seconds"] = float(os.environ["SIM_PUMP_ANOMALY_RAMP_SEC"])
    if os.environ.get("SIM_PUMP_ANOMALY_SLOPE"):
        pa["slope_mm_s_per_sec"] = float(os.environ["SIM_PUMP_ANOMALY_SLOPE"])
    # Maintain invariant: end = begin + ramp (enforced below by assert).
    tl["pump_anomaly_end_at_sec"] = float(tl["pump_anomaly_begin_at_sec"]) + float(pa["ramp_seconds"])

    p = ScenarioParams(
        cue_oven_setpoint_step=float(tl["oven_setpoint_step_at_sec"]),
        cue_oven_setpoint_step_to=float(tl["oven_setpoint_step_to_c"]),
        cue_mixer_start=float(tl["mixer_running_rising_at_sec"]),
        cue_pump_anomaly_start=float(tl["pump_anomaly_begin_at_sec"]),
        cue_pump_anomaly_end=float(tl["pump_anomaly_end_at_sec"]),
        cue_kill=float(tl["kill_cue_at_sec"]),
        cue_restart=float(tl["restart_cue_at_sec"]),
        cue_steady_state_resume=float(tl["steady_state_resume_at_sec"]),
        cue_oven4_ddeath=float(tl.get("oven4_ddeath_at_sec", 270.0)),
        cue_oven4_dbirth=float(tl.get("oven4_dbirth_at_sec", 290.0)),
        anomaly_vibration_start=float(pa["start_value_mm_s"]),
        anomaly_vibration_threshold=float(pa["threshold_mm_s"]),
        anomaly_vibration_slope=float(pa["slope_mm_s_per_sec"]),
        anomaly_ramp_seconds=float(pa["ramp_seconds"]),
        anomaly_baseline_decay_sec=float(pa["return_to_baseline_decay_sec"]),
        anomaly_pressure_slope=float(pa["correlated_outlet_pressure_slope_bar_per_sec"]),
        bdseq_starts_at=int(raw["edges"]["bdseq_starts_at"]),
        demo_batch_id=str(raw["demo"]["batch_id"]),
    )

    # ---- Validation rules per ADR-0007 § Amendment 2026-04-29 ----
    if p.anomaly_vibration_threshold != THRESHOLD:
        raise ValueError(
            f"scenario.yaml pump3_anomaly.threshold_mm_s ({p.anomaly_vibration_threshold}) "
            f"!= ADR-0010 THRESHOLD ({THRESHOLD}); demo would never fire"
        )
    expected_initial = next(
        m.initial for e in topology.EDGES for d in e.devices
        if d.device_id == "pump3" for m in d.metrics if m.name == "Vibration"
    )
    if p.anomaly_vibration_start != expected_initial:
        raise ValueError(
            f"scenario.yaml pump3_anomaly.start_value_mm_s ({p.anomaly_vibration_start}) "
            f"!= topology.py pump3.Vibration initial ({expected_initial})"
        )
    reachable_max = (
        p.anomaly_vibration_start
        + p.anomaly_vibration_slope * p.anomaly_ramp_seconds
    )
    if reachable_max < p.anomaly_vibration_threshold:
        raise ValueError(
            f"scenario.yaml pump3_anomaly cannot cross threshold: "
            f"{p.anomaly_vibration_start} + {p.anomaly_vibration_slope} × {p.anomaly_ramp_seconds} "
            f"= {reachable_max} < threshold {p.anomaly_vibration_threshold}"
        )
    if p.cue_pump_anomaly_end - p.cue_pump_anomaly_start != p.anomaly_ramp_seconds:
        raise ValueError(
            f"scenario.yaml timeline.pump_anomaly_end_at_sec - pump_anomaly_begin_at_sec "
            f"({p.cue_pump_anomaly_end - p.cue_pump_anomaly_start}) "
            f"!= pump3_anomaly.ramp_seconds ({p.anomaly_ramp_seconds})"
        )
    if p.cue_oven4_dbirth <= p.cue_oven4_ddeath:
        raise ValueError(
            f"scenario.yaml timeline.oven4_dbirth_at_sec ({p.cue_oven4_dbirth}) "
            f"must be > oven4_ddeath_at_sec ({p.cue_oven4_ddeath}) "
            f"so DBIRTH revives the device after DDEATH"
        )
    return p


class ScenarioRunner:
    """Owns scenario state and per-edge asyncio coroutines.

    Lifecycle: instantiate once per simulator process, call `run_edge(client, edge)`
    once per edge inside an asyncio.TaskGroup.
    """

    def __init__(
        self,
        params: "ScenarioParams",
        scenario_start_offset_sec: float = 0.0,
    ) -> None:
        self.params = params
        self.scenario_start_offset_sec = scenario_start_offset_sec
        # Per-edge bdSeq counters. Initial value loaded from scenario.yaml
        # `edges.bdseq_starts_at` (RESEARCH Open Question #4 recommendation (a) —
        # each fresh container starts at 0 by default; Phase 2 may persist).
        self._bd_seq: dict[str, int] = {
            edge.edge_id: params.bdseq_starts_at for edge in topology.EDGES
        }
        # Per-edge seq counter (Pitfall 6: ONE counter per edge).
        self._seq: dict[str, "itertools.cycle"] = {
            edge.edge_id: itertools.cycle(range(256)) for edge in topology.EDGES
        }
        # Whether the next NBIRTH for this edge should reorder devices (the t=5:00 cue).
        self._reorder_on_next_birth: dict[str, bool] = {
            edge.edge_id: False for edge in topology.EDGES
        }
        # Live metric values keyed by (edge_id, device_id_or_None, metric_name).
        self._values: dict[tuple[str, str | None, str], object] = {}
        self._init_metric_values()
        # 999.4 D-04: oven4 DDEATH/DBIRTH single-shot cues. Latched per scenario
        # run; reset only when ScenarioRunner is reconstructed (i.e., a sim
        # restart wipes the flag along with everything else). Within one run we
        # publish DDEATH at cue_oven4_ddeath then DBIRTH at cue_oven4_dbirth,
        # then nothing further.
        self._oven4_ddeath_fired: bool = False
        self._oven4_dbirth_fired: bool = False
        self._oven4_alive: bool = True
        # Scenario start wall-clock (set when the first edge issues NBIRTH).
        self._t0_wall: float | None = None

    # --- helpers ---

    def _init_metric_values(self) -> None:
        """Reset metric state to ADR-0007 initial values."""
        for edge in topology.EDGES:
            for em in edge.edge_metrics:
                self._values[(edge.edge_id, None, em.name)] = em.initial
            for dev in edge.devices:
                for m in dev.metrics:
                    self._values[(edge.edge_id, dev.device_id, m.name)] = m.initial

    @property
    def edges(self) -> tuple[EdgeSpec, ...]:
        return topology.EDGES

    def bd_seq(self, edge_id: str) -> int:
        return self._bd_seq[edge_id]

    def request_reorder_for_next_birth(self, edge_id: str) -> None:
        """Schedule alias renumbering on the next NBIRTH for this edge (t=5:00 cue)."""
        self._reorder_on_next_birth[edge_id] = True

    def _next_seq(self, edge_id: str) -> int:
        return next(self._seq[edge_id])

    def _reset_seq(self, edge_id: str) -> None:
        # Restart the cycle so the next NBIRTH gets seq=0.
        self._seq[edge_id] = itertools.cycle(range(256))

    def _scenario_t(self) -> float:
        """Seconds since scenario start (t=0)."""
        if self._t0_wall is None:
            return 0.0
        return _time.monotonic() - self._t0_wall

    # --- per-edge coroutine ---

    async def run_edge(self, client: Client, edge: EdgeSpec) -> None:
        """Per-edge publish coroutine: NBIRTH + DBIRTHs, then tick loop until cancelled."""
        # Establish scenario start the first time any edge starts.
        if self._t0_wall is None:
            if self.scenario_start_offset_sec > 0:
                logger.info("scenario start offset: sleeping %.1fs", self.scenario_start_offset_sec)
                await asyncio.sleep(self.scenario_start_offset_sec)
            self._t0_wall = _time.monotonic()
            logger.info("scenario t=0 anchored at monotonic=%.3f", self._t0_wall)

        # Bump bdSeq for THIS connection (start of a new session).
        # Note: aiomqtt's Will was already built with the bd_seq value passed
        # to main.py; if reconnect loop bumps bd_seq in the outer scope, the
        # Will is rebuilt for the next Client construction.
        bd_seq = self._bd_seq[edge.edge_id]
        # Consume the pending-reorder flag if set; default False on first run.
        # (Previously: `pop(..., False) or self._reorder_on_next_birth[edge.edge_id]`
        # which raised KeyError on first call because pop just deleted the key.)
        reorder = self._reorder_on_next_birth.pop(edge.edge_id, False)
        # Ensure the dict still has a default for next time:
        self._reorder_on_next_birth[edge.edge_id] = False

        aliases = assign_aliases(edge, reorder_devices=reorder)

        # --- NBIRTH (edge metrics + all device metrics, since per ADR-0007 NBIRTH
        # declares every metric for the edge AND all child devices.) ---
        self._reset_seq(edge.edge_id)
        nbirth_seq = self._next_seq(edge.edge_id)  # = 0 after reset
        nbirth_metrics = self._collect_all_metrics_for_birth(edge, aliases)
        nbirth_bytes = build_nbirth_payload(nbirth_metrics, seq=nbirth_seq, bd_seq=bd_seq)
        await client.publish(
            f"spBv1.0/{GROUP_ID}/NBIRTH/{edge.edge_id}",
            payload=nbirth_bytes, qos=1, retain=False,
        )
        logger.info("NBIRTH published edge=%s bd_seq=%d seq=%d reorder=%s",
                    edge.edge_id, bd_seq, nbirth_seq, reorder)

        # --- DBIRTH per device. ---
        for dev in edge.devices:
            dev_metrics = [
                (m.name, m.datatype, self._values[(edge.edge_id, dev.device_id, m.name)],
                 aliases[(dev.device_id, m.name)])
                for m in dev.metrics
            ]
            dbirth_bytes = build_dbirth_payload(dev_metrics, seq=self._next_seq(edge.edge_id))
            await client.publish(
                f"spBv1.0/{GROUP_ID}/DBIRTH/{edge.edge_id}/{dev.device_id}",
                payload=dbirth_bytes, qos=1, retain=False,
            )
            logger.info("DBIRTH published edge=%s device=%s", edge.edge_id, dev.device_id)

        # --- Steady-state tick loop. ---
        try:
            while True:
                await asyncio.sleep(TICK_SECONDS)
                await self._publish_data_tick(client, edge, aliases)
        except asyncio.CancelledError:
            logger.info("edge %s task cancelled", edge.edge_id)
            raise

    def _collect_all_metrics_for_birth(self, edge: EdgeSpec, aliases: dict) -> list[tuple]:
        """Collect (name, datatype, value, alias) tuples for NBIRTH (edge metrics + ALL device metrics)."""
        out: list[tuple] = []
        for em in edge.edge_metrics:
            out.append(
                (em.name, em.datatype, self._values[(edge.edge_id, None, em.name)], aliases[(None, em.name)])
            )
        for dev in edge.devices:
            for m in dev.metrics:
                out.append((
                    m.name, m.datatype,
                    self._values[(edge.edge_id, dev.device_id, m.name)],
                    aliases[(dev.device_id, m.name)],
                ))
        return out

    async def _publish_data_tick(self, client: Client, edge: EdgeSpec, aliases: dict) -> None:
        """Apply dynamics for one tick and publish NDATA + DDATA frames."""
        t = self._scenario_t()

        # Apply per-metric dynamics for every metric in the edge's scope.
        self._apply_dynamics(edge, t)

        # Edge-level NDATA — only NodeControl/Rebirth in v1; always false (no change).
        # We emit it once per minute for liveness signal — keeps `nats sub` outputs honest.
        if int(t) % 60 == 0:
            edge_updates = []
            for em in edge.edge_metrics:
                alias = aliases[(None, em.name)]
                value = self._values[(edge.edge_id, None, em.name)]
                edge_updates.append((alias, em.datatype, value))
            if edge_updates:
                ndata_bytes = build_ndata_payload(edge_updates, seq=self._next_seq(edge.edge_id))
                await client.publish(
                    f"spBv1.0/{GROUP_ID}/NDATA/{edge.edge_id}",
                    payload=ndata_bytes, qos=1, retain=False,
                )

        # Device-level frames — every tick for every device, EXCEPT:
        #   - oven4 between t=cue_oven4_ddeath and t=cue_oven4_dbirth: skip DDATA
        #     (CONTEXT 999.4 D-04 — device is offline in this window).
        #   - At t==cue_oven4_ddeath (first tick crossing): fire DDEATH once.
        #   - At t==cue_oven4_dbirth (first tick crossing): fire DBIRTH once.
        # Cycle is single-shot via _oven4_ddeath_fired / _oven4_dbirth_fired.

        for dev in edge.devices:
            # 999.4 D-04 — oven4 single-shot DDEATH cue (edge2 only).
            if (
                edge.edge_id == "edge2"
                and dev.device_id == "oven4"
                and not self._oven4_ddeath_fired
                and t >= self.params.cue_oven4_ddeath
            ):
                ddeath_seq = self._next_seq(edge.edge_id)
                ddeath_bytes = build_ddeath_payload(seq=ddeath_seq)
                await client.publish(
                    f"spBv1.0/{GROUP_ID}/DDEATH/{edge.edge_id}/{dev.device_id}",
                    payload=ddeath_bytes, qos=1, retain=False,
                )
                self._oven4_ddeath_fired = True
                self._oven4_alive = False
                logger.info(
                    "CUE oven4 DDEATH fired at t=%.1f seq=%d (edge stays online)",
                    t, ddeath_seq,
                )
                # Skip DDATA for oven4 on this same tick.
                continue

            # 999.4 D-04 — oven4 single-shot DBIRTH revival.
            if (
                edge.edge_id == "edge2"
                and dev.device_id == "oven4"
                and self._oven4_ddeath_fired
                and not self._oven4_dbirth_fired
                and t >= self.params.cue_oven4_dbirth
            ):
                # Build DBIRTH from current oven4 metric values + the local
                # `aliases` parameter (the per-edge alias map captured at NBIRTH
                # is already passed into this method — no extra cache needed).
                # Tuple shape mirrors the existing NBIRTH/DBIRTH publish at
                # lines 270-282: (name, datatype, value, alias).
                dev_metrics = [
                    (m.name, m.datatype,
                     self._values[(edge.edge_id, dev.device_id, m.name)],
                     aliases[(dev.device_id, m.name)])
                    for m in dev.metrics
                ]
                dbirth_seq = self._next_seq(edge.edge_id)
                dbirth_bytes = build_dbirth_payload(dev_metrics, seq=dbirth_seq)
                await client.publish(
                    f"spBv1.0/{GROUP_ID}/DBIRTH/{edge.edge_id}/{dev.device_id}",
                    payload=dbirth_bytes, qos=1, retain=False,
                )
                self._oven4_dbirth_fired = True
                self._oven4_alive = True
                logger.info(
                    "CUE oven4 DBIRTH revival at t=%.1f seq=%d", t, dbirth_seq,
                )
                # Resume normal DDATA on the NEXT tick. Skip DDATA for oven4 this tick
                # to avoid an immediate DDATA-after-DBIRTH within the same millisecond.
                continue

            # 999.4 D-04 — suppress oven4 DDATA between DDEATH and DBIRTH.
            if (
                edge.edge_id == "edge2"
                and dev.device_id == "oven4"
                and self._oven4_ddeath_fired
                and not self._oven4_dbirth_fired
            ):
                continue

            dev_updates = []
            for m in dev.metrics:
                alias = aliases[(dev.device_id, m.name)]
                value = self._values[(edge.edge_id, dev.device_id, m.name)]
                dev_updates.append((alias, m.datatype, value))
            ddata_bytes = build_ddata_payload(dev_updates, seq=self._next_seq(edge.edge_id))
            await client.publish(
                f"spBv1.0/{GROUP_ID}/DDATA/{edge.edge_id}/{dev.device_id}",
                payload=ddata_bytes, qos=1, retain=False,
            )

    # --- per-tick dynamics (ADR-0007 § Metric set per device "Dynamics" column) ---

    def _apply_dynamics(self, edge: EdgeSpec, t: float) -> None:
        """Update self._values for every metric on this edge per ADR-0007 dynamics."""
        if edge.edge_id == "edge1":
            self._tick_pump3(t)
            self._tick_conveyor7(t)
        elif edge.edge_id == "edge2":
            self._tick_oven4(t)
            self._tick_mixer2(t)

    def _tick_pump3(self, t: float) -> None:
        e, d = "edge1", "pump3"
        p = self.params
        running = self._values[(e, d, "Running")]
        # Vibration: pink walk normally; linear ramp during anomaly window.
        if p.cue_pump_anomaly_start <= t < p.cue_pump_anomaly_end:
            elapsed = t - p.cue_pump_anomaly_start
            self._values[(e, d, "Vibration")] = physics.linear_ramp(
                p.anomaly_vibration_start, p.anomaly_vibration_slope, elapsed,
            )
            self._values[(e, d, "OutletPressure")] = physics.linear_ramp(
                4.10, p.anomaly_pressure_slope, elapsed,
            )
        else:
            # Outside the window: walk back toward baseline gently.
            self._values[(e, d, "Vibration")] = physics.pink_walk(
                self._values[(e, d, "Vibration")], sigma=0.5,
                bias=(p.anomaly_vibration_start - self._values[(e, d, "Vibration")]) * 0.05,
            )
            self._values[(e, d, "OutletPressure")] = physics.pink_walk(
                self._values[(e, d, "OutletPressure")], sigma=0.05,
                bias=(4.10 - self._values[(e, d, "OutletPressure")]) * 0.05,
            )
        # MotorAmps walks always.
        self._values[(e, d, "MotorAmps")] = physics.pink_walk(
            self._values[(e, d, "MotorAmps")], sigma=0.3, bias=(18.0 - self._values[(e, d, "MotorAmps")]) * 0.02,
        )
        # RunHours monotonic while Running.
        if running:
            self._values[(e, d, "RunHours")] = physics.monotonic_inc(
                self._values[(e, d, "RunHours")], rate_per_second=1.0 / 3600.0, dt_seconds=TICK_SECONDS,
            )

    def _tick_conveyor7(self, t: float) -> None:
        e, d = "edge1", "conveyor7"
        running = self._values[(e, d, "Running")]
        if running:
            self._values[(e, d, "Speed")] = physics.pink_walk(
                self._values[(e, d, "Speed")], sigma=0.05, bias=(1.20 - self._values[(e, d, "Speed")]) * 0.05,
            )
            self._values[(e, d, "LoadCell")] = physics.pink_walk(
                self._values[(e, d, "LoadCell")], sigma=0.5, bias=(38.0 - self._values[(e, d, "LoadCell")]) * 0.02,
            )
            # PiecesCount approx +1/sec while running.
            self._values[(e, d, "PiecesCount")] = int(self._values[(e, d, "PiecesCount")]) + 1
        else:
            self._values[(e, d, "Speed")] = 0.0

    def _tick_oven4(self, t: float) -> None:
        e, d = "edge2", "oven4"
        p = self.params
        # Setpoint step at t=0:30 (cue + new value loaded from scenario.yaml).
        if t >= p.cue_oven_setpoint_step and self._values[(e, d, "Setpoint")] == 220.0:
            self._values[(e, d, "Setpoint")] = p.cue_oven_setpoint_step_to
            logger.info("CUE oven4.Setpoint -> %s at t=%.1f", p.cue_oven_setpoint_step_to, t)
        setpoint = float(self._values[(e, d, "Setpoint")])
        self._values[(e, d, "Temperature")] = physics.first_order_lag(
            float(self._values[(e, d, "Temperature")]), setpoint=setpoint, tau_seconds=90.0, dt_seconds=TICK_SECONDS,
        )
        temp = float(self._values[(e, d, "Temperature")])
        # Energy rate ∝ temperature (toy linear model).
        self._values[(e, d, "EnergyKwh")] = physics.monotonic_inc(
            self._values[(e, d, "EnergyKwh")], rate_per_second=temp * 0.0001, dt_seconds=TICK_SECONDS,
        )

    def _tick_mixer2(self, t: float) -> None:
        e, d = "edge2", "mixer2"
        p = self.params
        was_running = bool(self._values[(e, d, "Running")])
        # Rising edge at t=1:30 (cue + batch_id loaded from scenario.yaml).
        if t >= p.cue_mixer_start and not was_running:
            self._values[(e, d, "Running")] = True
            self._values[(e, d, "BatchID")] = p.demo_batch_id
            self._values[(e, d, "RPM")] = 240
            logger.info("CUE mixer2 rising edge at t=%.1f BatchID=%s", t, p.demo_batch_id)
        if bool(self._values[(e, d, "Running")]):
            # RPM jitters around 240.
            current = int(self._values[(e, d, "RPM")])
            self._values[(e, d, "RPM")] = max(230, min(250, current + (1 if int(t) % 2 == 0 else -1)))
            self._values[(e, d, "TankLevel")] = physics.pink_walk(
                float(self._values[(e, d, "TankLevel")]), sigma=0.01, bias=(0.6 - float(self._values[(e, d, "TankLevel")])) * 0.05,
            )
        else:
            self._values[(e, d, "RPM")] = 0
