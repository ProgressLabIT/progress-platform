---
title: Integration — Admin & Integrator
description: NATS subjects, Sparkplug bridge HTTP read API, and OpenAPI consumer notes for Progress Platform.
---

# Integration

> If you're building a downstream consumer of the Progress Platform — subscribing
> to real-time events, querying historical Sparkplug data, or generating a typed
> SDK from the OpenAPI schema — this page maps the integration surfaces and points
> at the locked contracts that govern each one.

## NATS subject taxonomy

Two subject hierarchies coexist on the broker:

1. **`progress.notification.<subtopic>`** — domain events emitted by the FastAPI
   backend after a successful transaction commit. The full per-event mapping is in
   the [Events reference](/events/). Subtopics include `production`, `inventory`,
   `serial`, `issue`, `task`, `message`, `user.{user_key}`.
2. **`progress.sparkplug.>`** — Sparkplug B frames decoded by the Sparkplug bridge
   into JSON. Bridge is the sole producer; the API, UI, slim wedge, and historian
   are read-only consumers.

The Sparkplug subject shape is locked in ADR-0002:

| Subject pattern | Carries | Producer |
|-----------------|---------|----------|
| `progress.sparkplug.<group>.<edge>.session.online` | NBIRTH state transition + initial metric snapshot | bridge |
| `progress.sparkplug.<group>.<edge>.session.offline` | NDEATH (with `reason`: `ndeath_lwt`, `bridge_timeout`) | bridge |
| `progress.sparkplug.<group>.<edge>.<device>.session.online` | DBIRTH device-level transition | bridge |
| `progress.sparkplug.<group>.<edge>.<device>.session.offline` | DDEATH or synthetic NDEATH cascade (`reason="ndeath_cascade"`) | bridge |
| `progress.sparkplug.<group>.<edge>.metric.<name>.birth` | Per-metric birth re-emit for late subscribers | bridge |
| `progress.sparkplug.<group>.<edge>.metric.<name>.data` | NDATA edge-level metric value | bridge |
| `progress.sparkplug.<group>.<edge>.<device>.metric.<name>.birth` | Per-metric birth re-emit (device-scoped) | bridge |
| `progress.sparkplug.<group>.<edge>.<device>.metric.<name>.data` | DDATA device-level metric value | bridge |
| `progress.notification.sparkplug` | SSE fan-out — session transitions, `session.suspect` (seq gap), `binding.fired` | bridge |

Every payload includes the canonical envelope: `schema_version`, `ts_utc_ms`,
`source_ts_utc_ms`, `group`, `edge`, `device` (null at edge level), `bd_seq`, `seq`.
Tokens are slugified by the bridge to lowercase ASCII alphanumeric + dashes; the
unslugged values are returned in `original_*` fields for display.

> The locked taxonomy is defined in
> [ADR-0002 — NATS Subject Taxonomy](https://github.com/ProgressLabIT/progress-platform/blob/DEV/km/decisions/0002-nats-subject-taxonomy.md)
> of the Sparkplug demo workstream. Do not extend or override subjects without
> updating that ADR. The repo path is
> `km/decisions/0002-nats-subject-taxonomy.md`.

The bridge does NOT persist raw subjects to JetStream streams. Live state lives in
four JetStream KV buckets — `sparkplug_sessions`, `sparkplug_aliases`,
`sparkplug_last_seq`, `sparkplug_last_values` — for cold-start hydration.

## Sparkplug bridge HTTP read API

The bridge serves an internal HTTP read surface that is proxied by the FastAPI
backend under `/api/uns/*`. UI clients and downstream consumers should use the
proxied endpoints, not the bridge directly — the bridge port is not exposed via
Traefik and has no auth of its own.

| Endpoint | Method | Purpose | Notes |
|----------|--------|---------|-------|
| `/api/uns/topology` | GET | Single-shot snapshot of the whole UNS tree (groups → edges → devices → metrics, last values + quality). | Auth: `production` or `admin` scope. Proxies bridge `/topology` 1:1. |
| `/api/uns/metrics/{id}` | GET | Single metric metadata + live state. `id` is dotted slug `<group>.<edge>[.<device>].<name>`. | Auth: `production` or `admin` scope. 404 if metric unknown. |
| `/api/uns/history` | GET | Downsampled metric history from Timescale. Query params: `subject`, `from`, `to`, `max_points` (default 500). 24h range cap in v1. | Auth: `production` or `admin` scope. Bucket size auto-selected to honor `max_points`. |
| `/api/broker/health` | GET | NATS broker liveness from the API's perspective (connection status, RTT, JetStream + MQTT enablement). | Auth: `production` or `admin` scope. 503 on broker outage. |
| `/health` (bridge-internal) | GET | Bridge composite health: MQTT connected + NATS connected + primary-host STATE observed online. | No auth; not exposed via Traefik. Used by Docker healthcheck. |

> These endpoints require the Sparkplug bridge stack to be running. The bridge is
> an optional Compose extension — enable it via
> `deploy/compose/sparkplug.yaml`. See
> [ADR-0004 — UNS HTTP Read API](https://github.com/ProgressLabIT/progress-platform/blob/DEV/km/decisions/0004-bridge-http-read-api.md)
> for the full request/response shapes and error model. The repo path is
> `km/decisions/0004-bridge-http-read-api.md`.
> ADR-0004 was superseded by Phase 3 D-01..D-03, which moves the read surface
> into a Streamlit app reading NATS KV + Timescale directly. Verify your
> deployment's read path before integrating.

## OpenAPI consumer notes

The Progress Platform API publishes its full OpenAPI 3.x schema at
`/api/openapi.json` (served by FastAPI at startup). The schema is also committed
to the repository at `docs/public/openapi.json`, generated by
`scripts/export_openapi.py` on every build of the docs site, so consumers can
diff schema versions without a running deployment.

To generate a typed client:

```bash
# Python client via openapi-generator-cli
openapi-generator-cli generate \
  -i https://<your-host>/api/openapi.json \
  -g python \
  -o ./progress-client

# TypeScript client (axios template)
openapi-generator-cli generate \
  -i https://<your-host>/api/openapi.json \
  -g typescript-axios \
  -o ./progress-client-ts
```

Authenticate generated clients with the same JWT bearer token issued by
`POST /api/auth` (see the [API reference](/api/) → Security section). The
`/api/hello` route is the only public endpoint; everything else requires a
valid bearer.

The [API reference](/api/) renders the same schema inline with per-endpoint
examples — use it for quick lookup before committing to SDK generation.

## Related

- [API reference](/api/) — inline OpenAPI schema browser
- [Events reference](/events/) — full `progress.notification.*` mapping by event type
- [Deployment](/admins/deployment) — how to enable the Sparkplug bridge stack
- [Operations](/admins/operations) — broker and bridge health verification
- ADR-0002 — NATS subject taxonomy (`km/decisions/0002-nats-subject-taxonomy.md`)
- ADR-0004 — Bridge HTTP read API (`km/decisions/0004-bridge-http-read-api.md`)
