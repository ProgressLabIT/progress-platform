# Phase 3: Print Service - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver the on-prem print infrastructure: a Python SSE-subscriber client that receives print jobs from the main API and forwards them as raw bytes over TCP to LAN printers, plus the main API endpoints that accept print jobs and distribute them via SSE. Browser UI wiring (print dialog "Send to Printer" action) is Phase 4.

</domain>

<decisions>
## Implementation Decisions

### Architecture (significant pivot from original spec)

The original design (browser → print service HTTP server on LAN IP) was rejected for security reasons: it requires either an unauthenticated/unencrypted endpoint on the operator's network or a full TLS + auth setup on a trivial relay service.

**Chosen architecture: SSE-subscriber pattern**

```
Browser → POST /api/print (main API, existing auth + HTTPS) → SSE channel → Print Service client → TCP → Printer
```

- Print service is an **SSE subscriber client**, not an HTTP server (except GET /health for ops)
- Print service connects **out** to the main API — no inbound port needed, no TLS config, no auth on the service itself
- Browser calls the main API only — existing Traefik + auth covers security
- `printServerURL` in appConfig.js is **no longer needed** — remove from Phase 4 scope
- Phase 3 delivers: print service client + main API print endpoints (POST /api/print, SSE channel, result callback)
- Phase 4 delivers: browser UI wiring only

### SSE channel design

- **Single channel** in the main API — print service subscribes once at startup, receives all jobs for the site
- No per-printer channels, no subscriber enforcement (one service per site is ops convention, not a technical constraint — no need to reject a second subscriber)
- Job payload contains `printer_host`, `printer_port`, `format`, `data`, `copies`, `timeout_seconds`
- Printer reachability determined at print time via TCP attempt — no heartbeating, no pre-flight pings
- Printer online/offline status shown in UI = result of last print attempt (not a live indicator)

### Result reporting

- After TCP send, print service POSTs to `POST /api/print-jobs/{id}/result` on the main API with `{"ok": true}` or `{"ok": false, "error": "...", "detail": "..."}`
- Main API pushes result to the browser via the existing notification/WebSocket system (already in `backend/api`)
- Print job has a DB record in the main API (created on `POST /api/print`, updated on result callback)

### Error response contract

- **TCP failure** → HTTP 503 + JSON body: `{"ok": false, "error": "<type>", "detail": "<message>"}`
- **Validation failure** → HTTP 422 (pydantic handles automatically)
- **Success** → HTTP 200, no body
- Error types to distinguish: `connection_refused`, `timeout`, `send_error`
- Error is surfaced in the main API response to the browser (browser doesn't talk to print service directly)

### TCP timeout

- Default: 5 seconds
- Configurable per-printer: stored in the printer record in app settings DB, passed in the job payload as `timeout_seconds`
- Print service uses `timeout_seconds` from the job payload if present, falls back to 5s default

### ASCII encoding (ZPL)

- Print service **enforces ASCII** when encoding ZPL strings to bytes before TCP send
- Service config env var `PRINT_SERVICE_NON_ASCII` with two modes:
  - `replace` (default) — substitute non-ASCII characters with `?` placeholder, continue printing
  - `error` — return a structured 503 error identifying the non-ASCII content
- **PDF**: decoded from base64 → raw bytes before TCP send (no encoding concern)
- Callers (Phase 4) are responsible for pre-processing: strip/transliterate accented characters before sending, to avoid relying on the `?` fallback

### Deployment

- Standalone optional compose file: `deploy/compose/print.yaml`
- Operators deploy it only on sites with ZPL/PDF printers — not part of the main stack
- Pre-built registry image: `registry.gitlab.com/progresslab/progress-platform/print-service:${VERSION}`
- No Traefik labels (`traefik.enable=false` — not needed, service connects out)
- No `progress` Docker network needed (print service reaches main API via its public URL, not internal network)
- Health endpoint only: `GET /health` returns 200 — for ops monitoring of the client process

### Requirements update required

The original SVC-01–SVC-05 were written for the direct HTTP server approach. The planner **must revise these requirements** to reflect the SSE architecture before creating plans. Key changes:
- SVC-01: POST /print moves to main API, print service only exposes GET /health
- SVC-02: POST /api/print request contract replaces the original print service endpoint spec
- SVC-03: CORS no longer needed on print service (browser never calls it); CORS on new main API endpoint may be needed
- SVC-04/SVC-05: Dockerfile + compose still apply but print service is now a client process, not a server

### Claude's Discretion

- Print job DB collection name and schema
- SSE channel URL path and authentication mechanism (how print service authenticates its SSE subscription to the main API)
- Exact pydantic models for print job request/response
- Whether GET /health on the print service also reports the SSE connection status

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing print infrastructure
- `.planning/phases/02-zpl-generator/02-01-PLAN.md` — generateZpl() signature and ZPL output format the print service will receive
- `webapps/main/src/lib/print/zpl.js` — actual implementation; ASCII-only ZPL output

### Main API patterns
- `backend/api/main.py` — FastAPI app structure, CORS middleware pattern, startup events
- `backend/api/requirements.txt` — sse_starlette already present; pydantic v2, uvicorn, gunicorn
- `backend/api/Dockerfile` — python:3.11-slim base image pattern to follow for print service

### Compose patterns
- `deploy/compose/warehouse.yaml` — standalone optional service compose pattern (no Traefik, pre-built image, progress network)
- `deploy/compose/reporting.yaml` — another standalone service example with network + secrets pattern

### Notification system (result push to browser)
- `backend/api/managers/websocket_manager.py` — existing WebSocket manager for pushing results to browser
- `backend/api/managers/server_event_manager.py` — existing SSE manager; review before adding new SSE channel

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `sse_starlette` in `backend/api/requirements.txt` — SSE infrastructure already installed, no new dependency
- `WebsocketManager` / `ServerEventManager` in `backend/api/managers/` — existing patterns for push notifications to browser; result reporting should plug into these
- `backend/api/main.py` CORS middleware — pattern for adding CORS to the new `/api/print` endpoint if needed

### Established Patterns
- FastAPI app uses `gunicorn -k uvicorn.workers.UvicornWorker` in production (Dockerfile CMD)
- New endpoints live in `backend/api/endpoints/` as packages with `__init__.py` exporting a router
- `get_config()` from `utils/config.py` — use same pattern for print service env var config
- Compose files are standalone per optional service (warehouse, reporting) — print.yaml follows the same structure

### Integration Points
- `backend/api/endpoints/` — add `print/` package with POST /api/print endpoint and SSE channel
- `backend/api/managers/` — result callback updates job status and notifies browser via existing notification system
- `backend/print-service/` — new directory: `main.py` (SSE subscriber loop + TCP sender), `Dockerfile`, `requirements.txt`
- `deploy/compose/print.yaml` — new compose file following warehouse.yaml pattern

</code_context>

<specifics>
## Specific Ideas

- Print service is a long-running Python process: connect to SSE, loop forever receiving jobs, for each job open TCP socket to `printer_host:printer_port`, send bytes, close socket, POST result back
- The service needs graceful reconnect logic for the SSE subscription (main API restarts, network blips)
- "One service per site" is the expected deployment but is not enforced — ops manages it

</specifics>

<deferred>
## Deferred Ideas

- Live printer online/offline status indicator in the UI — would require heartbeating or periodic TCP pings; not worth the complexity for v1. Last-print-result is sufficient.
- Multiple print services per site for HA — out of scope; ops convention handles this.
- `printServerURL` in appConfig.js — no longer needed; remove from Phase 4 scope.

</deferred>

---

*Phase: 03-print-service*
*Context gathered: 2026-03-18*
