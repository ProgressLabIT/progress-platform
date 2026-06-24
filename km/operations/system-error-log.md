# System Error Log (5xx persistence)

Server-side HTTP failures (5xx) are persisted to ArangoDB so a 500 can be inspected after the fact — endpoint, redacted payload, error, and traceback — without grepping container logs. Implemented in [`backend/api/utils/error_log.py`](../../backend/api/utils/error_log.py).

## What gets captured

Two FastAPI exception handlers, registered in `backend/api/main.py`, cover both failure patterns in this codebase:

| Handler | Catches | Behaviour |
|---|---|---|
| `http_exception_handler` | `StarletteHTTPException` (FastAPI `HTTPException` + the codebase's `HTTPError`) | Records only when `status_code >= 500`, then defers to FastAPI's default response. 4xx are **not** logged. |
| `unhandled_exception_handler` | any uncaught `Exception` | Records, then returns an opaque `500 {"detail": "Internal Server Error"}` — the traceback is stored, never returned to the client. |

Logging is **best-effort**: every persistence path is guarded, so an insert failure only warns (logger `error_log`) and never breaks the request.

## Where it lives

- **Collection:** `ErrorLog`
- **Retention:** 30 days, via a TTL index `errorlog-ttl` on the numeric `ts` field (`expireAfter = 2592000`). The index is created two ways (both idempotent): `db_init.py` on fresh provisioning, and `error_log.ensure_collection()` on every API startup (covers DBs created before the collection existed).

Each document:

| Field | Notes |
|---|---|
| `endpoint`, `method` | request path + verb |
| `query` | query params, **redacted** |
| `payload` | request JSON body, **redacted**; `null` for non-JSON, multipart, unparsed, or bodies > 64 KB |
| `user_key` | best-effort `sub` from the Bearer token (decoded **without** expiry/DB check); `null` if absent |
| `status_code`, `error`, `traceback` | |
| `timestamp` | ISO-8601, human-readable |
| `ts` | epoch seconds — the TTL index field |

### Redaction

Values under these keys (case-insensitive, recursive) are replaced with `***REDACTED***` before storage: `password` (+ `old_/new_/current_`), `token`, `access_token`, `refresh_token`, `secret`, `jwt`, `authorization`, `cookie`, `signature`. Applies to both query params and JSON body.

## How to inspect

Open the ArangoDB web UI (or `arangosh`) against the API's database and query `ErrorLog`. Most-recent first:

```aql
FOR e IN ErrorLog SORT e.ts DESC LIMIT 50 RETURN e
```

Filter to one endpoint, last 24 h:

```aql
FOR e IN ErrorLog
  FILTER e.endpoint == "/production/work-order" AND e.ts > DATE_NOW()/1000 - 86400
  SORT e.ts DESC
  RETURN { e.timestamp, e.status_code, e.error, e.user_key }
```

## Verifying it works

`backend/api/main.py` exposes a test route that raises `HTTPException(500, "manual test boom")` — hit it and confirm a row lands in `ErrorLog`. Remove/guard that route before it matters in production.

## Operational notes

- The collection grows with your 5xx rate; the TTL index keeps it bounded at ~30 days. No manual pruning needed.
- A spike in `ErrorLog` inserts is a leading signal of a regression — worth a glance after each deploy.
- Tracebacks may contain internal detail; the collection inherits ArangoDB's access controls. Treat it as operator-only.
