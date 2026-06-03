# 0004 — UNS HTTP Read API

**Status:** superseded by Phase 3 D-01..D-03
**Date:** 2026-04-28
**Revised:** 2026-04-28 (renamed `/api/sparkplug/*` → `/api/uns/*`; added `/api/broker/health`)
**Superseded:** 2026-05-04 (Phase 3 discuss-phase D-01..D-03 — Streamlit reads NATS KV + Timescale directly)
**Audience:** S1 (bridge), S2 (UI)
**Supersedes:** none
**Superseded by:** Phase 3 D-01..D-03 (no replacement ADR — read surface moved out of HTTP and into Streamlit-direct queries)

## Why superseded

The bridge is a plugin in the Progress platform — not core to every deployment. Adding `/api/uns/*` endpoints to the main FastAPI service or a `/app/uns` route to the core Quasar webapp couples the platform to an optional feature. Phase 3's D-01 surfaced this constraint and reshaped the read side: Phase 4's Streamlit reports app reads `sparkplug_last_values` + `sparkplug_sessions` JetStream KV buckets via `nats-py` and queries `progress_historian` Timescale via `asyncpg` directly. The whole sparkplug stack (bridge + historian + Streamlit) ships under `deploy/compose/sparkplug.yaml`; main API and core webapp keep zero sparkplug imports.

The original endpoint specifications below are retained for historical context. Do not implement.

## Context

The webapp UI hydrates topology, metric metadata, and historical values via
HTTP from the bridge or the API. NATS subjects (per ADR-0002) carry
streaming updates but cannot serve a fresh-page load. This ADR locks the
HTTP read surface so S2 (frontend) can build against it before S1 (bridge)
implements it, using fixture responses that match this contract verbatim.

The naming convention is **UNS-aligned**: the public read API lives under
`/api/uns/*` because the underlying tree is the unified namespace of NATS
subjects, not a Sparkplug-specific concept. v1 demo populates only the
sparkplug branch of this namespace, but the contract is forward-compatible
with future producers (production events, alarms, agents).

The endpoints split into two groups by host:

- **On the bridge service** (port 8001 internal, not exposed externally):
  `/topology`, `/metrics/:id`, `/health`. Bridge is the source of truth for
  live UNS topology and per-metric live state.
- **On the FastAPI API** (existing port 8000, externally routed):
  `/api/uns/topology`, `/api/uns/metrics/:id`, `/api/uns/history`,
  `/api/broker/health`. The API gates auth (existing JWT middleware) and
  proxies bridge endpoints; UI never talks to the bridge directly.

## Decision

### Bridge-internal endpoints

#### `GET /health`

Returns 200 only when ALL of:

- bridge's MQTT client is connected to the broker;
- bridge's NATS client is connected;
- bridge's primary-host STATE has been observed back as ONLINE on
  `spBv1.0/STATE/<host_id>` with `retain=true, QoS=1`.

Body:

```json
{
  "status": "ok",
  "mqtt": "connected",
  "nats": "connected",
  "primary_host_state": "online",
  "uptime_seconds": 4123
}
```

Used by the API proxy and Docker healthcheck. Returns 503 with the same
shape (filled with the failing field) when any check fails. No auth.

#### `GET /topology`

Returns the bridge's in-memory topology snapshot. Single shot, no streaming.

```json
{
  "schema_version": 1,
  "ts_utc_ms": 1714305600000,
  "groups": [
    {
      "id": "plant1",
      "edges": [
        {
          "id": "edge1",
          "session": { "online": true, "bd_seq": 14, "since_ts_utc_ms": 1714300000000 },
          "edge_metrics": [
            { "id": "plant1.edge1.NodeControl", "name": "NodeControl", "type": "Boolean", "last_value": false, "last_ts_utc_ms": 1714305599875, "quality": "good" }
          ],
          "devices": [
            {
              "id": "pump3",
              "session": { "online": true, "bd_seq": 14, "since_ts_utc_ms": 1714300000000 },
              "metrics": [
                { "id": "plant1.edge1.pump3.Vibration", "name": "Vibration", "type": "Float", "last_value": 24.7, "last_ts_utc_ms": 1714305599875, "quality": "good" }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

Notes:

- `metric.id` uses dotted slug form: `<group>.<edge>[.<device>].<name>`. Same
  ID is used by `/metrics/:id` and `/history`.
- `last_value` follows the same type rules as ADR-0002.
- `quality` enum matches ADR-0002: `good | stale | bad`.
- An edge or device whose session is offline still appears in the response
  with `online: false` and the last known metric values; UI de-emphasizes
  visually.
- The topology shape is currently Sparkplug-shaped (group/edge/device/metric).
  Post-demo when other UNS producers come online, this endpoint can return
  multiple top-level "namespaces" each with its own internal shape; v1
  ships a single namespace.

#### `GET /metrics/:id`

Returns a single metric's metadata + live state. Faster path than walking
the topology when the UI knows the ID (e.g. opening a metric detail view).

```json
{
  "schema_version": 1,
  "id": "plant1.edge1.pump3.Vibration",
  "group": "plant1",
  "edge": "edge1",
  "device": "pump3",
  "name": "Vibration",
  "type": "Float",
  "last_value": 24.7,
  "last_ts_utc_ms": 1714305599875,
  "quality": "good",
  "session": { "online": true, "bd_seq": 14 }
}
```

404 if the metric ID is not in topology.

### FastAPI-exposed endpoints

All require an authenticated user with `production` scope (existing JWT
middleware via `verify_token` dependency). Implementation lives in
`backend/api/endpoints/uns.py` (new file owned by S1).

#### `GET /api/uns/topology`

Proxies the bridge's `GET /topology` 1:1. The API caches nothing; every
request hits the bridge. Bridge response time is sub-10 ms for the demo
topology size, so caching is unnecessary.

#### `GET /api/uns/metrics/:id`

Proxies the bridge's `GET /metrics/:id` 1:1. The route preserves the term
`metrics` because the audience reads it as the leaf entity in a UNS / Sparkplug
namespace; if non-metric subjects join the UNS later, a separate
`/api/uns/subjects/:id` may be added without renaming this one.

#### `GET /api/uns/history?subject=<id>&from=<iso>&to=<iso>&max_points=<n>`

Reads from Timescale (NOT the bridge). Returns downsampled history for the
given metric over the given time range.

Query parameters:

- `subject` (required): the metric ID, dotted slug form. The query parameter
  is named `subject` rather than `metric` so that future non-metric subjects
  can reuse this endpoint.
- `from`, `to` (required): ISO 8601 UTC timestamps. Range cap of 24 hours
  in v1; longer ranges return 400.
- `max_points` (optional, default 500): UI hint. The API picks a
  continuous-aggregate bucket size (per ADR-0005) that yields ≤ this many
  rows.

Response:

```json
{
  "schema_version": 1,
  "subject_id": "plant1.edge1.pump3.Vibration",
  "from_ts_utc_ms": 1714302000000,
  "to_ts_utc_ms": 1714305600000,
  "bucket_seconds": 30,
  "points": [
    { "ts_utc_ms": 1714302000000, "avg": 22.4, "min": 21.9, "max": 23.0, "count": 30 },
    { "ts_utc_ms": 1714302030000, "avg": 22.6, "min": 22.0, "max": 23.1, "count": 30 }
  ]
}
```

If the subject has no history in the requested range, returns `points: []`
with an empty array, not 404.

#### `GET /api/broker/health`

Reports the NATS broker's liveness from the API's perspective. Useful to
the UI's pipeline-health pill so the audience can see "broker / bridge /
API" all green.

Body:

```json
{
  "status": "ok",
  "broker": {
    "url": "nats://broker:4222",
    "connected": true,
    "rtt_ms": 1,
    "jetstream": "enabled",
    "mqtt": "enabled"
  }
}
```

Returns 503 with the failing fields when any check fails. Same auth as the
other API endpoints.

### Authentication

- Bridge endpoints: no auth, listening only on the docker-compose internal
  network. Not exposed via Traefik. The API's network access alone is the
  trust boundary.
- API endpoints: existing JWT bearer + scope check. No new auth code.
  - `/topology`, `/metrics/:id`, `/history`: `production` or `admin` scope.
  - `/broker/health`: `production` or `admin` scope.
- The bridge's *own* outbound POST to `/api/event` (per ADR-0010) uses a
  separate JWT loaded from `/opt/progress/config/.sparkplug-token`, not
  these read endpoints.

### Errors

All endpoints return JSON error bodies with this shape:

```json
{ "error": { "code": "subject_not_found", "message": "..." } }
```

Status code conventions follow Progress's existing patterns: 400 for
invalid query params, 401 for missing token, 403 for insufficient scope,
404 for missing resources, 503 for bridge or Timescale unavailability.

### CORS and rate limits

Existing API CORS rules apply. No new rate limits in v1. UI's own polling
discipline (page-load only for `/topology`; on-demand only for `/history`)
is the rate control. NATS handles the streaming volume; HTTP serves the
cold-start case.

## Trade-offs and rejected options

**Topology hydration via NATS replay vs HTTP single-shot.** A NATS-only
hydration would require either a JetStream stream replay (rejected — see
ADR-0002, no JetStream persistence on raw subjects in v1) or stitching the
state from in-memory by waiting for the next NDATA cycle (rejected — page
load would feel laggy). HTTP single-shot is the simplest cold-start path.

**`/api/sparkplug/*` vs `/api/uns/*`.** UNS naming aligns with the
audience's vocabulary (UNS = Unified Namespace, ISA-95-flavoured) and
keeps the contract forward-compatible to future namespace producers. The
sparkplug-specific name would be a forced rename later.

**Direct UI → bridge.** Considered. Rejected because the bridge has no
auth, exposing it via Traefik would mean adding a new auth path for one
service. Proxying through the existing API is one extra hop and zero new
auth code.

**`/history` on the bridge vs the API.** Bridge does NOT hold long history;
Timescale does. Putting `/history` on the bridge would mean adding a
Postgres connection there. Putting it on the API reuses the API's existing
DB pool and keeps the bridge's responsibilities crisp.

**Server-Sent Events for live updates.** The existing
`progress.notification.sparkplug` SSE channel is sufficient. Live metric
data is consumed via NATS subjects (in dev) or via additional SSE topics
(post-demo). v1 UI uses NATS WebSocket subscription for live values
(through Progress's existing NATS-WebSocket bridge if available; otherwise
falls back to short-interval `/topology` polling during the demo segment
— S2 picks during PLAN).

**`subject` vs `metric` query parameter on `/api/uns/history`.** Chose
`subject` so non-metric subjects can use the same endpoint shape later.

## Consequences

- S1 (bridge) implements `/health`, `/topology`, `/metrics/:id` per this
  spec, plus the FastAPI endpoints in `backend/api/endpoints/uns.py` that
  proxy them and serve `/history` and `/broker/health`.
- S2 (UI) builds against this contract using stub/fixture responses until
  S1's endpoints come online. Hand-written fixture JSON files matching
  these shapes are checked into the repo.
- S5 (demo data) ensures the service-user JWT for the bridge has scope to
  call `/api/event` (per ADR-0010), but is NOT used for these read
  endpoints (those are user-scoped from the UI).

## Related

- ADR-0002 — NATS subject taxonomy (live updates).
- ADR-0005 — Timescale schema and downsampling buckets used by `/history`.
- ADR-0008 — NATS-MQTT subject mapping (relevant when debugging raw bridged subjects, not these read endpoints).
- ADR-0010 — hardcoded automation; uses the `/api/event` write path, not these read endpoints.
- `backend/api/utils/auth.py` — existing scope/auth machinery reused here.
