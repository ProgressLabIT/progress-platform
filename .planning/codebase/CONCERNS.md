# Codebase Concerns

**Analysis Date:** 2026-04-15

## Critical

### Stacktrace Leakage to API Clients

- Issue: Full Python tracebacks are returned to API clients via `HTTPException(detail=traceback.format_exc())`. This exposes internal file paths, library versions, database schema details, and code structure to anyone who triggers an error.
- Files: 106 occurrences across all 16 endpoint files. Worst offenders:
  - `backend/api/endpoints/inventory.py` (13 occurrences)
  - `backend/api/endpoints/production.py` (12 occurrences)
  - `backend/api/endpoints/counting.py` (11 occurrences)
  - `backend/api/endpoints/product.py` (9 occurrences)
  - `backend/api/endpoints/process.py` (8 occurrences)
- Impact: **Security vulnerability**. Attackers can map internal architecture, identify library versions with known CVEs, and discover database collection names. Also leaks `stacktrace=traceback.format_exc()` in `backend/api/utils/auth.py:46` and `:387`, exposing auth internals.
- Fix approach: Log the traceback server-side using `logger.exception()`, return a generic error message to the client. Create a centralized error handler via FastAPI exception handlers.

### Unauthenticated Endpoints

- Issue: Multiple endpoints have no authentication at all.
- Files:
  - `backend/api/endpoints/file.py:103` - `POST /files` (file upload) - **no auth dependency**
  - `backend/api/endpoints/file.py:136` - `DELETE /files` (file deletion) - **no auth dependency**
  - `backend/api/endpoints/notification.py:8` - `GET /notification/{topic}` (SSE stream) - **no auth dependency**
  - `backend/api/endpoints/config.py:15` - `GET /config` (system configuration) - **no auth dependency**
- Impact: Anyone with network access can upload arbitrary files, delete files, stream all notifications (potentially containing business data), and read system configuration. File upload without auth is a particularly serious vector for attacks.
- Fix approach: Add `dependencies=[Depends(auth.verify_token)]` to all these endpoints. For SSE, consider token-based auth via query parameter since EventSource API does not support headers natively.

### Empty JWT Secret Default

- Issue: `jwt_secret` defaults to an empty string `""` in `backend/api/utils/config.py:14`. If the secret is not configured via environment or Docker secrets, JWTs are signed with an empty key, making them trivially forgeable.
- Files: `backend/api/utils/config.py:14`
- Impact: Complete authentication bypass if deployment misconfigures secrets.
- Fix approach: Add a startup check that raises an error if `jwt_secret` is empty. Alternatively, use a pydantic validator to enforce a minimum length.

### Uninitialized Variable Bug in Admin Endpoint

- Issue: `reset_warehouse_data()` references `tx.abort_transaction()` in its `except` block, but `tx` is never defined in this function. The function uses `db.collection().truncate()` directly without a transaction.
- Files: `backend/api/endpoints/admin.py:83-101` (line 97: `tx.abort_transaction()`)
- Impact: If any error occurs during warehouse reset, a `NameError: name 'tx' is not defined` will be raised instead of the actual error, masking the real problem and returning an unhelpful 500.
- Fix approach: Either wrap the operations in a transaction and define `tx`, or remove the `tx.abort_transaction()` call from the except block.

---

## High

### Pervasive Bare `except:` Clauses

- Issue: 74 bare `except:` clauses (no exception type specified) across the backend. These catch **everything** including `SystemExit`, `KeyboardInterrupt`, and `GeneratorExit`, preventing clean shutdowns and masking programming errors.
- Files: Highest density in:
  - `backend/api/endpoints/counting.py` (8 bare excepts)
  - `backend/api/endpoints/product.py` (6 bare excepts)
  - `backend/api/endpoints/org.py` (6 bare excepts)
  - `backend/api/endpoints/process.py` (5 bare excepts)
  - `backend/api/endpoints/production.py` (5 bare excepts)
  - `backend/api/utils/auth.py:258,263,268,314` (4 bare excepts in token verification)
  - `backend/api/endpoints/counter.py` (4 bare excepts in 62 lines)
- Impact: Silent error swallowing, inability to distinguish between expected and unexpected failures. Errors in authentication code are silently caught and re-raised as generic credential failures, hiding root causes.
- Fix approach: Replace `except:` with `except Exception:` at minimum, and ideally catch specific exception types. In auth code, catch `jwt.ExpiredSignatureError`, `jwt.InvalidSignatureError`, `DocumentGetError` etc. separately.

### Debug `print()` Statements in Production Code

- Issue: 65 `print()` calls across 16 files, including 42 in `backend/api/utils/dhr.py` alone. Auth code at `backend/api/utils/auth.py` uses `print()` for error reporting (lines 251, 255, 269, 273, 277, 281).
- Files:
  - `backend/api/utils/dhr.py` - 42 print statements (many with DEBUG emoji prefix)
  - `backend/api/utils/auth.py` - 7 print statements in security-critical token verification
  - `backend/api/endpoints/traceability.py` - 3 print statements
  - `backend/api/events/serial/*.py` - 5 print statements using `traceback.format_exc()`
  - `backend/api/utils/file.py:87` - prints on every file save
- Impact: Logging goes to stdout instead of structured logging. Security-sensitive information (token errors) logged without structure. DHR debug prints pollute production logs. Only 7 files actually use the `logging` module properly (17 total `logger.*` calls vs 65 `print()` calls).
- Fix approach: Replace all `print()` with `logger.debug()` / `logger.error()` / `logger.exception()`. Remove or gate DHR debug prints behind a log level.

### CORS Wildcard Default with Credentials

- Issue: Default CORS configuration allows all origins (`["*"]`) combined with `allow_credentials=True` and `allow_methods=["*"]`.
- Files: `backend/api/utils/config.py:15`, `backend/api/main.py:22-29`
- Impact: Enables cross-site attacks if production deployment does not override the default. Browsers may block this combination, but the intent indicates a misconfiguration risk.
- Fix approach: Remove the wildcard default. Require explicit origin configuration in production. Add a startup warning if wildcard origins are used with credentials.

### No Rate Limiting on Auth Endpoints

- Issue: No rate limiting or brute-force protection exists anywhere in the codebase.
- Files: `backend/api/endpoints/auth.py` (login endpoint), `backend/api/main.py` (no rate limit middleware)
- Impact: Authentication endpoints are vulnerable to brute-force attacks. Password verification at `backend/api/endpoints/auth.py:127-137` can be called unlimited times.
- Fix approach: Add rate limiting middleware (e.g., `slowapi`) or implement at the Traefik reverse proxy level.

### No Path Traversal Protection on File Upload

- Issue: `FileHandler` at `backend/api/utils/file.py` uses `file.filename` directly in `os.path.join()` without sanitizing for path traversal characters. Only `backend/api/endpoints/serial.py:24-35` implements `sanitize_filename()` -- this is not used elsewhere.
- Files:
  - `backend/api/utils/file.py:73,81` - uses `file.filename` directly
  - `backend/api/endpoints/media.py:35` - `path.join(media_root_path, media_key)` uses user-supplied key
  - `backend/api/endpoints/counting.py:430` - `os.path.join(import_dir, new_file_key)`
- Impact: A crafted filename like `../../../etc/cron.d/exploit` could write files outside the media directory. Partially mitigated by Docker containerization, but still a risk within the container filesystem.
- Fix approach: Apply `sanitize_filename()` (from `backend/api/endpoints/serial.py`) globally in `FileHandler.write_file()`. Validate that resolved paths stay within `media_root_path` using `os.path.realpath()`.

---

## Medium

### Vuex-to-Pinia Migration Incomplete

- Issue: The codebase has a dual state management system. Legacy Vuex store has 15 modules. New Pinia stores have only 4 modules. 79 files import from Vuex (`store/`) while 46 files import from Pinia (`stores/`).
- Files:
  - Legacy Vuex: `webapps/main/src/store/` - 15 files: `traceability.js` (533 lines), `product.js` (422 lines), `warehouse.js` (370 lines), `process.js` (277 lines), `session.js` (214 lines), and 10 more
  - New Pinia: `webapps/main/src/stores/` - 4 files: `config.js`, `countSession.js`, `task.js`, `taskType.js`
- Impact: Developers must understand two different state management patterns. State may be split across systems for related features. Increases onboarding cost and bug surface.
- Fix approach: Incrementally migrate Vuex modules to Pinia, starting with smaller ones (`bom.js` 835B, `form.js` 836B, `org.js` 1.2K). The `traceability.js` and `product.js` modules should be migrated last.

### Options API vs Composition API Split (50/50)

- Issue: ~100 Vue components use Options API (`export default {`), while ~101 use `<script setup>` Composition API. Nearly a perfect 50/50 split.
- Files: All `.vue` files in `webapps/main/src/views/` and `webapps/main/src/components/`
- Impact: Inconsistent patterns across the codebase. New developers must understand both APIs. Components cannot easily share logic between the two styles.
- Fix approach: Convert Options API components to `<script setup>` when modifying them. Do not bulk-refactor. Priority: components that interact with Pinia stores should be converted first.

### Deprecated Pydantic v1 API Usage

- Issue: 10 files still use `.dict()` (Pydantic v1 API) instead of `.model_dump()` (Pydantic v2). The codebase depends on `pydantic==2.*`.
- Files:
  - `backend/api/endpoints/media.py` (2 calls)
  - `backend/api/endpoints/counter.py`, `print.py`, `form.py`, `collaboration.py` (1 each)
  - `backend/api/events/admin/time_override_requested.py`, `events/collaboration/issue_created.py`
  - `backend/api/utils/auth.py`, `utils/print.py`
- Impact: `.dict()` is deprecated in Pydantic v2 and will be removed in v3. Emits deprecation warnings at runtime.
- Fix approach: Replace `.dict()` with `.model_dump()` and `.dict(by_alias=True)` with `.model_dump(by_alias=True)`.

### Wildcard Imports Throughout Backend

- Issue: 28+ files use `from models.* import *` or `from utils.* import *` wildcard imports.
- Files: Prevalent in:
  - `backend/api/endpoints/inventory.py:6`, `production.py:10`, `product.py:10,16`, `process.py:11,17`
  - `backend/api/events/production/*.py` (5 files import `from models.traceability import *`)
  - `backend/api/utils/auth.py:12,16`
- Impact: Namespace pollution, impossible to trace where symbols come from, hides unused imports from linters, can cause subtle bugs when modules export conflicting names.
- Fix approach: Replace with explicit imports. Use IDE refactoring tools to identify which names are actually used.

### Large Files Indicating Excessive Complexity

- Issue: Several files are excessively large, suggesting they need decomposition.
- Files:
  - `backend/api/utils/dhr.py` - 1,307 lines (PDF generation utility, mixed concerns)
  - `backend/api/endpoints/production.py` - 874 lines (17 endpoint functions)
  - `backend/api/endpoints/process.py` - 713 lines
  - `backend/api/events/admin/progress_override_requested.py` - 681 lines (single event class)
  - `backend/api/events/inventory/count_imported.py` - 636 lines (single event class)
  - `webapps/main/src/views/TaskScreen.vue` - 1,169 lines
  - `webapps/main/src/views/ProductHome.vue` - 1,007 lines
  - `webapps/main/src/views/TaskOverview.vue` - 894 lines
- Impact: Hard to review, test, and maintain. High merge conflict probability.
- Fix approach: Extract logical sections from endpoint files into domain-specific utilities. Split large Vue components into smaller composables and child components.

### Inconsistent Transaction Handling in Endpoints

- Issue: Many endpoints manually manage transactions with inconsistent patterns. Some abort in `except`, some in `finally`, some forget to abort entirely.
- Files:
  - `backend/api/endpoints/production.py:40-165` - manual `try/except/tx.abort` repeated 4 times for a single endpoint (`create_work_order`)
  - `backend/api/endpoints/production.py:848-850` - uses `finally` for abort (correct pattern)
  - `backend/api/endpoints/counting.py:42-81` - abort in bare `except:`
  - `backend/api/endpoints/admin.py:97` - references undefined `tx` (see Critical section)
- Impact: Transaction leaks if abort is missed. Inconsistent patterns make code review unreliable. The event system at `backend/api/events/base_event.py:223-270` has proper finally-based transaction handling -- endpoints should follow this pattern.
- Fix approach: Create a transaction context manager. Adopt the `finally`-based pattern from `base_event.py` consistently.

### TODOs Indicating Incomplete Features

- Issue: 30+ TODO comments in backend, 30+ in frontend, indicating incomplete implementations and known shortcuts.
- Files (high-impact TODOs):
  - `backend/api/events/inventory/movement_completed.py:154` - "handle serial creation if product requires it" (data integrity gap)
  - `backend/api/endpoints/product.py:305` - "Verify if there's any workorder or active item related" (unsafe deletion)
  - `backend/api/models/event.py:101` - `WORK_ORDER_CANCELED` event type defined but no endpoint exists
  - `backend/api/events/admin/progress_override_requested.py:365` - "refactor to avoid code duplication"
  - `webapps/main/src/views/TaskScreen.vue:1063` - "Implement the actual API call to link the entity"
  - `webapps/main/src/views/ProductionProcess.vue:456` - "Migrate process to new media structure"
- Impact: Feature gaps in serial traceability, product deletion safety, and task entity linking.

---

## Low

### Loose Dependency Pinning

- Issue: Many dependencies use wildcard minor/major version pins (`==0.*`, `==2.*`, `>=0.11`).
- Files: `backend/api/requirements.txt`
  - `fastapi==0.*` - any 0.x version (significant API changes between 0.x releases)
  - `starlette>=0.13` - allows any version from 0.13 onwards
  - `uvicorn>=0.11` - very loose
  - `cryptography==41.0.*` - pinned to 41.0.x (current is 44.x, missing security fixes)
  - `click==7.1.*` - very old (current is 8.x)
  - `passlib==1.7.2` - exact pin, last release 2022, project appears abandoned
  - `six==1.15.0` - Python 2/3 compat library, unnecessary for Python 3.11-only project
- Impact: Builds may pull in incompatible versions. `cryptography==41.0.*` is likely missing security patches. `passlib` has no active maintainer for critical security functionality.
- Fix approach: Pin exact versions via a lockfile. Evaluate replacing `passlib` with direct `bcrypt` usage. Remove `six`. Update `cryptography` to latest.

### Synchronous DB Calls in Async Endpoints

- Issue: Endpoints are defined as `async def` but use synchronous `python-arango` calls (`db.aql.execute()`, `db.collection().get()`). This blocks the event loop.
- Files: All endpoint files. For example:
  - `backend/api/endpoints/production.py` - 24 `db.aql.execute()` calls in `async def` functions
  - `backend/api/endpoints/inventory.py` - 9 calls
- Impact: Under concurrent load, blocked async endpoints will queue behind synchronous DB calls, reducing throughput. FastAPI uses a threadpool for `def` (non-async) endpoints, which would actually handle this better.
- Fix approach: Either change `async def` to `def` for DB-heavy endpoints (FastAPI runs them in a threadpool automatically), or migrate to an async ArangoDB client.

### Orphaned Media Files

- Issue: Media uploads at `backend/api/endpoints/media.py:42` create files on disk before linking them to entities. The TODO at line 41 acknowledges this: "If a created media is not connected to any entity in a reasonable amount of time, delete it."
- Files: `backend/api/endpoints/media.py:41-54`
- Impact: Disk space leak over time as orphaned files accumulate.
- Fix approach: Implement a cleanup job (cron or Prefect task) that removes Media records and files not linked via `media_connection` edges after a configurable timeout.

### Deprecated FastAPI Lifecycle Events

- Issue: `@app.on_event("startup")` and `@app.on_event("shutdown")` are deprecated in modern FastAPI in favor of lifespan context managers.
- Files: `backend/api/main.py:43-57`
- Impact: Will generate deprecation warnings and eventually break in future FastAPI versions.
- Fix approach: Migrate to FastAPI's lifespan context manager pattern.

### Dead/Unused Components

- Issue: Several components and code paths appear unused based on TODO comments.
- Files:
  - `webapps/main/src/components/BaseAvatarListElement.vue` - "only used within PhaseAssignments.vue which is not used anywhere"
  - `webapps/main/src/components/ProductAside.vue` - "Migrate to Quasar if the component will end up being used"
  - `webapps/main/src/views/SessionLock.vue` - "Migrate to Quasar if the component will end up being used"
  - `backend/api/models/process.py:90` - "this is not used anywhere, consider removing"
- Impact: Dead code increases maintenance burden and confusion.
- Fix approach: Verify usage and remove confirmed dead components.

---

## Summary by Area

| Area | Critical | High | Medium | Low |
|------|----------|------|--------|-----|
| Security | 3 | 3 | 0 | 1 |
| Error Handling | 1 | 2 | 1 | 0 |
| Code Quality | 0 | 0 | 4 | 0 |
| Architecture | 0 | 0 | 2 | 2 |
| Frontend | 0 | 0 | 2 | 1 |
| Dependencies | 0 | 0 | 1 | 1 |

---

*Concerns audit: 2026-04-15*
