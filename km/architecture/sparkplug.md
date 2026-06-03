# Sparkplug B and the Progress Platform

> Internal KM doc. Future user-facing system-integrator material may derive from this.
> Audience: developers, system integrators, and demo presenters who need a working
> mental model of Sparkplug B and how Progress consumes it.

> **Scope note.** This documents Sparkplug B as **one optional ingress adapter**, used
> only when equipment already speaks Sparkplug B natively. Progress does **not** require
> Sparkplug B. Its internal IIoT data plane is **normalized JSON on NATS**, protocol-agnostic
> and fed equally by other edge bridges (OPC-UA, Modbus TCP, EtherNet/IP, S7, plain MQTT).
> Each bridge decodes whatever its equipment emits into that JSON plane; downstream consumers
> (historian, UNS browser, event/Issue automation) only ever see JSON. Sparkplug B is the
> **first** such bridge to ship (the May 15 demo) — first to ship, not foundational. Mandating
> Sparkplug B on a deployment whose equipment does not natively emit it would just mean encoding
> data into Sparkplug protobuf so the bridge can decode it again, for no benefit.

## Why Sparkplug B exists

MQTT is a thin transport: topics and bytes, nothing more. Industrial deployments need
more semantics on top — knowing whether a publisher is alive, whether a value is
current, what type a metric has, what changed since the last update. Sparkplug B is
an Eclipse-Foundation specification (current version 3.0.0) that fixes a topic
naming convention, a Protocol Buffers payload schema, and a session lifecycle on top
of MQTT 3.1.1. It turns MQTT from "raw pub-sub" into "stateful telemetry with type
information and report-by-exception".

Three concepts do most of the work.

**Topic structure.** Sparkplug topics live under a fixed prefix and follow a strict
shape:

```
spBv1.0/<group_id>/<message_type>/<edge_node_id>[/<device_id>]
```

`group_id` is the deployment-wide grouping (often a site or a line). `edge_node_id`
is a gateway or edge device that owns one or more `device_id` children.
`message_type` is one of `NBIRTH`, `NDATA`, `NDEATH`, `DBIRTH`, `DDATA`, `DDEATH`,
`NCMD`, `DCMD`, `STATE`. The `N` prefix means "node-level"; the `D` prefix means
"device-level" (a child under a node).

**Session lifecycle.** Every edge node and device announces itself with a BIRTH
message (`NBIRTH`/`DBIRTH`) listing all its metrics with their types, aliases, and
current values. Subsequent value updates flow as DATA messages (`NDATA`/`DDATA`)
that reference metrics by alias only — saving bandwidth. When a node disconnects
cleanly it publishes a DEATH message; when it disconnects uncleanly the broker
publishes a pre-arranged Last Will and Testament for it. A monotonic `bdSeq`
counter on each (node, session) pair lets consumers detect stale DEATH messages
from a previous session. A per-message `seq` (uint8, wraps at 255 → 0) lets
consumers detect dropped messages within a session.

**Primary host.** A "primary host" application (the consumer of all this telemetry —
think SCADA, MES, historian) publishes a `STATE` message with `retain=true, QoS=1`
to declare itself online. Edge nodes may use this to gate their own publish behaviour
("only publish when a host is listening"). When the host shuts down it publishes
`OFFLINE` on the same topic before disconnecting; otherwise its LWT does the same.

The combination of these three is what turns MQTT into a "real-time, type-aware,
session-managed" data plane suitable for industrial use.

## Progress's approach

Progress uses NATS as its internal messaging backbone. NATS 2.4+ ships with a
built-in MQTT 3.1.1 endpoint that supports the Sparkplug-critical primitives:
LWT, retained messages, QoS 0/1, and JetStream-backed session persistence. We
expose this endpoint on port 1883 as the broker for Sparkplug edge devices.
**One broker, one spine** — Sparkplug edges and Progress internal services see the
same NATS server, just via different protocols.

A custom Python asyncio bridge (`backend/sparkplug_bridge/`) sits between the MQTT
namespace and Progress's internal NATS subject namespace:

```
                         ┌─────────────────────────────────────────────┐
                         │  Sparkplug Edges (simulated or real)        │
                         │  publish via MQTT 3.1.1                     │
                         └──────────────────────┬──────────────────────┘
                                                │ MQTT (port 1883)
                                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│  NATS Server (with JetStream + MQTT 3.1.1 endpoint enabled)            │
└────────────────────────────────────────────────────────────────────────┘
        ▲                                        ▲
        │ aiomqtt (MQTT client)                  │ nats-py (NATS client)
        │                                        │
┌───────┴──────────────────────────────┐         │
│  Sparkplug Bridge                    │         │
│  - Decodes Tahu protobuf             │         │
│  - Tracks bdSeq, alias, seq          │         │
│  - JetStream KV for session state    │         │
│  - Emits Primary Host STATE          │─────────┤
│  - Publishes JSON on                 │         │
│    progress.sparkplug.<group>...     │         │
│  - In-bridge automation (v1 demo)    │         │
└──────────────────────────────────────┘         │
                                                 │
                                ┌────────────────┼─────────────────┐
                                ▼                ▼                 ▼
                       Webapp (UNS browser)  Historian      FastAPI API
                                              (Timescale)
```

The bridge speaks MQTT against NATS-MQTT (consuming MQTT topics with their
original names) and publishes plain NATS JSON on a clean
`progress.sparkplug.>` namespace. Inside the bridge: protobuf decode, session
state machine, alias resolution, primary-host STATE handshake, and a small
hardcoded automation that fires Issues on threshold crossings (v1 demo;
post-demo this becomes a Bytewax-driven binding engine).

The historian is a separate Python process subscribed to the same
`progress.sparkplug.>` subjects, writing batched rows to a TimescaleDB
hypertable. The TimescaleDB instance reuses Progress's existing Postgres
process by enabling the extension on a dedicated `progress_historian`
database.

The webapp's `/app/uns` route is a generic UNS topology browser; v1 ships
with the Sparkplug branch populated, the architecture is forward-compatible
to other UNS producers (production events, future agent emissions).

## System integrator view

### NATS subject taxonomy

The bridge publishes decoded Sparkplug frames as JSON onto a clean NATS
subject namespace. Every subject is rooted at `progress.sparkplug.`:

```
progress.sparkplug.<group>.<edge>.session.online            # NBIRTH
progress.sparkplug.<group>.<edge>.session.offline           # NDEATH
progress.sparkplug.<group>.<edge>.<device>.session.online   # DBIRTH
progress.sparkplug.<group>.<edge>.<device>.session.offline  # DDEATH
progress.sparkplug.<group>.<edge>.<device>.metric.<name>.birth  # per-metric birth
progress.sparkplug.<group>.<edge>.<device>.metric.<name>.data   # NDATA / DDATA
progress.sparkplug.<group>.<edge>.metric.<name>.birth           # edge-level metric birth
progress.sparkplug.<group>.<edge>.metric.<name>.data            # edge-level metric data
progress.notification.sparkplug                                 # SSE fan-out
```

Tokens (`group`, `edge`, `device`) are slugified by the bridge: lowercase,
ASCII alphanumeric, dashes only.

Payloads are JSON. Every payload includes an envelope:

```jsonc
{
  "schema_version": 1,
  "ts_utc_ms": 1714305600000,
  "source_ts_utc_ms": 1714305599875,
  "group": "plant1",
  "edge": "edge1",
  "device": "pump3",
  "bd_seq": 14,
  "seq": 127
}
```

A `metric.data` payload extends the envelope with `name`, `alias`, `type`,
`value`, `quality`. See `decisions/0002-nats-subject-taxonomy.md` for the
full payload reference.

### NATS-side debugging (escape rules)

For ops or debugging that wants to read the **raw** Sparkplug protobuf
frames from the NATS side (instead of consuming through the bridge),
remember the NATS-MQTT escape rule:

| In MQTT | Becomes on NATS |
|---|---|
| `/` (separator) | `.` |
| `.` (literal) | `//` (replaces, does not prepend) |

So `spBv1.0/plant1/NDATA/edge1/pump3` shows up on NATS as
`spBv1//0.plant1.NDATA.edge1.pump3`. To tail all Sparkplug v1.0 traffic:

```bash
nats sub 'spBv1//0.>'
```

The bridge itself does not see this escape — it consumes via aiomqtt over
MQTT semantics. The decoded JSON path on `progress.sparkplug.>` is also
unaffected. Only raw-Sparkplug-on-NATS paths surface the escape.

For pretty-printed decoded output, use `progress tap`:

```bash
progress tap 'progress.sparkplug.>'
progress tap 'spBv1//0.>'  # raw, with built-in protobuf decode
```

See `decisions/0008-natsmqtt-subject-mapping.md` for the full conversion
table.

### REST endpoints

The webapp talks to the FastAPI API (not the bridge directly). The API's
UNS surface lives under `/api/uns/*`:

| Endpoint | Purpose |
|---|---|
| `GET /api/uns/topology` | Tree of groups → edges → devices → metrics, with last values |
| `GET /api/uns/metrics/:id` | One metric's metadata + last value |
| `GET /api/uns/history?subject=<id>&from=<iso>&to=<iso>&max_points=<n>` | Downsampled history from Timescale |
| `GET /api/broker/health` | NATS broker liveness from the API's perspective |

All require an authenticated user with `production` or `admin` scope. The
bridge exposes equivalent unauthenticated endpoints
(`/topology`, `/metrics/:id`, `/health`) on its internal port; the API
proxies them.

See `decisions/0004-bridge-http-read-api.md` for the full contract.

### Security model

- **Edge devices ↔ broker**: standard MQTT auth (TLS + client cert or
  username/password) configured in the NATS-MQTT account section. v1 demo
  runs on plain TCP for simplicity; production deployments enable TLS.
- **Bridge ↔ API**: the bridge POSTs to `/api/event` using a JWT bearer
  token issued for a service user (`USR-SPARKPLUG-BRIDGE`). The token
  lives in `/opt/progress/config/.sparkplug-token` (file mode 0600),
  mounted into the bridge container. Filesystem access on the host is the
  trust boundary.
- **Webapp ↔ API**: existing JWT bearer + scope checks via
  `verify_token` dependency, identical to all other API routes.
- **Bridge HTTP ↔ API**: bridge's read endpoints are unauthenticated but
  not exposed externally. The API's `/api/uns/*` is the only externally
  reachable surface; it proxies to the bridge over the internal Docker
  Swarm overlay network.

### Persistence

| Store | Holds | Backed by |
|---|---|---|
| In-memory (bridge) | Live topology, alias map, last-value cache | Process memory |
| JetStream KV | Session state, alias map, last seq, last values | NATS JetStream |
| TimescaleDB hypertable `metric_samples` | Metric history (avg / min / max / count) | Postgres + TimescaleDB extension |
| ArangoDB | Issues, work orders, phases, all Progress domain state | ArangoDB cluster |

The TimescaleDB instance is the existing Prefect `workflow-db` Postgres
process re-imaged to `timescale/timescaledb:latest-pg15`. Prefect's
`prefect` database is unaffected; the new `progress_historian` database
holds the hypertable. See `decisions/0005-timescale-schema-and-downsampling.md`.

## What's next (post-demo)

The v1 demo ships a single hardcoded automation in the bridge. Post-demo
work introduces a configurable engine on Bytewax 1.x as a separate
`backend/bindings/` service:

- `bindings.yaml` per the schema sketched in
  `decisions/0003-bindings-yaml-schema.md`, refined with operator
  vocabulary.
- Each binding compiles to a Bytewax dataflow:
  `input(NATSSource).filter(match).window(dwell).filter(operator).map(latch).map(render_payload).output(HTTPSink)`.
- Hot-reload, debounce, circuit breaker, generic-subject matching.
- Machine-as-user resolution: bindings can target a "machine user" and
  the engine auto-resolves the running job (linking phase, work order,
  product, assignee).

See `decisions/0009-stream-processing-framework.md` for the framework
choice rationale and the migration path from the v1 hardcoded module.

ISA-18.2 alarms (state machine with deadband + on-delay + off-delay)
follow the engine on the same plumbing.

## References

- Eclipse Sparkplug 3.0.0 specification — <https://sparkplug.eclipse.org/specification/>
- Eclipse Tahu reference implementation — <https://github.com/eclipse-sparkplug/tahu>
- pysparkplug (active PyPI library, used by the simulator) —
  <https://pypi.org/project/pysparkplug/>
- aiomqtt (MQTT client used by the bridge) —
  <https://pypi.org/project/aiomqtt/>
- NATS-MQTT documentation —
  <https://docs.nats.io/running-a-nats-service/configuration/mqtt>
- TimescaleDB documentation — <https://docs.timescale.com/>
- Workstream artifacts: `.planning/workstreams/sparkplug-demo/`
- ADR registry: `km/decisions/index.md`
