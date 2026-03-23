---
phase: 03-print-service
plan: 02
subsystem: infra
tags: [python, asyncio, httpx, httpx-sse, tcp, docker, pydantic-settings, pytest]

# Dependency graph
requires:
  - phase: 03-print-service/03-01
    provides: GET /print-jobs/stream SSE endpoint and POST /print-jobs/{id}/result callback on main API

provides:
  - backend/print-service/tcp_sender.py: encode_zpl (ASCII modes), decode_pdf (base64), send_tcp (async TCP with error classification)
  - backend/print-service/config.py: pydantic-settings Settings with PRINT_SERVICE_* env prefix
  - backend/print-service/requirements.txt: httpx, httpx-sse, pydantic, pydantic-settings, pytest, pytest-asyncio
  - backend/print-service/test_tcp_sender.py: 8 unit tests covering all tcp_sender functions
  - backend/print-service/main.py: SSE subscriber loop, job handler, result reporter, health server on :8200
  - backend/print-service/Dockerfile: python:3.11-slim image, CMD python main.py, HEALTHCHECK via urllib
  - deploy/compose/print.yaml: standalone optional compose file, no networks, traefik.enable=false

affects: [04-print-ui]

# Tech tracking
tech-stack:
  added:
    - httpx-sse>=0.4 (SSE client for print service)
    - pytest-asyncio>=0.23 (async test support for print service unit tests)
  patterns:
    - Raw asyncio TCP send via asyncio.open_connection() + asyncio.wait_for() for timeout
    - Minimal HTTP health endpoint as raw asyncio TCP server (no FastAPI/uvicorn — client process)
    - SSE reconnect loop with exponential-ish backoff (delay, delay*2) on unexpected errors
    - pydantic-settings with PRINT_SERVICE_* env prefix following main API get_config() pattern

key-files:
  created:
    - backend/print-service/main.py
    - backend/print-service/config.py
    - backend/print-service/tcp_sender.py
    - backend/print-service/requirements.txt
    - backend/print-service/test_tcp_sender.py
    - backend/print-service/Dockerfile
    - deploy/compose/print.yaml
  modified: []

key-decisions:
  - "Health endpoint implemented as raw asyncio TCP server on :8200 — no FastAPI/uvicorn needed for a client process, keeps image lightweight"
  - "PDF copies > 1 sends data multiple times via separate TCP calls; ZPL copies handled by ^PQ in ZPL string from generateZpl()"
  - "asyncio.sleep(0.05) added in test_send_tcp_success to yield control for server handler to complete before asserting received data"
  - "Dockerfile copies only main.py, config.py, tcp_sender.py — no test file in image"

patterns-established:
  - "Print service is a plain Python process: asyncio.run(main()), CMD python main.py, no WSGI/ASGI server"
  - "TCP error classification: timeout (asyncio.TimeoutError), connection_refused (ConnectionRefusedError), send_error (OSError)"
  - "compose file for on-prem optional service: no networks:, no volumes:, traefik.enable=false, reaches main API via public PRINT_SERVICE_API_URL"

requirements-completed: [SVC-01, SVC-02, SVC-04, SVC-05]

# Metrics
duration: 5min
completed: 2026-03-18
---

# Phase 03 Plan 02: Print Service Client Summary

**Standalone Python print service: asyncio SSE subscriber over httpx-sse relays ZPL/PDF jobs to TCP printers via asyncio.open_connection(), with health endpoint, Dockerfile, and Docker Compose deployment file**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-18T21:45:39Z
- **Completed:** 2026-03-18T21:50:00Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Created complete `backend/print-service/` directory with tcp_sender.py (ASCII/base64 encoding + async TCP), config.py (pydantic-settings with PRINT_SERVICE_* prefix), and 8 passing unit tests
- Implemented main.py with asyncio.gather() running subscribe_loop (SSE subscriber with 5s reconnect) and health_server (raw TCP HTTP on :8200 reporting sse_connected status)
- Created Dockerfile (python:3.11-slim, CMD python main.py, HEALTHCHECK via stdlib urllib) and deploy/compose/print.yaml (no networks, traefik.enable=false, PRINT_SERVICE_* env vars)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create tcp_sender.py and config.py** - `618cadea` (feat)
2. **Task 2: Create main.py SSE subscriber, Dockerfile, and compose file** - `972572f2` (feat)

## Files Created/Modified

- `backend/print-service/tcp_sender.py` - encode_zpl (ASCII with replace/error modes), decode_pdf (base64), send_tcp (async TCP, timeout/connection_refused/send_error classification)
- `backend/print-service/config.py` - pydantic-settings Settings: api_url, api_token, non_ascii, reconnect_delay with PRINT_SERVICE_* env prefix
- `backend/print-service/requirements.txt` - httpx, httpx-sse, pydantic, pydantic-settings, pytest, pytest-asyncio
- `backend/print-service/test_tcp_sender.py` - 8 unit tests: encode_zpl ASCII/replace/error, decode_pdf valid/invalid, send_tcp success/refused/timeout
- `backend/print-service/main.py` - subscribe_loop + handle_job + report_result + health_server + main() via asyncio.gather
- `backend/print-service/Dockerfile` - python:3.11-slim, copies only 3 Python files, HEALTHCHECK via urllib, CMD python main.py
- `deploy/compose/print.yaml` - standalone optional compose, no progress network, traefik.enable=false

## Decisions Made

- Health endpoint is a raw asyncio TCP server on port 8200 — keeps the print service as a lightweight client process with no WSGI/ASGI overhead
- PDF copies > 1 sends data multiple times via separate TCP calls; ZPL copies are handled by `^PQ` in the ZPL string generated by generateZpl() in Phase 2
- Dockerfile copies only the three runtime Python files (excludes test_tcp_sender.py from the image)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added asyncio.sleep(0.05) in test_send_tcp_success for timing**
- **Found during:** Task 1 (TDD — GREEN phase)
- **Issue:** test_send_tcp_success passed for {"ok": True} but asserted received_data == [] because the server's handle_client coroutine hadn't run yet when assertion executed
- **Fix:** Added `await asyncio.sleep(0.05)` inside the `async with server:` block after send_tcp to yield control to the event loop so handle_client completes
- **Files modified:** backend/print-service/test_tcp_sender.py
- **Verification:** All 8 tests pass
- **Committed in:** 618cadea (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — test timing bug)
**Impact on plan:** Necessary for test correctness. No scope creep.

## Issues Encountered

None beyond the timing fix above.

## User Setup Required

External services require manual configuration:

**PRINT_SERVICE_API_TOKEN** must be a non-expiring JWT issued for a service user account via the main API's `issue_token()`. It cannot be auto-generated. Operator must:
1. Create a service user account on the main API
2. Call `issue_token()` for that account with no expiry
3. Set `PRINT_SERVICE_API_TOKEN` in the compose environment or `.env` file

**PRINT_SERVICE_API_URL** must be the public URL of the main API including the `/api` suffix (e.g., `https://site.progresslab.it/api`).

## Next Phase Readiness

- Print service is fully implemented and ready for Docker image build and on-prem deployment
- Phase 04 (browser UI wiring) only needs to call `POST /api/print-job` on the main API — no print service URL needed
- The print service's `_sse_connected` health flag verifies the SSE subscription is active after deployment

---
*Phase: 03-print-service*
*Completed: 2026-03-18*
