# Architecture

**Analysis Date:** 2026-04-15

## Pattern Overview

**Overall:** Event-sourced MES (Manufacturing Execution System) with transactional event log

**Key Characteristics:**
- All business state mutations flow through typed `BaseEvent` subclasses, each executed within an ArangoDB transaction
- Events are stored immutably in an `Event` collection; parent-child relationships tracked via `event_source` edges
- NATS pub/sub handles real-time notification pipeline (replaced earlier Kafka approach for notifications)
- Dual-webapp architecture: desktop SPA (Quasar) + mobile warehouse app (Quasar + Capacitor)
- Graph database (ArangoDB) for documents + edge relationships (serial trees, BOM links, event chains)

## Layers

**Reverse Proxy / Edge:**
- Purpose: TLS termination, routing, static asset serving
- Location: `deploy/compose/tls.yaml` (Traefik v2.11), `deploy/compose/base.yaml`
- Contains: Traefik configuration, path-based routing to API and webapp containers
- Depends on: Docker networking
- Used by: All external clients

**FastAPI Application:**
- Purpose: HTTP request routing, middleware chain, SSE notification endpoint, NATS lifecycle
- Location: `backend/api/main.py`
- Contains: FastAPI app instance, CORS middleware, GZip filter middleware, NATS connection startup/shutdown, 20 domain router registrations
- Depends on: FastAPI, Starlette middleware, NATS client (`utils/nats_client.py`), `ServerEventManager`
- Used by: All HTTP clients (webapps, mobile, third-party)
- Middleware order: CORSMiddleware -> GZipFilterMiddleware (excludes `/notification`)

**Endpoints (Route Handlers):**
- Purpose: Receive HTTP requests, validate input, instantiate domain events or execute queries
- Location: `backend/api/endpoints/*.py` (20 modules)
- Contains: FastAPI route handlers with Pydantic request models and JWT auth dependencies
- Depends on: Event classes, utility query modules, Pydantic models, `utils.auth`
- Used by: HTTP clients via routers registered in `main.py`
- Key files by size/complexity:
  - `backend/api/endpoints/production.py` (26KB) -- work orders, jobs, batches, steps
  - `backend/api/endpoints/counting.py` (20KB) -- inventory counting sessions
  - `backend/api/endpoints/product.py` (15KB) -- product/BOM management
  - `backend/api/endpoints/serial.py` (13KB) -- serial number management
  - `backend/api/endpoints/inventory.py` (13KB) -- warehouse movements
  - `backend/api/endpoints/traceability.py` (12KB) -- DHR, traceability queries
  - `backend/api/endpoints/collaboration.py` (10KB) -- issues, messages, tasks
  - `backend/api/endpoints/process.py` (21KB) -- process definition management
  - `backend/api/endpoints/auth.py` (8KB) -- login, session management
  - `backend/api/endpoints/print.py` (7KB) -- print template management

**Events (Domain State Mutations):**
- Purpose: Execute atomic, immutable business logic within ArangoDB transactions
- Location: `backend/api/events/base_event.py` (abstract base), `backend/api/events/` (domain subdirs)
- Contains: `BaseEvent` ABC and 60+ concrete event classes organized by domain
- Depends on: Pydantic models (`EventInfoModel`), ArangoDB transaction API, NATS publisher
- Used by: Endpoints instantiate events; events can spawn child events via `create_as_child()`
- Domains:
  - `events/production/` (16 files) -- StepCompleted, BatchCompleted, JobStarted, JobClosed, JobPaused, etc.
  - `events/inventory/` (23 files) -- MovementCompleted, CountSessionApplied, WarehouseListCreated, etc.
  - `events/serial/` (8 files) -- SerialCreated, SerialLinked, SerialUpdated, etc.
  - `events/collaboration/` (17 files) -- IssueCreated, TaskCompleted, MessagePosted, etc.
  - `events/wip/` (4 files) -- WIPBooked, WIPDeclared, WIPRemoved, WIPUnbooked
  - `events/work_session/` (3 files) -- WorkSessionCreated, WorkSessionClosed, WorkSessionCanceled
  - `events/admin/` (6 files) -- JobReset, ProgressOverrideRequested, BatchCanceled, etc.

**Managers (Singletons / Side-Effect Handlers):**
- Purpose: Handle cross-cutting runtime concerns (SSE push, notification routing)
- Location: `backend/api/managers/`
- Contains:
  - `server_event_manager.py` -- Singleton SSE fan-out manager with per-topic/per-client async queues; supports wildcard subscriptions (`{prefix}:*`)
- Depends on: asyncio, NATS messages routed from `main.py` startup subscriber
- Used by: SSE notification endpoint (`endpoints/notification.py`)

**Models (Data Validation):**
- Purpose: Pydantic models for request/response validation and ArangoDB document structure
- Location: `backend/api/models/*.py` (20 files)
- Contains: Domain models with ArangoDB field aliases (`_id`, `_key`, `_rev`, `_from`, `_to`)
- Key files:
  - `backend/api/models/event.py` -- `EventType` enum (100+ types), `EventInfoModel`, `EventModel`, `BulkEventRequest`
  - `backend/api/models/production.py` -- Job, Batch, WorkOrder, StepExecutionData models
  - `backend/api/models/collaboration.py` -- Issue, Task, Message models
  - `backend/api/models/serial.py` -- Serial number and link models
  - `backend/api/models/print.py` -- Print template models
  - `backend/api/models/base_models.py` -- Shared base model definitions
  - `backend/api/models/inventory/` -- Inventory-specific models (subdirectory)

**Utilities (Shared Logic):**
- Purpose: Query builders, helper functions, cross-cutting infrastructure
- Location: `backend/api/utils/` (~28 files)
- Key files:
  - `backend/api/utils/db.py` -- ArangoDB client singleton (`db` global instance)
  - `backend/api/utils/config.py` -- `Settings` via pydantic-settings, env prefix `PROGRESS_`
  - `backend/api/utils/auth.py` (13KB) -- JWT verification, user resolution, token management
  - `backend/api/utils/nats_client.py` -- NATS connection, publish/subscribe, sync-to-async bridge
  - `backend/api/utils/production.py` (20KB) -- AQL queries for jobs, batches, work orders
  - `backend/api/utils/inventory.py` (20KB) -- AQL queries for positions, movements
  - `backend/api/utils/serial.py` (14KB) -- AQL queries for serial management
  - `backend/api/utils/dhr.py` (44KB) -- Device History Record generation (largest single file)
  - `backend/api/utils/traceability.py` (12KB) -- Traceability queries and progress updates
  - `backend/api/utils/counter.py` -- Auto-incrementing counter generation
  - `backend/api/utils/collaboration.py` (12KB) -- Issue/task/message queries
  - `backend/api/utils/process.py` -- Process definition queries
  - `backend/api/utils/event.py` -- Event class registry and lookup (`register_event_class`, `get_event_class`)
  - `backend/api/utils/nats_client.py` -- NATS connection lifecycle + sync publish bridge

**Middleware:**
- Purpose: Cross-cutting request/response handling
- Location: `backend/api/middlewares/`
- Contains:
  - `gzipfilter_middleware.py` -- Conditional GZip compression, excludes SSE notification endpoint
- Note: Only one custom middleware active. CORS handled by Starlette's built-in middleware.

**Workflow Engine:**
- Purpose: Scheduled/automated background jobs via Prefect 3.x
- Location: `backend/workflow/`
- Contains: Prefect flows for batch operations
- Key flows:
  - `backend/workflow/flows/flowcode/apply_inventory_counts.py` -- Apply count session results
  - `backend/workflow/flows/flowcode/cleanup_disposable_positions.py` -- Clean temp positions
  - `backend/workflow/flows/flowcode/pause_offline_jobs.py` -- Auto-pause stale jobs
- Depends on: `python-arango` (direct DB access), `httpx` (API calls)
- Deployed as: Separate container with Prefect server + PostgreSQL (`deploy/compose/workflow.yaml`)

## Data Flow

**Production Event Chain (Critical Path):**

1. Operator completes a step on frontend -> POST to `endpoints/production.py`
2. Endpoint validates input, creates `StepCompletedEvent(info=..., tx=None)`
3. `BaseEvent.save()` begins ArangoDB transaction (event owns the tx since `tx=None`)
4. `StepCompletedEvent.apply()` updates `StepExecutionData` collection
5. If last step in batch: spawns `BatchCompletedEvent` as child via `create_as_child()` (shares same tx)
6. `BatchCompletedEvent.apply()` updates Batch status, may cascade to `JobClosedEvent`
7. Each event stored in `Event` collection; parent-child edge in `event_source`
8. Transaction commits atomically (all-or-nothing)
9. Collected NATS payloads published after commit via `_publish_collected_events()`
10. `main.py` NATS subscriber receives on `progress.notification.>` wildcard
11. `ServerEventManager.enqueue()` fans out to per-topic SSE queues
12. Frontend `useSSE` composable receives event, triggers UI update

**Real-Time Notification Flow:**

1. Event completes -> `_build_event_payload()` creates notification dict with subtopic
2. Payload appended to `tx._pending_events` list (deferred until commit)
3. After transaction commit -> `_publish_collected_events()` publishes each to NATS
4. `main.py` startup subscriber receives on `progress.notification.>` wildcard
5. `ServerEventManager.enqueue()` routes message to per-topic async queues
6. Supports exact-topic delivery and wildcard fan-out (`production:*` receives all `production:{x}` events)
7. SSE endpoint (`GET /notification/{topic}`) streams events via `push_events()` async generator
8. Frontend `useSSE` composable (`webapps/main/src/composables/useSSE.js`) manages shared `EventSource` connections (ref-counted across components)

**Event Transaction Lifecycle:**

```
BaseEvent.__init__() -> validate InfoModel
BaseEvent.save():
  1. begin_transaction() if _owns_transaction
  2. pre_processing()
  3. apply()             <- domain logic, DB mutations
  4. post_processing()
  5. store_event()       <- write to Event collection
  6. _build_event_payload() -> append to tx._pending_events
  7. commit_transaction() if _owns_transaction
  8. _publish_collected_events() -> NATS
  finally: abort if tx still running
```

**Child Event Spawning:**

- `BaseEvent.create_as_child(parent_event, new_event_data)` shares parent's transaction
- Creates `event_source` edge immediately (both events have UUID keys)
- Child's `save()` does NOT commit (it doesn't own the tx)
- Example: `StepCompletedEvent` -> `BatchCompletedEvent` -> `JobClosedEvent` (cascading chain)

**Bulk Event Creation:**

- `BaseEvent.spawn_multiple(shared_data, event_data_list)` creates multiple events of the same type in one transaction
- All events share the same `event_group` UUID
- Used for batch operations (e.g., multiple serial creations)

**API Request Authentication:**

1. Client sends JWT in `Authorization: Bearer <token>` header
2. `utils.auth.verify_token` FastAPI dependency validates token
3. User claims extracted from token for downstream use
4. Axios interceptor on frontend attaches token from Vuex session store
5. 401 responses trigger auto-logout via Axios response interceptor (`boot/axios.js`)

## Key Abstractions

**BaseEvent:**
- Purpose: Abstract base for all domain events; manages transaction lifecycle, event storage, NATS publishing
- Location: `backend/api/events/base_event.py`
- Pattern: Template Method -- subclasses implement `get_event_type()`, `get_tx_collections()`, `apply()`, optionally `pre_processing()` / `post_processing()`
- Transaction ownership: If created without a `tx`, the event owns the transaction (begins + commits). Child events share the parent's transaction.
- Key methods:
  - `save()` -- Full lifecycle: begin tx -> pre -> apply -> post -> store -> commit
  - `create_as_child()` -- Spawn child event sharing parent tx
  - `spawn_multiple()` -- Create N events of same type in one tx
  - `_build_event_payload()` -- Build NATS notification (overridable)

**EventInfoModel:**
- Purpose: Base Pydantic model for all event data; carries metadata
- Location: `backend/api/models/event.py`
- Fields: `event_type`, `event_group`, `primary`, `user_key`, `user_session_key`, `timestamp`, `context_type`, `context_key`, `description`
- Pattern: Each event subclass defines an inner `InfoModel(EventInfoModel)` with domain-specific fields
- Extra fields: `ConfigDict(extra='allow')` lets parent event data flow through; `exclude_extra=True` strips it on save

**EventType Enum:**
- Purpose: Centralized registry of all event types (100+ members)
- Location: `backend/api/models/event.py`
- Categories: Production (10), Collaboration (16), Admin (8), Serial (8), Inventory (14), Counting (10), WorkOrder (4), WorkSession (4), WIP (4), Queue (1)

**Event Registration:**
- Purpose: Runtime registry mapping `EventType` -> event class
- Location: `backend/api/events/__init__.py` (auto-registers all event classes on module import via loop)
- Lookup: `backend/api/utils/event.py` provides `get_event_class(event_type)` and `register_event_class()`

**ServerEventManager:**
- Purpose: Singleton SSE fan-out with per-topic, per-client async queues
- Location: `backend/api/managers/server_event_manager.py`
- Pattern: Singleton via `getInstance()`; one instance for app lifetime
- Queue structure: `{topic: {request_id: asyncio.Queue}}`
- Wildcard support: `{prefix}:*` subscriptions receive all `{prefix}:{x}` events
- SSE delivery: `push_events()` async generator with 14-second heartbeat timeout

**NATS Client:**
- Purpose: Message bus for decoupling event commits from client notifications
- Location: `backend/api/utils/nats_client.py`
- Subject mapping: `progress.notification.{inventory|serial|task|production|message}`
- Sync bridge: `publish_sync()` uses `run_coroutine_threadsafe` to publish from synchronous event code
- Lifecycle: Connected in `main.py` startup, drained in shutdown

## Entry Points

**FastAPI Application:**
- Location: `backend/api/main.py`
- Triggers: HTTP requests from webapps/clients
- Routers (20): admin, auth, bom, config, file, form, serial, media, org, print, process, product, production, tag, collaboration, traceability, counter, notification, inventory, counting
- Startup: Connects to NATS, subscribes to `progress.notification.>`, routes to `ServerEventManager`
- Shutdown: Closes `ServerEventManager`, drains NATS connection
- Health check: `GET /hello` (no auth)

**SSE Notification Endpoint:**
- Location: `backend/api/endpoints/notification.py`
- Route: `GET /notification/{topic}`
- Response: `EventSourceResponse` (SSE stream)
- Triggers: Frontend `EventSource` connections via `useSSE` composable

**Prefect Workflow Flows:**
- Location: `backend/workflow/flows/flowcode/*.py`
- Triggers: Scheduled by Prefect server
- Direct DB access via `python-arango` (not through API events)

**Frontend App Entry:**
- Main app: `webapps/main/src/App.vue`
- Boot sequence (`webapps/main/src/boot/`): axios -> store (Vuex) -> pinia -> i18n -> theme -> filters -> registerRouter
- Router: `webapps/main/src/router/routes.js` -> `MainLayout.vue` wraps all `/app/*` routes
- Warehouse app: `webapps/warehouse/src/App.vue` (separate Quasar + Capacitor app)

## Error Handling

**Strategy:** Mixed -- events use transaction rollback, endpoints use HTTP exceptions

**Patterns:**
- **Transaction safety:** `BaseEvent.save()` uses `try/finally` -- if exception occurs and transaction is still `running`, it aborts automatically
- **NATS publish failures:** Non-blocking (logged via `logger.exception`, not raised) -- event data is committed regardless
- **Endpoint validation:** Pydantic models validate request bodies; `HTTPException` raised for business rule violations
- **Legacy pattern:** Many endpoints use bare `except:` with `traceback.format_exc()` in response body (technical debt, see `endpoints/production.py`)
- **Child event failures:** Propagate up and abort the parent transaction (same ArangoDB tx)
- **Custom exceptions:** `backend/api/utils/exceptions.py` defines `HTTPError` for structured error responses

## Cross-Cutting Concerns

**Authentication:**
- JWT tokens in `Authorization` header
- `utils.auth.verify_token` as FastAPI `Depends()` on protected routes
- `/hello` endpoint is public (health check)
- Frontend stores token in Vuex session store; Axios interceptor attaches it (`boot/axios.js`)
- 401 responses trigger auto-logout

**Validation:**
- Request level: Pydantic models in endpoint function signatures
- Event level: `InfoModel` (inheriting `EventInfoModel`) validates event-specific data in `__init__`
- Business level: Endpoint code checks preconditions before creating events

**Real-Time Updates:**
- NATS pub/sub as message bus between event commits and SSE push
- Topics: `inventory`, `serial`, `task`, `production`, `message`
- Frontend: `useSSE` composable (`webapps/main/src/composables/useSSE.js`) -- shared ref-counted `EventSource` per topic
- Wildcard: `ServerEventManager` supports `{prefix}:*` subscriptions for grouped topics

**Database Access:**
- Global singleton: `utils.db.db` (ArangoDB `StandardDatabase` instance)
- Transaction API: Events use `db.begin_transaction(write=[...])` for atomic mutations
- AQL queries: Stored as constants in domain utility modules (e.g., `utils.production.Queries`)
- No ORM -- direct ArangoDB document operations via `python-arango`

**Configuration:**
- Backend: `pydantic-settings` with `PROGRESS_` env prefix, Docker secrets at `/run/secrets`
- Frontend: `window.API_CONFIG` object injected from `deploy/config/appConfig.js`
- Local dev: Falls back to `http://0.0.0.0:8000` for API base URL

**State Management (Frontend):**
- **Vuex** (`webapps/main/src/store/`): 13 modules -- session, product, process, job, bom, form, org, quality, serial, traceability, warehouse, user, workorder
- **Pinia** (`webapps/main/src/stores/`): 4 stores -- config, countSession, task, taskType (newer additions)
- Session persistence: Vuex state saved to localStorage on tab close, restored within 5-minute window with session lock

---

*Architecture analysis: 2026-04-15*
