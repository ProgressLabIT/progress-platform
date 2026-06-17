# 0002 — NATS Subject Taxonomy for Sparkplug Frames

**Status:** decided
**Date:** 2026-04-28
**Amended:** 2026-04-29 — Added `session.suspect` to the notification `kind` enum with `reason="seq_gap"`; documented the bridge's edge-NDEATH device-cascade synthesis as a primary-host feature (Phase 2 D-12).
**Audience:** S1 (bridge), S2 (UI), S3 (slim wedge), S5 (demo data)
**Supersedes:** none

## Context

The Sparkplug bridge decodes MQTT frames and re-emits them on NATS so that
every downstream consumer (the FastAPI API, the SSE fan-out, the Timescale
ingester, the slim-wedge rule engine, the future bindings/alarms work) sees
Sparkplug as a first-class event domain. The shape of those NATS subjects is
the single largest cross-session contract: anything that subscribes to or
publishes onto these subjects must agree on the same names, the same payload
shape, and the same retention semantics.

The sparkplug-demo workstream's `research/SUMMARY.md` already proposed a
taxonomy. This ADR ratifies it as the v1 demo contract and freezes the JSON
payload shape so that S2 (frontend) and S5 (demo data + simulator) can build
against it in parallel with S1 (bridge implementation).

## Decision

### Subject namespace

All decoded Sparkplug traffic flows under the `progress.sparkplug.*`
hierarchy. The bridge is the sole producer on this hierarchy; the API, the
UI, the wedge, and the historian are read-only consumers.

```
progress.sparkplug.<group>.<edge>.session.online
progress.sparkplug.<group>.<edge>.session.offline
progress.sparkplug.<group>.<edge>.<device>.session.online
progress.sparkplug.<group>.<edge>.<device>.session.offline
progress.sparkplug.<group>.<edge>.<device>.metric.<name>.birth
progress.sparkplug.<group>.<edge>.<device>.metric.<name>.data
progress.sparkplug.<group>.<edge>.metric.<name>.birth
progress.sparkplug.<group>.<edge>.metric.<name>.data
progress.notification.sparkplug
```

Notes on the shape:

- **Group / edge / device tokens** correspond directly to the Sparkplug B
  topic structure (`spBv1.0/{group_id}/{msg_type}/{edge_node_id}/{device_id}`).
  Tokens are slugified by the bridge: lowercase, ASCII alphanumeric, dashes
  only. The slugged value is also returned in payload `original_*` fields for
  display.
- **Edge-level vs device-level metric subjects** both exist because Sparkplug
  edge nodes can publish their own metrics (NDATA) in addition to device
  metrics (DDATA). The token slot count distinguishes them.
- **Session subjects** carry NBIRTH / NDEATH / DBIRTH / DDEATH events. They
  are emitted only on state transitions, not on every frame.
- **Metric subjects** carry NDATA / DDATA frames after birth. The
  `.birth` variant is a per-metric publish at NBIRTH/DBIRTH time so late
  subscribers can hydrate without a full topology fetch.
- **`progress.notification.sparkplug`** is the single subtopic that the
  existing `ServerEventManager` fans out via SSE under topic name
  `sparkplug`. The bridge publishes one notification per state transition and
  per binding firing; raw metric data does NOT fan out via SSE (volume
  control). UI subscribes to the typed metric subjects directly via the
  bridge's read API instead.

### Payload shape (JSON, not protobuf)

Bridge decodes Eclipse Tahu protobuf once and publishes JSON only. Every
subject's payload includes the envelope fields below; per-subject extensions
are listed after.

```jsonc
// envelope (all subjects)
{
  "schema_version": 1,
  "ts_utc_ms": 1714305600000,        // bridge clock at publish time
  "source_ts_utc_ms": 1714305599875, // Sparkplug payload timestamp if present
  "group": "plant1",
  "edge": "edge1",
  "device": "pump3",                 // null on edge-level subjects
  "bd_seq": 14,                      // current session generation
  "seq": 127                         // Sparkplug message seq, 0–255 (uint8, wraps)
}
```

```jsonc
// session.online (NBIRTH / DBIRTH)
{
  ...envelope,
  "kind": "session.online",
  "metrics": [
    { "name": "Temperature", "alias": 1, "type": "Float", "value": 22.4, "quality": "good" },
    { "name": "Running", "alias": 2, "type": "Boolean", "value": false, "quality": "good" }
  ]
}
```

```jsonc
// session.offline (NDEATH / DDEATH)
{
  ...envelope,
  "kind": "session.offline",
  "reason": "ndeath_lwt"             // ndeath_lwt | ddeath | ndeath_cascade | bridge_timeout
}
```

```jsonc
// metric.<name>.data (NDATA / DDATA)
{
  ...envelope,
  "kind": "metric.data",
  "name": "Temperature",
  "alias": 1,
  "type": "Float",
  "value": 24.7,
  "quality": "good"                  // good | stale | bad
}
```

```jsonc
// metric.<name>.birth — same as session.online's metric entries but
// re-emitted as a typed per-metric subject for late subscribers
{
  ...envelope,
  "kind": "metric.birth",
  "name": "Temperature",
  "alias": 1,
  "type": "Float",
  "value": 22.4,
  "quality": "good"
}
```

```jsonc
// progress.notification.sparkplug (SSE fan-out)
{
  "schema_version": 1,
  "ts_utc_ms": 1714305600000,
  "kind": "session.online" | "session.offline" | "session.suspect" | "binding.fired",
  "subject": "progress.sparkplug.plant1.edge1.session.online",
  "summary": "Edge edge1 came online",
  "payload_ref": { /* same as the typed subject's payload */ }
}
```

### Wildcards and consumer patterns

Subscribers should subscribe to the narrowest pattern that fits their need:

- Topology view: `progress.sparkplug.>` (one subscription, all transitions
  and metrics, filtered client-side).
- Per-edge debugging: `progress.sparkplug.<group>.<edge>.>`.
- Single metric subscribe: `progress.sparkplug.<group>.<edge>.<device>.metric.<name>.data`.
- Slim wedge rule engine: `progress.sparkplug.>` (subscribes broadly, evaluates rules in-process).
- Timescale ingester: `progress.sparkplug.>` filtered to `.metric.*.data` and
  `.metric.*.birth` only.

### Type system

`type` field uses Sparkplug B protobuf type names verbatim:
`Int8 Int16 Int32 Int64 UInt8 UInt16 UInt32 UInt64 Float Double Boolean String DateTime`.
v1 demo decodes the numeric, Boolean, and String types. DataSet, Template,
and File are deferred (see `REQUIREMENTS.md` ADV-01 in the post-demo set).

### Quality field

`quality` enum:

- `good`: value is current and reliable.
- `stale`: owning node/device is in DEATH state; last known value retained for
  display, must be visually de-emphasized in UI.
- `bad`: bridge could not decode or trust the value; last known value
  retained but UI should mark it as broken.

The bridge computes quality from Sparkplug's `is_null` / `is_historical`
flags plus its own session state machine.

### Session and seq invariants

- Every payload includes the current `bd_seq` for the owning edge, even on
  device-level subjects.
- `seq` follows the Sparkplug 0–255 wraparound. Consumers must NOT use it to
  detect ordering across sessions; it resets at every NBIRTH.
- Bridge drops any NDEATH whose embedded `bdSeq` does not match the last
  NBIRTH for that edge. Such drops do not produce a session.offline event.

### Session-suspect notifications

The bridge emits `progress.notification.sparkplug` with `kind="session.suspect"`
when it observes anomalies that do NOT yet warrant flipping the session offline
but indicate the session is unhealthy:

- **`reason="seq_gap"`**: the Sparkplug `seq` counter for an edge skipped one
  or more values. Consumers should treat the most recent values as good (the
  gap reflects ordering, not value validity per Sparkplug spec) but surface
  the warning to operators.

Envelope shape (extends the standard notification envelope with a
`payload_ref` carrying gap diagnostics):

```jsonc
{
  "schema_version": 1,
  "ts_utc_ms": 1714305600000,
  "kind": "session.suspect",
  "subject": "progress.sparkplug.<group>.<edge>.session.online",
  "summary": "seq gap on <edge>: expected N, observed M",
  "reason": "seq_gap",
  "payload_ref": {
    "group": "...",
    "edge": "...",
    "device": "..." | null,
    "bd_seq": int,
    "expected_seq": int,
    "observed_seq": int,
    "gaps_observed": int,
    "gaps_window_sec": float
  }
}
```

**Suspect-cap escalation:** When `gaps_observed` reaches the bridge's
configured `gap_tolerance` (default 5) within `gap_window_sec` (default 60s),
the bridge publishes a `session.offline` with `reason="bridge_timeout"` (the
enum entry already documented in this ADR). The `gap_tolerance` and
`gap_window_sec` thresholds are set via `PROGRESS_BRIDGE_GAP_TOLERANCE` and
`PROGRESS_BRIDGE_GAP_WINDOW_SEC` env vars. The session recovers
automatically on the next clean NBIRTH for that edge.

Alias-miss anomalies (NDATA referencing an alias not registered by the
most recent NBIRTH) ALSO contribute to the same gap counter — they are not
a separate suspect kind in v1 demo.

### Edge-NDEATH device-cascade synthesis (bridge feature)

Sparkplug B does NOT mandate that a primary host derive device-level
DEATH events from an edge-level NDEATH — strictly speaking, devices on a
dead edge are simply unreachable. The Progress bridge synthesizes
cascade events as a value-add for downstream consumers:

On receipt of a matching NDEATH for `(group, edge)`, the bridge:

1. Marks the edge session offline in `sparkplug_sessions` KV (alive=False);
   flips `sparkplug_last_values` quality to `stale` for every metric under
   the edge (edge-scope and child-device scope);
2. Publishes the edge-level `progress.sparkplug.<group>.<edge>.session.offline`
   per ADR-0002 (UI flips the edge dot to red — fastest visual signal);
3. For each child device of the dying edge present in `sparkplug_last_values`,
   publishes a synthetic `progress.sparkplug.<group>.<edge>.<device>.session.offline`
   with `reason="ndeath_cascade"` AND iterates the device's metrics
   publishing `metric.<name>.data` with `quality="stale"`.

Step 3 ensures Phase 4 UI consumers (UI-DEMO-04 visual de-emphasis) and
cold-start KV readers see a consistent device-level view without having
to derive child-DEATH from the parent edge's NDEATH themselves.

The cascade ordering is bounded — for the ADR-0007 topology (1 edge × 2
devices × ≤6 metrics each = ~14 publishes) it completes within tens of
milliseconds on local NATS; the bridge's success-criterion budget is 1
second.

**`reason` enum extension:** the device-level cascade `session.offline`
carries `reason="ndeath_cascade"` to distinguish it from a directly-received
DDEATH (`reason="ddeath"`). Both are valid `session.offline` events.

### Retention and KV state

NATS subjects under `progress.sparkplug.*` are NOT persisted to JetStream as
streams in v1 demo. The bridge's state lives in four JetStream KV buckets:

- `sparkplug_sessions` — keyed by `<group>.<edge>`, holds the current bdSeq + the BIRTH metric snapshot (full type/alias/initial-value list per metric).
- `sparkplug_aliases` — keyed by `<group>.<edge>.<bdSeq>`, holds alias→name resolution for the current session.
- `sparkplug_last_seq` — keyed by `<group>.<edge>`, holds the last `seq` observed for monotonicity checking.
- `sparkplug_last_values` — keyed by metric ID (`<group>.<edge>[.<device>].<name>`), holds the last decoded value + timestamp + quality for cold-start hydration. UI can read directly from this bucket without round-tripping through the bridge.

The historian (Timescale, ADR-0005) holds long-form metric history. Live
consumers see live frames on NATS subjects.

`progress.notification.sparkplug` is bridged to the existing
`ServerEventManager` which has its own buffering for SSE; no JetStream
persistence is added there either.

### Subject mapping note

The bridge consumes Sparkplug frames via aiomqtt over the MQTT 3.1.1 endpoint
of NATS, not via NATS-side subscription, so the NATS-MQTT bridge's subject
escape rules do not affect the bridge code. They DO matter when debugging
raw MQTT-bridged frames on the NATS side via `nats sub`. See ADR-0008 for
the conversion table and the debugging recipe.

`progress.notification.sparkplug` is bridged to the existing
`ServerEventManager` which has its own buffering for SSE; no JetStream
persistence is added there either.

### Device-owned channels & inbound-context class (ADR-0016, discussion)

> Forward-looking extension — not part of the frozen v1 demo contract. See [ADR-0016](0016-reactive-event-automation-contract.md) (status: `discussion`).

Beyond the read-only `progress.sparkplug.*` consumer hierarchy above, the reactive-apps work introduces **device-owned channels** scoped per `DEVICE` identity (ADR-0015): a device publishes its own *report* channel and subscribes its own *command* channel, both derivable from `device_id`. A second channel class — **inbound-context** (route-to-page + data injection, e.g. JobStep fields / BoM serials) — carries effects toward the app. Unlike the trust-on-origin telemetry here, inbound-context/command payloads must be **validated by the subscriber** (the channel proves origin, not payload truth). Exact prefixes land when ADR-0016 moves to `decided`.

## Trade-offs and rejected options

**Per-metric subject vs per-device subject.** A naive 1:1 metric→subject
mapping would explode under thousands of metrics. The chosen taxonomy uses
device-level wildcards as the practical filter granularity; per-metric
subjects exist but are intended for narrow consumers, not broad subscribes.

**JSON vs protobuf on NATS.** Decoding once at the bridge and publishing JSON
keeps every downstream consumer trivial (UI, tests, Timescale, future
agents). The bridge's protobuf dependency does not leak. The cost is one
extra (de)serialization but the demo is far from a throughput regime where it
matters.

**Birth as a separate subject vs only inside session.online.** A late-joining
subscriber that misses the NBIRTH would otherwise wait until the next NDATA
to see a metric appear. Re-emitting per-metric `.birth` subjects costs a
bounded burst at session start and dramatically simplifies hydration on
clients.

**Including raw metric subjects in SSE fan-out.** Rejected. SSE is for
notifications and would flood under load. UI uses the bridge's HTTP read API
for topology hydration and subscribes to typed subjects directly via NATS
proxying as needed.

## Consequences

- S1 (bridge) implements the publish path against this exact shape and the
  KV bucket names listed.
- S2 (UI) builds the topology browser and live-value updates against this
  payload shape, regardless of S1's progress.
- S3 (slim wedge) subscribes to `progress.sparkplug.>` and reads
  `metric.data` payloads for rule evaluation.
- S5 (demo data + simulator) tunes the simulator scenario knowing the exact
  metric naming convention the host uses.
- A new schema version bump (`schema_version: 2`) is required for any
  payload shape change after this ADR is `decided`.

## Related

- `.planning/workstreams/sparkplug-demo/research/SUMMARY.md` — original
  taxonomy proposal.
- ADR-0003 — bindings.yaml schema (consumes `metric.data` payloads).
- ADR-0004 — bridge HTTP read API (mirrors this taxonomy in REST shape).
- ADR-0005 — Timescale schema (stores the metric.data payloads).
