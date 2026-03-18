# Phase 3: Print Service - Research

**Researched:** 2026-03-18
**Domain:** Python SSE subscriber client + FastAPI print endpoints + raw TCP socket sender
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Architecture: SSE-subscriber pattern**

```
Browser → POST /api/print (main API, existing auth + HTTPS) → SSE channel → Print Service client → TCP → Printer
```

- Print service is an **SSE subscriber client**, not an HTTP server (except GET /health for ops)
- Print service connects **out** to the main API — no inbound port needed, no TLS config, no auth on the service itself
- Browser calls the main API only — existing Traefik + auth covers security
- `printServerURL` in appConfig.js is **no longer needed** — remove from Phase 4 scope
- Phase 3 delivers: print service client + main API print endpoints (POST /api/print, SSE channel, result callback)
- Phase 4 delivers: browser UI wiring only

**SSE channel design**
- Single channel in the main API — print service subscribes once at startup, receives all jobs for the site
- No per-printer channels, no subscriber enforcement
- Job payload contains `printer_host`, `printer_port`, `format`, `data`, `copies`, `timeout_seconds`
- Printer reachability determined at print time via TCP attempt

**Result reporting**
- After TCP send, print service POSTs to `POST /api/print-jobs/{id}/result` with `{"ok": true}` or `{"ok": false, "error": "...", "detail": "..."}`
- Main API pushes result to browser via existing WebSocket/notification system
- Print job has a DB record in the main API (created on `POST /api/print`, updated on result callback)

**Error response contract**
- TCP failure → HTTP 503 + `{"ok": false, "error": "<type>", "detail": "<message>"}`
- Validation failure → HTTP 422 (pydantic automatic)
- Success → HTTP 200, no body
- Error types: `connection_refused`, `timeout`, `send_error`

**TCP timeout**
- Default: 5 seconds
- Configurable per-printer via `timeout_seconds` in job payload

**ASCII encoding (ZPL)**
- Enforce ASCII when encoding ZPL strings
- `PRINT_SERVICE_NON_ASCII` env var: `replace` (default) or `error`
- PDF: decoded from base64 → raw bytes, no encoding concern

**Deployment**
- Standalone optional compose file: `deploy/compose/print.yaml`
- Pre-built registry image: `registry.gitlab.com/progresslab/progress-platform/print-service:${VERSION}`
- `traefik.enable=false` — not needed, service connects out
- No `progress` Docker network needed — print service reaches main API via its public URL
- Health endpoint only: `GET /health` returns 200

**Requirements revision required**
- SVC-01: POST /print moves to main API; print service only exposes GET /health
- SVC-02: POST /api/print request contract replaces original endpoint spec
- SVC-03: CORS no longer needed on print service; CORS on new main API endpoint if needed
- SVC-04/SVC-05: Dockerfile + compose still apply but print service is a client process

### Claude's Discretion

- Print job DB collection name and schema
- SSE channel URL path and authentication mechanism (how print service authenticates its SSE subscription to the main API)
- Exact pydantic models for print job request/response
- Whether GET /health on the print service also reports the SSE connection status

### Deferred Ideas (OUT OF SCOPE)

- Live printer online/offline status indicator in the UI (heartbeating / periodic TCP pings)
- Multiple print services per site for HA
- `printServerURL` in appConfig.js — removed from Phase 4 scope
</user_constraints>

<phase_requirements>
## Phase Requirements

Note: Requirements SVC-01 through SVC-05 were written for the original direct HTTP server approach. The planner MUST revise these to reflect the SSE-subscriber architecture before creating plans.

| ID | Original Description | Revised Scope |
|----|---------------------|---------------|
| SVC-01 | `backend/print-service/main.py` FastAPI app with GET /health and POST /print | `backend/print-service/main.py` — SSE subscriber client process; GET /health only (no POST /print on the service). POST /api/print lives on main API. |
| SVC-02 | POST /print accepts printer_host, printer_port, format, data, copies; raw TCP send | POST /api/print on the main API accepts these fields + timeout_seconds; stores DB record, enqueues SSE event to print service; print service does the TCP send |
| SVC-03 | CORS via PRINT_SERVICE_CORS_ORIGINS env var | CORS no longer needed on print service (browser never calls it). Main API /api/print is behind existing CORS config. |
| SVC-04 | Dockerfile (python:3.11-slim, port 8200, uvicorn) | Dockerfile for print service: python:3.11-slim, no port exposure needed (client process), simple `python main.py` CMD |
| SVC-05 | deploy/compose/print.yaml with traefik.enable=false | deploy/compose/print.yaml — standalone optional compose, no Traefik, no progress network; service connects out via public API URL |
</phase_requirements>

---

## Summary

Phase 3 delivers two separate deliverables: (1) new endpoints on the existing main API (`POST /api/print`, an SSE channel for the print service to subscribe to, and `POST /api/print-jobs/{id}/result`), and (2) a new standalone Python service (`backend/print-service/`) that acts as a long-running SSE subscriber — receiving print jobs and forwarding them as raw bytes over TCP to LAN printers.

The architecture pivot from the original spec (browser → print service HTTP server) to the SSE-subscriber pattern eliminates all inbound networking concerns for the print service. The print service connects out to the main API over HTTPS, subscribes to a job SSE stream, and re-posts results back. The main API handles authentication, CORS, and browser-facing result delivery through the existing WebSocket/notification infrastructure.

The main implementation risk is the SSE reconnect loop in the print service client: it must handle main API restarts, network blips, and gracefully resume without losing jobs (in-flight jobs during disconnect are acceptable to lose for v1 given the ops convention of one service per site). The secondary challenge is correctly partitioning between the new main API endpoints and the new standalone service process.

**Primary recommendation:** Use `httpx` (already in `backend/api/requirements.txt`) with `httpx-sse` for the print service SSE client; `asyncio` raw TCP socket send; pydantic-settings for env config following the exact `get_config()` pattern in the main API.

---

## Standard Stack

### Core (Print Service — new standalone process)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.11 | Runtime | Matches `python:3.11-slim` base in all existing Dockerfiles |
| httpx | 0.* | HTTP client for SSE subscription + result POST | Already in `backend/api/requirements.txt`; supports async streaming |
| httpx-sse | latest stable | SSE client wrapper around httpx | Standard companion to httpx for consuming SSE streams |
| pydantic-settings | 2.* | Env var config | Same pattern as main API `get_config()` |
| pydantic | 2.* | Data models / validation | Already used throughout project |
| asyncio | stdlib | Async event loop, TCP socket send | No dependency needed; Python stdlib |

### Core (Main API — new endpoints on existing service)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| sse_starlette | latest | SSE endpoint (job channel) | **Already installed** in `backend/api/requirements.txt` |
| FastAPI | 0.* | Router + endpoint definitions | Already the app framework |
| pydantic | 2.* | Request/response models | Already used |
| python-arango | 8.* | DB writes for print job records | Already used |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| gunicorn + uvicorn | Already present | Production WSGI wrapper | Main API uses this pattern; print service is a plain Python process, not a server |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| httpx-sse | aiohttp SSE | httpx-sse is the natural companion to httpx already in requirements; aiohttp adds a new dependency |
| asyncio TCP socket | socket stdlib (sync) | asyncio socket allows non-blocking send within async event loop; sync socket would require threading |
| asyncio TCP socket | `asyncio.open_connection()` | `asyncio.open_connection()` is the clean async API — prefer over raw socket |

**Installation (print service):**
```bash
# backend/print-service/requirements.txt
httpx==0.*
httpx-sse
pydantic==2.*
pydantic-settings==2.*
```

---

## Architecture Patterns

### Recommended Project Structure
```
backend/
└── print-service/
    ├── main.py            # Entry point: SSE subscriber loop + TCP sender
    ├── config.py          # pydantic-settings config (PRINT_SERVICE_* env vars)
    ├── tcp_sender.py      # Raw TCP send logic, error classification
    ├── Dockerfile         # python:3.11-slim, CMD ["python", "main.py"]
    └── requirements.txt   # httpx, httpx-sse, pydantic, pydantic-settings

backend/api/endpoints/
├── print.py               # EXISTING — add POST /api/print + SSE channel + result callback
└── ...

backend/api/models/
├── print.py               # EXISTING — add PrintJob, PrintJobRequest, PrintJobResult models
└── ...

deploy/compose/
└── print.yaml             # NEW — standalone optional compose file
```

### Pattern 1: SSE subscriber reconnect loop (print service main.py)
**What:** Long-running async loop that connects to main API SSE, reconnects on disconnect
**When to use:** Always — this is the core process logic

```python
# Source: httpx-sse documentation pattern
import asyncio
import httpx
from httpx_sse import connect_sse

async def subscribe_loop(api_url: str, api_token: str):
    headers = {"Authorization": f"Bearer {api_token}"}
    while True:
        try:
            async with httpx.AsyncClient() as client:
                async with connect_sse(
                    client, "GET", f"{api_url}/api/print-jobs/stream",
                    headers=headers
                ) as event_source:
                    async for sse in event_source.aiter_sse():
                        job = parse_job(sse.data)
                        await handle_job(client, api_url, headers, job)
        except (httpx.ConnectError, httpx.ReadError, httpx.RemoteProtocolError) as e:
            print(f"SSE disconnected: {e} — reconnecting in 5s")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Unexpected error: {e} — reconnecting in 10s")
            await asyncio.sleep(10)
```

### Pattern 2: Raw TCP send with asyncio (tcp_sender.py)
**What:** Open TCP connection, send bytes, close, classify error
**When to use:** For each print job received from SSE

```python
# Source: Python asyncio docs — asyncio.open_connection
import asyncio

async def send_tcp(host: str, port: int, data: bytes, timeout: float = 5.0):
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout
        )
        writer.write(data)
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return {"ok": True}
    except asyncio.TimeoutError:
        return {"ok": False, "error": "timeout", "detail": f"Connection to {host}:{port} timed out after {timeout}s"}
    except ConnectionRefusedError:
        return {"ok": False, "error": "connection_refused", "detail": f"Connection refused at {host}:{port}"}
    except OSError as e:
        return {"ok": False, "error": "send_error", "detail": str(e)}
```

### Pattern 3: SSE channel endpoint on main API (following existing notification.py pattern)
**What:** FastAPI endpoint that yields SSE events to the subscribed print service
**When to use:** Main API — new `/api/print-jobs/stream` endpoint

```python
# Source: existing backend/api/endpoints/notification.py pattern
from fastapi import Request, APIRouter, Depends
from sse_starlette.sse import EventSourceResponse
from managers.server_event_manager import ServerEventManager
from utils import auth

router = APIRouter()

@router.get("/print-jobs/stream")
async def print_job_stream(request: Request, token=Depends(auth.verify_token)):
    return EventSourceResponse(
        ServerEventManager.getInstance().push_events(request, "print-jobs")
    )
```

### Pattern 4: Config following main API get_config() pattern
**What:** pydantic-settings BaseSettings with env_prefix
**When to use:** All env var access in print service

```python
# Source: backend/api/utils/config.py (existing pattern)
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    api_url: str = "http://localhost:8000"
    api_token: str = ""                           # JWT for SSE auth
    non_ascii: str = "replace"                    # "replace" | "error"

    model_config = SettingsConfigDict(
        env_prefix="print_service_",
        env_file=".env"
    )

@lru_cache()
def get_config() -> Settings:
    return Settings()
```

### Pattern 5: POST /api/print + DB record (main API)
**What:** Accept print job from browser, store in ArangoDB, enqueue SSE event
**When to use:** New endpoint in `backend/api/endpoints/print.py`

```python
# Source: existing print.py pattern + ServerEventManager.enqueue()
@router.post("/print", dependencies=[Depends(auth.verify_token)])
async def create_print_job(job: PrintJobRequest):
    # 1. Insert DB record → get job_key
    record = {"status": "pending", "printer_host": job.printer_host, ...}
    result = db.collection("PrintJob").insert(record)
    job_key = result["_key"]
    # 2. Enqueue SSE event to print service
    payload = job.model_dump()
    payload["job_id"] = job_key
    ServerEventManager.getInstance().enqueue(
        json.dumps({"subtopic": "print-jobs", **payload})
    )
    return {"job_id": job_key}
```

### Anti-Patterns to Avoid
- **Using uvicorn/gunicorn for the print service:** The print service is a plain async Python process (not an HTTP server). Use `python main.py` → `asyncio.run(main())`. The Dockerfile CMD should be `["python", "main.py"]`, not a gunicorn invocation.
- **Blocking TCP socket in async context:** Use `asyncio.open_connection()`, not `socket.socket()`. A blocking socket blocks the entire event loop.
- **Using `asyncio.wait_for` wrong:** Wrap the entire `open_connection` call in `wait_for`, not just `writer.write()` — the connection phase is where timeout applies.
- **Not closing writer properly:** Always call `writer.close()` AND `await writer.wait_closed()` to avoid ResourceWarning and half-open connections.
- **Fire-and-forget result callback:** Always await the result POST back to the main API so connection errors surface in logs.
- **Assuming SSE subtopic format in ServerEventManager:** `enqueue()` reads `json.loads(message)['subtopic']` — the payload must be JSON with a `subtopic` key matching the topic string used in `push_events()`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SSE client with reconnect | Custom HTTP chunked reader | `httpx-sse` | Handles chunked transfer, event parsing, malformed events |
| Async TCP with timeout | `threading.Timer` + socket | `asyncio.wait_for` + `asyncio.open_connection` | Clean cancellation, no thread leaks |
| Env var config | `os.environ.get()` calls | `pydantic-settings` BaseSettings | Validation, type coercion, consistent with rest of project |
| Base64 decode for PDF | Custom base64 parser | `import base64; base64.b64decode(data)` | stdlib, one line |
| ASCII encode with replace | Custom character loop | `zpl_string.encode('ascii', errors='replace')` | Python codec built-in |

**Key insight:** The entire print service is ~100-150 lines. Its complexity is entirely in the reconnect logic and error classification — both of which are solved by stdlib asyncio patterns. Nothing custom needs building.

---

## Common Pitfalls

### Pitfall 1: ServerEventManager subtopic routing
**What goes wrong:** SSE events enqueued for `"print-jobs"` don't reach the print service subscriber because the `push_events()` call uses a different topic string, or the JSON payload lacks the `subtopic` key.
**Why it happens:** `ServerEventManager.enqueue()` routes by `json.loads(message)['subtopic']`. If the payload doesn't have this key, the event is silently dropped (KeyError caught by nowhere, or routes to wrong queue).
**How to avoid:** Always enqueue with `{"subtopic": "print-jobs", ...rest of payload}` and use the exact same string `"print-jobs"` in `push_events(request, "print-jobs")`.
**Warning signs:** Print service receives no events after browser submits job; no errors in main API logs.

### Pitfall 2: asyncio event loop in gunicorn workers
**What goes wrong:** `ServerEventManager.getInstance().enqueue()` is called from a gunicorn uvicorn worker but the SSE `push_events` generator yields `await queue.get()` — if the queue was created in a different event loop (e.g., startup event), `put_nowait` may not wake the correct loop.
**Why it happens:** `asyncio.Queue` is tied to the event loop it was created on. In multi-worker gunicorn, each worker has its own loop.
**How to avoid:** The existing `ServerEventManager` is already used for notifications and appears to work under gunicorn. Use **1 worker** for the print channel feature initially (same as existing notification pattern). Document the 1-worker constraint.
**Warning signs:** SSE subscriber connects but never receives events even though enqueue is called.

### Pitfall 3: Print service loses in-flight job on reconnect
**What goes wrong:** SSE event is sent to print service, print service disconnects mid-event, job is lost silently.
**Why it happens:** SSE is fire-and-forget from the server side. Once enqueued and yielded, a disconnect drops the event.
**How to avoid:** This is accepted for v1 (CONTEXT.md: "In-flight jobs during disconnect are acceptable to lose"). Document it. Do not attempt to build a re-delivery mechanism.
**Warning signs:** N/A — by design for v1.

### Pitfall 4: Non-ASCII ZPL data
**What goes wrong:** ZPL string contains accented characters (é, ü, etc.), `.encode('ascii')` raises `UnicodeEncodeError`.
**Why it happens:** The `generateZpl()` in Phase 2 outputs ASCII-only ZPL, but Phase 4 callers send raw field values that may not be sanitised.
**How to avoid:** Use `encode('ascii', errors='replace')` as the default (`PRINT_SERVICE_NON_ASCII=replace`). When mode is `error`, catch the UnicodeEncodeError explicitly and return structured 503.
**Warning signs:** 500 errors on print jobs with non-ASCII content instead of structured 503.

### Pitfall 5: Compose file network confusion
**What goes wrong:** print.yaml declares `progress` network, which means it needs swarm-level network setup that ops may not have. Or operators expect to reference the API via internal Docker hostname.
**Why it happens:** The CONTEXT.md decision is clear: print service reaches main API via its **public URL**, not internal network. But copy-pasting warehouse.yaml/reporting.yaml (which use the progress network) as templates leads to including the network by mistake.
**How to avoid:** print.yaml must NOT declare the `progress` network. The service connects to the main API via `PRINT_SERVICE_API_URL` (e.g., `https://site.progresslab.it/api`). This is the explicit design decision.
**Warning signs:** Compose file includes `networks: progress:` — remove it.

### Pitfall 6: Authentication for the SSE subscription
**What goes wrong:** The print service needs to authenticate to the main API's SSE endpoint (`verify_token` dependency), but the print service is a non-interactive process with no user session.
**Why it happens:** All existing API endpoints use `Depends(auth.verify_token)` which validates a JWT Bearer token. The print service needs a long-lived token.
**How to avoid (Claude's discretion):** Issue a service account token at setup time (same `issue_token()` function in `utils/auth.py`), store in `PRINT_SERVICE_API_TOKEN` env var. Alternatively, add a dedicated `verify_service_token` dependency that checks a shared secret. The simplest approach: issue a non-expiring JWT for a service user account — same code path, no new mechanism.
**Warning signs:** 401 on the SSE subscription; token expiry causing reconnect failures.

---

## Code Examples

### ZPL encode with non-ASCII handling
```python
# Source: Python stdlib docs — str.encode errors parameter
def encode_zpl(zpl_string: str, mode: str = "replace") -> bytes:
    if mode == "error":
        try:
            return zpl_string.encode('ascii', errors='strict')
        except UnicodeEncodeError as e:
            raise ValueError(f"Non-ASCII character at position {e.start}: {repr(zpl_string[e.start])}")
    else:  # replace
        return zpl_string.encode('ascii', errors='replace')
```

### PDF base64 decode
```python
# Source: Python stdlib — base64
import base64

def decode_pdf(data_b64: str) -> bytes:
    return base64.b64decode(data_b64)
```

### Dockerfile for print service (client process, no port exposure)
```dockerfile
FROM python:3.11-slim

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

COPY . /app
WORKDIR /app

CMD ["python", "main.py"]
```

### deploy/compose/print.yaml (no progress network, no Traefik)
```yaml
services:
  print-service:
    image: registry.gitlab.com/progresslab/progress-platform/print-service:${VERSION}
    restart: unless-stopped
    environment:
      PRINT_SERVICE_API_URL: ${PRINT_SERVICE_API_URL}
      PRINT_SERVICE_API_TOKEN: ${PRINT_SERVICE_API_TOKEN}
      PRINT_SERVICE_NON_ASCII: ${PRINT_SERVICE_NON_ASCII:-replace}
    deploy:
      replicas: 1
      labels:
        - "traefik.enable=false"
```

### PrintJob DB record schema (Claude's discretion — recommended)
```python
# ArangoDB collection: PrintJob
{
    "_key": "auto-generated",
    "status": "pending" | "sent" | "failed",
    "printer_host": str,
    "printer_port": int,
    "format": "zpl" | "pdf",
    "copies": int,
    "timeout_seconds": float,
    "created_at": datetime ISO string,
    "completed_at": datetime ISO string | null,
    "error": str | null,
    "error_detail": str | null
}
```

### POST /api/print-jobs/{id}/result — result callback endpoint
```python
# Source: pattern from existing endpoints
@router.post("/print-jobs/{job_id}/result")
async def print_job_result(job_id: str, result: PrintJobResult):
    # Update DB record
    update = {"_key": job_id, "status": "sent" if result.ok else "failed"}
    if not result.ok:
        update["error"] = result.error
        update["error_detail"] = result.detail
    db.collection("PrintJob").update(update)
    # Notify browser via existing notification system
    NotificationManager.getInstance().notifyConflated(
        "global-notification",
        json.dumps({"subtopic": "global-notification", "notification": "REFRESH"}),
        delay=0
    )
    return {"ok": True}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Browser → print service HTTP server (original spec) | SSE-subscriber pattern (browser → main API → SSE → print service → TCP) | Phase 3 CONTEXT.md decision | Eliminates inbound port + TLS + auth on print service entirely |
| `POST /print` on print service | `POST /api/print` on main API + SSE relay | Same decision | All browser traffic stays on existing auth-protected HTTPS endpoint |
| CORS on print service | No CORS needed on print service | Same decision | SVC-03 requirement obsolete as originally written |

**Deprecated/outdated (from original requirements):**
- `PRINT_SERVICE_CORS_ORIGINS` env var: Not needed; remove from SVC-03 scope
- Port 8200 in Dockerfile: Not needed; print service exposes no inbound port
- uvicorn in print service: Not needed; plain `python main.py`

---

## Open Questions

1. **SSE channel authentication mechanism**
   - What we know: `verify_token` validates JWT Bearer tokens via the `Token` ArangoDB collection. `issue_token()` in `utils/auth.py` can create non-expiring tokens.
   - What's unclear: Whether there's a standard "service account" pattern in this project, or whether the SSE endpoint should use a shared secret env var instead of a user JWT.
   - Recommendation (Claude's discretion): Issue a non-expiring JWT for a dedicated service user (e.g., `print-service-account`) during setup. Store in `PRINT_SERVICE_API_TOKEN`. This reuses existing auth machinery with zero new code.

2. **Browser notification for print result**
   - What we know: `NotificationManager.notifyConflated()` → Kafka → `NotificationsKafkaConsumer` → `WebsocketManager.broadcast()` sends to all browser WebSocket connections.
   - What's unclear: Whether the browser should poll the print job status, receive a generic REFRESH event, or receive a targeted notification per job.
   - Recommendation: For v1, use `notifyConflated("global-notification", ...)` with `REFRESH` — same pattern as other result updates in the system. Targeted per-job notification is a v2 improvement.

3. **gunicorn worker count and asyncio Queue**
   - What we know: `ServerEventManager` queues are `asyncio.Queue` objects. With multiple gunicorn workers, each has its own asyncio loop and its own `ServerEventManager` singleton. An `enqueue()` call in worker A won't wake the queue in worker B where the SSE subscriber is connected.
   - What's unclear: Whether the existing notification SSE already constrains main API to 1 worker, or whether there's a cross-worker pub/sub mechanism (Kafka consumer already exists for notifications).
   - Recommendation: Use 1 gunicorn worker for the print feature, OR route print job SSE events through Kafka the same way notifications do (more complex but scalable). Inspect existing Kafka notification flow before planning.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | vitest (JS — `webapps/main/vitest.config.js`) |
| Config file | `webapps/main/vitest.config.js` |
| Quick run command | `cd webapps/main && yarn vitest run` |
| Full suite command | `cd webapps/main && yarn vitest run` |

No Python test framework detected in the backend (no pytest.ini, no test_*.py files outside of an ad-hoc script). Python components will need manual smoke tests.

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SVC-01 (revised) | print service GET /health returns 200 | smoke (manual) | manual — `curl http://localhost:8200/health` | ❌ Wave 0 |
| SVC-01 (revised) | print service subscribes to SSE stream on startup | smoke (manual) | manual — inspect logs | ❌ Wave 0 |
| SVC-02 (revised) | POST /api/print accepts valid payload, inserts DB record, enqueues SSE | integration (manual) | manual — `curl -X POST /api/print ...` | ❌ Wave 0 |
| SVC-02 (revised) | TCP send succeeds for ZPL format | smoke (manual) | manual — netcat listener | ❌ Wave 0 |
| SVC-02 (revised) | TCP send succeeds for PDF (base64) format | smoke (manual) | manual — netcat listener | ❌ Wave 0 |
| SVC-02 (revised) | `copies` parameter passes correctly | unit (Python) | `python -m pytest backend/print-service/test_tcp_sender.py` | ❌ Wave 0 |
| SVC-02 (revised) | Non-ASCII ZPL with replace mode produces `?` | unit (Python) | `python -m pytest backend/print-service/test_tcp_sender.py` | ❌ Wave 0 |
| SVC-02 (revised) | Non-ASCII ZPL with error mode returns 503 | unit (Python) | `python -m pytest backend/print-service/test_tcp_sender.py` | ❌ Wave 0 |
| SVC-03 (revised) | No CORS required on print service | N/A — requirement obsolete | — | — |
| SVC-04 | Dockerfile builds successfully | smoke (manual) | `docker build -t print-service backend/print-service/` | ❌ Wave 0 |
| SVC-05 | docker compose -f deploy/compose/print.yaml up starts service | smoke (manual) | `docker compose -f deploy/compose/print.yaml config` (validate syntax) | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd webapps/main && yarn vitest run` (JS only — no Python unit tests exist)
- **Per wave merge:** Full vitest suite + manual smoke of print service Docker build
- **Phase gate:** All smoke tests passing before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/print-service/test_tcp_sender.py` — unit tests for encode_zpl (ASCII modes), decode_pdf, TCP error classification
- [ ] No pytest infrastructure in backend — install: `pip install pytest pytest-asyncio` (for print service unit tests only)
- [ ] Python unit tests are isolated to print service directory, not the main API (which has no test infra)

---

## Sources

### Primary (HIGH confidence)
- `backend/api/managers/server_event_manager.py` — SSE queue structure, enqueue routing by subtopic, push_events generator
- `backend/api/managers/websocket_manager.py` — broadcast pattern for result notification
- `backend/api/managers/notification_manager.py` — Kafka-backed notification pattern
- `backend/api/endpoints/notification.py` — EventSourceResponse usage with sse_starlette
- `backend/api/utils/config.py` — pydantic-settings pattern with env_prefix
- `backend/api/utils/auth.py` — verify_token, issue_token, Bearer token mechanics
- `backend/api/requirements.txt` — confirmed: sse_starlette, httpx, pydantic 2.*, pydantic-settings 2.*
- `backend/api/Dockerfile` — python:3.11-slim base, gunicorn CMD pattern
- `deploy/compose/warehouse.yaml` + `deploy/compose/reporting.yaml` — standalone service compose patterns
- Python stdlib asyncio docs — `asyncio.open_connection`, `asyncio.wait_for`

### Secondary (MEDIUM confidence)
- httpx-sse library: standard companion to httpx for SSE consumption; widely used in Python async ecosystem

### Tertiary (LOW confidence)
- gunicorn multi-worker asyncio Queue behaviour: not verified against production config; requires investigation of existing notification Kafka flow before planning

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified against existing requirements.txt and code
- Architecture: HIGH — all patterns traced to existing code in the codebase
- Pitfalls: HIGH (SSE routing, ASCII encoding) / MEDIUM (gunicorn worker count — needs investigation)
- Deployment: HIGH — compose patterns verified against existing warehouse.yaml / reporting.yaml

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (stable domain — Python, FastAPI, asyncio, Docker Compose)
