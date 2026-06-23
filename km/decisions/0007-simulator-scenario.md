# 0007 — Simulator Topology and Demo Scenario

**Status:** decided
**Date:** 2026-04-28 (amended 2026-04-29 — see § Amendment)
**Audience:** S1 (bridge tests), S3 (slim wedge tuning), S5 (demo data + walkthrough)
**Supersedes:** none

## Context

The Sparkplug demo is self-contained: a `sparkplug_sim` service inside
`deploy/compose/sparkplug.yaml` plays the role of every edge node and
device. Its scenario must:

- exercise enough Sparkplug spec surface to be credible to an
  ISA-95 / ProveIT!-fluent audience (NBIRTH/DBIRTH, NDEATH/DDEATH, alias
  resolution, primary-host STATE, sequence numbers);
- produce data dynamics that look industrial (warm-up curves, state-driven
  metrics, not pure random walks);
- trigger the slim wedge's binding (per ADR-0003) exactly once in the
  ~5-minute Sparkplug segment of the demo;
- support a kill-and-restart bit of theatre that visibly exercises
  DEATH→BIRTH transitions in the topology browser;
- repeat cleanly after `make demo-reset` so multiple rehearsals don't
  diverge.

This ADR fixes the topology, the metric set, the value dynamics, and the
scenario timeline so S3 and S5 can build the simulator code and demo
script in parallel with S1's bridge work.

## Decision

### Topology

One ISA-95-aligned group with two edges and four devices total. The slug
forms below match ADR-0002's group/edge/device tokens.

| Group  | Edge   | Device     | Real-world archetype           |
|--------|--------|------------|--------------------------------|
| plant1 | edge1  | pump3      | Centrifugal pump               |
| plant1 | edge1  | conveyor7  | Variable-speed conveyor        |
| plant1 | edge2  | oven4      | Process oven                   |
| plant1 | edge2  | mixer2     | Batch mixer                    |

`group_id` `"plant1"` is the static ISA-95 enterprise/site stand-in; the
demo deck explains the mapping. Edge names map to PLC/edge-gateway IDs.

### Metric set per device

Each device publishes 4–6 metrics: a state metric, a primary process
metric, and 2–3 supporting telemetry/counter metrics. This matches what
real Sparkplug deployments look like at this scale and gives the topology
browser something visually rich without flooding.

#### `pump3`

| Metric         | Type    | Initial | Dynamics                                                     |
|----------------|---------|---------|--------------------------------------------------------------|
| `Running`      | Boolean | true    | Held true through scenario except for the kill-and-restart  |
| `Vibration`    | Float   | 22.0    | Pink-noise random walk around 22 ± 1.5 mm/s; spikes scripted |
| `OutletPressure` | Float | 4.10    | Slow walk around 4.1 bar; correlates with Vibration spike    |
| `MotorAmps`    | Float   | 18.5    | Walk around 18 ± 2 A                                         |
| `RunHours`     | Float   | 14512.3 | Monotonic + 1/3600 per second while Running=true             |

#### `conveyor7`

| Metric         | Type    | Initial | Dynamics                                                     |
|----------------|---------|---------|--------------------------------------------------------------|
| `Running`      | Boolean | true    | Toggles per scenario state transitions                       |
| `Speed`        | Float   | 1.20    | Walk around 1.2 m/s; drops to 0 when Running=false           |
| `LoadCell`     | Float   | 38.0    | Walk around 38 kg; correlates with Speed                     |
| `PiecesCount`  | Int32   | 17441   | Monotonic +1 per simulated piece while Running               |

#### `oven4`

| Metric         | Type    | Initial | Dynamics                                                     |
|----------------|---------|---------|--------------------------------------------------------------|
| `Running`      | Boolean | true    | Stays true                                                   |
| `Setpoint`     | Float   | 220.0   | Steps in scenario timeline                                   |
| `Temperature`  | Float   | 218.5   | First-order lag toward Setpoint, time constant 90 s          |
| `EnergyKwh`    | Float   | 8421.6  | Monotonic; rate proportional to Temperature                  |

#### `mixer2`

| Metric         | Type    | Initial | Dynamics                                                     |
|----------------|---------|---------|--------------------------------------------------------------|
| `Running`      | Boolean | false   | Toggles in scenario                                          |
| `RPM`          | Int32   | 0       | 0 when stopped; 240 ± 10 when running                        |
| `BatchID`      | String  | ""      | Set on Running rising edge; cleared on falling edge          |
| `TankLevel`    | Float   | 0.62    | Walk around 0.6 ± 0.05                                       |

### Edge-level metrics

Each edge node publishes one edge-scope metric so consumers see the
NDATA path exercised:

- `edge1`: `NodeControl.Rebirth` Boolean (always false; flips true briefly
  when the rebirth-request action is wired post-demo).
- `edge2`: `NodeControl.Rebirth` Boolean (same).

### Aliases and birth ordering

NBIRTH for each edge declares all metrics for that edge plus all metrics
for its devices, with stable aliases assigned as the integer index in the
list above (1-based, scoped per (edge, bdSeq) pair).

DBIRTH for each device repeats the device's metrics for that bdSeq with
the same aliases. After NBIRTH/DBIRTH, NDATA / DDATA frames carry alias
references only (no metric names) — this exercises the bridge's alias
resolution path (per ADR-0002 design) and demonstrates compliance the
audience will test.

The simulator exercises an alias renumbering once during the scenario by
forcing a rebirth on `edge2` with reordered metrics. The bridge must
re-resolve aliases after this without losing names; this is a live
correctness signal during the demo.

### Sequence numbers and bdSeq

- `seq` follows the Sparkplug 0–255 wraparound, reset on every NBIRTH.
- `bdSeq` increments per edge across the simulator process lifetime. It is
  emitted on the LWT-encoded NDEATH and on each NBIRTH; the bridge drops
  any NDEATH whose bdSeq is stale.

### Scenario timeline

The simulator runs an idempotent timeline anchored to "scenario start"
(the moment the simulator container reports its first NBIRTH). A new
scenario start happens on container start or on `make demo-reset`. Times
below are simulator wall-clock from `t=0`.

```
t = 0:00    All edges and devices send NBIRTH/DBIRTH. Steady state begins.
t = 0:30    oven4.Setpoint steps from 220 to 245.
            (Temperature begins ramping up per the lag model.)
t = 1:30    mixer2.Running rises. BatchID = "B-2026-04-28-001". RPM ramps to 240.
t = 2:30    pump3 vibration scenario begins:
              - Vibration linearly increases (slope from scenario.yaml;
                default +5.0 / 5 s = +1.0 mm/s per second)
              - OutletPressure correlates: drops (default -0.05 / 4 s)
            For 90 s, Vibration crosses the wedge threshold (100 mm/s,
            locked by ADR-0010) upward at approximately t = 3:48.
            ←← THE AUTOMATION FIRES HERE ←←
t = 4:00    pump3 anomaly continues until t = 4:30 then returns to baseline
            via a 30-second linear decay back to 22 mm/s.
t = 4:45    Presenter kills sparkplug_sim container manually.
            edge1 + edge2 send NDEATH via NATS-MQTT LWT;
            UI marks pump3, conveyor7, oven4, mixer2 as offline (stale).
t = 5:00    Presenter restarts sparkplug_sim. New bdSeq.
            edge2 NBIRTH this time uses re-ordered alias slots
            (alias renumbering test).
t = 5:30    Steady state resumes. All metrics LIVE again.
```

The 3:50 binding-fire point is engineered to land mid-explanation in the
demo script (per ADR-0001's flow). Tolerance is ±15 s; the linear ramp
makes the cross deterministic.

The kill-and-restart at 4:45 is a manual action by the presenter. The
simulator does not self-kill; the demo scenario's "session lifecycle" act
depends on a human action so it can be skipped or repeated as the live
flow allows.

### Implementation tooling

The simulator is a Python service using `pysparkplug` 0.6.1 for protobuf
encoding, with a small scenario-runner module that drives the timeline
described above. It connects via `aiomqtt` to NATS' MQTT 3.1.1 endpoint
on `nats:1883`. It publishes `STATE` from its host id `sparkplug_sim` so
the bridge sees a paired primary host (the bridge itself is the real
primary host; the simulator does not pretend to be one).

The simulator package holds:

- `scenario.yaml`: the canonical, tweakable timing + dynamics parameters
  parsed at startup. See § Amendment for the schema and the locked
  parameters that mirror ADR-0010 (`pump3_anomaly.threshold`).
- `physics.py`: the small state-driven dynamics (lag, walk, wraparound).
- `topology.py`: the device list + per-device metric set + initial values
  (the parts ADR-0007 considers locked structure, not tweakable parameters).

The simulator runs idempotently; `docker compose restart sparkplug_sim`
or `make demo-reset` produces the same timeline every time.

### Demo data dependencies

The hardcoded automation (per ADR-0010) targets
`plant1.edge1.pump3.Vibration` with threshold `100`, dwell `5 s`, latch
`60 s` — all in-code constants. Linked to `WO-DEMO-001` and `PH-DEMO-001`
via a hardcoded link list. S5 ensures these keys exist in the restored
ArangoDB so the resulting `IssueCreatedEvent` applies cleanly:

- One `WorkOrder` document with `_key = "WO-DEMO-001"`, status
  appropriate for accepting linked issues, plus the related production
  records the event's `apply()` chain may touch.
- One `Phase` document with `_key = "PH-DEMO-001"` linked to the WO.
- The `USR-SPARKPLUG-BRIDGE` service user with an issued JWT mounted into
  the bridge container.

### Reset semantics

`make demo-reset` performs:

1. `docker compose stop sparkplug_sim sparkplug_bridge historian_ingester`
2. JetStream KV bucket flush for the three sparkplug buckets.
3. `metric_samples` truncate (per ADR-0005 reset path).
4. Re-start the three services.
5. Empty `bindings.yaml` is NOT used here; the original is reloaded on
   bridge start. Demo bindings fire the next time the simulator's
   scenario reaches t=3:50.

The `make demo-stop-automations` emergency action (per ADR-0010) is a
SEPARATE command that disables the hardcoded automation by setting
`SPARKPLUG_AUTOMATIONS_ENABLED=false` on the bridge container and
restarting it. Used if rehearsal proves the automation flaps; not used
during nominal demo.

## Trade-offs and rejected options

**4 devices vs more.** Considered 6+ for visual richness. Rejected; tree
becomes hard to read on a webinar's screen-share resolution. 4 devices
across 2 edges fills a screen without overflow.

**Boolean and String metrics included.** Yes — auditors check that the
host doesn't drop non-numeric types. Including `BatchID` (String) and
`Running` (Boolean) signals competence.

**Pre-recorded data file vs live procedural.** Procedural. A recorded
file would not exercise the alias renumbering / NDEATH / NBIRTH state
machine in a controlled-but-deterministic way. Procedural with seeded
randomness is reproducible enough.

**Random binding-fire time vs scripted.** Scripted. A demo where the
binding fires "sometime in the next 5 minutes" is a presentation
disaster. The linear ramp is the safest deterministic device.

**Alias renumbering on every restart vs once mid-scenario.** Once
mid-scenario. Two birth events in 30 s confuses the audience; one
deliberate one demonstrates the host's correctness.

**Including a DataSet metric.** Rejected. DataSet decoding is post-demo
(ADR-0002 ADV-01). A simulator publishing a metric the bridge can't
decode would log a warning during the demo, which we don't want.

## Consequences

- S1 (bridge) tests against this exact metric set and timeline as a
  reproducible integration scenario.
- S3 (slim wedge) tunes the binding's `threshold` to `100` and
  `latch_for_seconds` to `60` to ensure exactly one fire per scenario
  pass.
- S5 (demo data) seeds the demo work order, phase, and service user keys
  referenced here. Walkthrough script is written against the timeline
  above with named cues at each `t = X:YY` point.
- The `demos/sparkplug_sim/scenario.yaml` file is the
  single source of truth for tweakable scenario timing + dynamics
  parameters. Changes to its values do NOT require an ADR amendment;
  changes to its *schema* (new keys, removed keys, changed semantics)
  do. See § Amendment 2026-04-29.

## Related

- ADR-0001 — demo flow that places the Sparkplug segment.
- ADR-0002 — NATS subject taxonomy and quality semantics the simulator
  exercises.
- ADR-0003 — bindings.yaml schema; this ADR's threshold (100) and metric
  match it.
- ADR-0007 — implicitly anchors ADR-0005's downsampling behaviour at the
  data shapes produced here.
- ADR-0010 — locks the wedge threshold (`THRESHOLD = 100.0`) that the
  pump3 vibration ramp must cross during the demo. The amendment below
  guarantees the math actually crosses.
- `pysparkplug` documentation at https://pypi.org/project/pysparkplug/.

## Amendment — 2026-04-29

### What changed

A review of this ADR against ADR-0010 (`THRESHOLD = 100.0`) found that
the originally specified vibration ramp (`+0.4 / 5 s` = `0.08 mm/s/s`,
starting at 22.0 mm/s) **cannot reach 100 mm/s in the 80-second anomaly
window** — it only reaches ~28.4 mm/s. With the original parameters the
wedge automation (Phase 5) would never fire on this scenario.

Two adjustments are made to keep the demo self-consistent:

1. **Vibration ramp slope corrected** from `+0.4 / 5 s` to `+5.0 / 5 s`
   (= `+1.0 mm/s per second`). This makes Vibration cross 100 mm/s at
   t ≈ 3:48 (within the existing ±15 s tolerance window anchored on
   t = 3:50).

2. **Tweakable scenario parameters externalized** into a YAML config
   file at `demos/sparkplug_sim/scenario.yaml` so that
   future calibration (slope, threshold, anomaly start/end times,
   correlated pressure slope, etc.) does not require code changes or
   image rebuilds during rehearsal. ADR-0010's `THRESHOLD` constant
   remains locked in code; the simulator's `pump3_anomaly.threshold`
   key MUST equal it (asserted at simulator startup).

Locked structural decisions (topology, metric set, alias rules, edge
metrics, sequence/bdSeq semantics, kill-and-restart theatre) are
**unchanged**. Only the numerical parameters of the dynamics + the cue
timestamps move out into the YAML file.

### `scenario.yaml` schema (v1)

```yaml
version: 1

# Pump-3 anomaly window. Calibrated so Vibration crosses
# `pump3_anomaly.threshold` near t=3:50 (within ADR-0007 ±15s tolerance).
# `threshold` MUST equal ADR-0010 THRESHOLD (asserted at startup).
pump3_anomaly:
  start_value_mm_s: 22.0          # matches Vibration.initial in topology.py
  threshold_mm_s: 100.0           # locked to ADR-0010 THRESHOLD
  slope_mm_s_per_sec: 1.0         # +1.0 mm/s/s — crosses 100 at t=3:48
  ramp_seconds: 90                # anomaly window length
  return_to_baseline_decay_sec: 30
  correlated_outlet_pressure_slope_bar_per_sec: -0.0125  # = -0.05 / 4s

# Scenario timeline cues. Times in seconds from t=0 (first NBIRTH).
timeline:
  oven_setpoint_step_at_sec: 30
  oven_setpoint_step_to_c: 245.0
  mixer_running_rising_at_sec: 90
  pump_anomaly_begin_at_sec: 150
  pump_anomaly_end_at_sec: 240          # begin + ramp_seconds
  kill_cue_at_sec: 285                  # informational — presenter manual
  restart_cue_at_sec: 300               # informational — presenter manual
  steady_state_resume_at_sec: 330

# Edge metadata.
edges:
  bdseq_starts_at: 0                    # RESEARCH §Open Question #4 (a)

# Demo metadata.
demo:
  batch_id: "B-2026-04-28-001"          # set on mixer2.Running rising edge
```

### Validation rules

The simulator MUST:

1. Load `scenario.yaml` at startup via the path resolved from
   `PROGRESS_SIM_SCENARIO_PATH` (default: package-relative
   `scenario.yaml`).
2. Assert `pump3_anomaly.threshold_mm_s == ADR-0010 THRESHOLD` (currently
   `100.0`). Mismatch is a fatal startup error.
3. Assert `pump3_anomaly.start_value_mm_s` equals the Vibration initial
   value declared in `topology.py` (currently `22.0`). Mismatch is a
   fatal startup error.
4. Assert that
   `start_value + slope_mm_s_per_sec × ramp_seconds >= threshold_mm_s`
   so the cross is mathematically reachable. Mismatch is a fatal
   startup error.

These three assertions catch the original ADR-0007 discrepancy before
the demo and replace the `## EXECUTOR NOTE` flag in Plan 01-03.

### Consequences of the amendment

- Plan 01-03 (the simulator) is updated to load these parameters from
  YAML rather than hardcode them. The plan's previous `## EXECUTOR
  NOTE: FLAG ADR-0007 vibration-cross-100 math` block is **resolved**
  by this amendment and removed.
- ADR-0010's `THRESHOLD = 100.0` constant in
  `backend/sparkplug_bridge/automations/pump_anomaly.py` is unchanged.
  The simulator's startup assertion catches future drift between the
  YAML and ADR-0010 in either direction.
- Phase 5 (wedge automation) wiring is unchanged. The demo cue at
  t = 3:50 still fits within the new cross point (t ≈ 3:48) ± the
  scripted DWELL_SECONDS = 5, so the visible "issue created" in the UI
  lands at t ≈ 3:53 — still inside the demo narrative beat.
