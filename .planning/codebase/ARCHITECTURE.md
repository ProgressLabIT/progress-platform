<!-- refreshed: 2026-05-08 -->
# Architecture

**Analysis Date:** 2026-05-08

## System Overview

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                        HTTP / WebSocket Clients                          │
│         Main SPA (Vue3/Quasar)  │  Warehouse Mobile (Quasar+Capacitor)   │
└────────────────────────────┬────────────────────────┬────────────────────┘
                             │                        │
           ┌─────────────────┴────────────────────────┴──────────────────┐
           │                  Traefik Reverse Proxy                       │
           │              `deploy/compose/base.yaml`                      │
           └──────────────────┬──────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────────┬────────────────┐
        │                     │                         │                │
        ▼                     ▼                         ▼                ▼
    ┌────────────────┐  ┌──────────────┐      ┌─────────────┐    ┌──────────────┐
    │  FastAPI API   │  │ Sparkplug    │      │  Prefect    │    │  Reporting   │
    │  Server        │  │  Bridge      │      │  Server     │    │  (Streamlit) │
    │ backend/api/   │  │ backend/     │      │ backend/    │    │ deploy/      │
    │ main.py        │  │ sparkplug_   │      │ workflow/   │    │ scripts/     │
    │ (8000)         │  │ bridge/main  │      │ (3000)      │    │ (:8501)      │
    └────┬───────────┘  │ .py          │      └─────────────┘    └──────────────┘
         │              │ (MQTT→NATS)  │
         │              └──────┬───────┘
         │                     │
         └─────────────────────┼─────────────────────────────────────────┐
                               │                                         │
                    ┌──────────▼──────────┐                              │
                    │   NATS JetStream    │                              │
                    │  Message Broker     │                              │
                    │ (deploy/compose/    │                              │
                    │ base.yaml: 4222)    │                              │
                    └──────────┬──────────┘                              │
                               │                                         │
         ┌─────────────────────┼─────────────────────┬───────────────────┘
         │                     │                     │
         ▼                     ▼                     ▼
    ┌─────────────┐    ┌──────────────┐      ┌──────────────┐
    │  ArangoDB   │    │ PostgreSQL    │      │  MQTT Broker │
    │  Graph DB   │    │ (workflow     │      │  (Sparkplug  │
    │ (8529)      │    │  state)       │      │  ingestion)  │
    │ Multi-model │    │ (:5432)       │      │              │
    └─────────────┘    └──────────────┘      └──────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| FastAPI Entrypoint | HTTP routing, middleware chain, startup/shutdown lifecycle | `backend/api/main.py` |
| Endpoint Layer | Request validation, event instantiation, response marshaling | `backend/api/endpoints/` |
| Event System | Immutable business logic, transaction coordination, NATS publishing | `backend/api/events/` + `base_event.py` |
| Managers | Singleton services for cross-cutting concerns, SSE broadcast | `backend/api/managers/server_event_manager.py` |
| Models | Pydantic schemas for API boundaries, database documents, validation | `backend/api/models/` |
| Utils | Domain-specific queries, ArangoDB transactions, NATS client, auth | `backend/api/utils/` |
| Sparkplug Bridge | MQTT ingest, protobuf decode, Sparkplug B session state, NATS pub | `backend/sparkplug_bridge/` |
| Workflow Engine | Prefect-orchestrated async tasks, job scheduling, automation | `backend/workflow/flows/` |
| Main SPA | Vue3/Quasar desktop app, state management (Pinia), real-time SSE | `webapps/main/src/` |
| Warehouse Mobile | Quasar + Capacitor mobile barcode scanning, camera access | `webapps/warehouse/src/` |

## Pattern Overview

**Overall:** Event-sourced, immutable event log with transaction-scoped side effects and asynchronous NATS pub/sub for notifications and external integrations.

**Key Characteristics:**
- Every state mutation is a named, versioned Event subclass
- All mutations occur within ArangoDB transactions (ACID guarantees)
- Events publish to NATS JetStream after successful transaction commit
- ServerEventManager fans out notifications via Server-Sent Events (SSE) to browser clients
- Sparkplug B ingestion is a first-class subsystem: MQTT → bridge → NATS subjects
- Separation of concerns: endpoints are thin, managers handle async/background tasks

## Layers

**HTTP Routing & Middleware:**
- Purpose: Accept requests, apply cross-cutting middleware (CORS, GZip), coordinate startup/shutdown
- Location: `backend/api/main.py`
- Contains: FastAPI app initialization, middleware registration, router inclusion (12 routers for 12 domains)
- Depends on: FastAPI, Starlette, NATS client for startup connection
- Used by: All external clients (webapps, mobile, third-party systems)

**Endpoint Layer:**
- Purpose: Receive HTTP requests, validate input via Pydantic, instantiate domain events, return responses
- Location: `backend/api/endpoints/*.py` (22 files: production.py, inventory.py, counting.py, serial.py, collaboration.py, etc.)
- Contains: FastAPI route handlers (POST/GET/PUT/DELETE) that parse request bodies, check auth, create event objects
- Depends on: Event classes, Pydantic models, utility query functions
- Used by: HTTP clients; only entry points for external requests
- Example: `POST /production/batch` → `BatchCompletedEvent(info=request_body)` → `event.save()`

**Event Sourcing Layer:**
- Purpose: Execute immutable business logic as transaction-scoped event objects; atomicity boundary
- Location: `backend/api/events/` (6 domain folders: production, inventory, serial, collaboration, admin, wip, work_session + base_event.py)
- Contains: 50+ concrete event types across production/inventory/serial/collaboration domains
- Flow: `Event.__init__()` → `pre_processing()` → `apply()` (DB mutations) → `store_event()` → `commit_transaction()` → `post_processing()` (NATS publish)
- Atomicity: All mutations in `apply()` occur within a transaction; failure aborts
- Idempotency: Events designed to be replayable (stored event log)
- Depends on: Pydantic models, ArangoDB TransactionDatabase, NATS client for async publish

**Manager Layer (Singletons):**
- Purpose: Handle side effects, async operations, background tasks, WebSocket/SSE broadcast
- Location: `backend/api/managers/server_event_manager.py`
- Contains: `ServerEventManager` — singleton that queues notifications by NATS subtopic, dispatches via SSE to subscribed browser clients
- Depends on: asyncio, FastAPI SSE support
- Lifecycle: Initialized in `main.py` startup hook, closed in shutdown hook
- Used by: Middleware, notification endpoint (`GET /notification`)

**Model Layer (Data Validation):**
- Purpose: Pydantic schemas for API request/response validation, database document structure
- Location: `backend/api/models/` (22 files)
- Contains: `event.py` with EventType enum; domain models for Job, Batch, Step, Position, Movement, Serial, Task, etc.
- Depends on: Pydantic v2, ArangoDB field aliases (_id, _key, _rev, _from, _to)
- Used by: All endpoints, all events for data binding

**Utility Layer:**
- Purpose: Domain query helpers, transaction utilities, auth, NATS client wrapper, validation
- Location: `backend/api/utils/` (30+ files)
- Contains: `db.py` (ArangoDB singleton), `nats_client.py` (NATS wrapper), `auth.py` (JWT), domain query classes (production.Queries, inventory.Queries, serial.Queries)
- Depends on: python-arango, nats.py, cryptography (JWT)
- Used by: All layers (endpoints, events, managers)

**Middleware Layer:**
- Purpose: Request/response interception before/after endpoint execution
- Location: `backend/api/middlewares/gzipfilter_middleware.py`
- Contains: `GZipFilterMiddleware` (extends Starlette GZip, excludes `/notification` from compression for SSE)
- Stacking order: `CORSMiddleware` → `GZipFilterMiddleware` → user endpoint handlers

**Sparkplug B Ingestion Layer:**
- Purpose: Subscribe to MQTT broker, decode Sparkplug B protobuf frames, manage session state, publish to NATS subjects per ADR-0002 taxonomy
- Location: `backend/sparkplug_bridge/` (main.py, decoder.py, session_state.py, host_state.py, publisher.py, kv_store.py, heartbeat.py, subscriber.py)
- Contains: asyncio entrypoint, MQTT subscription, Sparkplug B state machine, NATS KV buckets for session cache and metric aliases
- Depends on: aiomqtt, nats.js, eclipse-tahu (protobuf)
- Used by: MQTT broker (upstream), NATS subscribers (downstream: API, UI, wedge, rule engine)

**Workflow Engine:**
- Purpose: Prefect-orchestrated background task execution, scheduling, retry logic
- Location: `backend/workflow/flows/` (Prefect 3)
- Contains: Flow definitions in `flowcode/` directory (system and integration workflows)
- Depends on: Prefect server (separate container), PostgreSQL for state
- Lifecycle: Agents pull flows from Prefect server, execute, report status

## Data Flow

### Primary Request Path (Example: Step Completion)

1. **HTTP Request** → `POST /production/step/complete` (`backend/api/endpoints/production.py`)
2. **Event Instantiation** → `event = StepCompletedEvent(info=request_body)` generates UUID event key, validates InfoModel
3. **Transaction Begin** → `event.save()` creates ArangoDB transaction with write access to Batch, StepExecutionData, Job, Queue, Event, event_source
4. **Pre-Processing** → `event.pre_processing()` (hook point, usually skipped)
5. **Business Logic** → `event.apply()` fetches batch, updates step execution, checks if batch complete, spawns child event if needed
6. **Store Event** → `event.store_event()` inserts event record into Event collection
7. **Collect Notifications** → `event._build_event_payload()` builds JSON notification for NATS publishing
8. **Transaction Commit** → `tx.commit_transaction()` makes all changes durable
9. **Post-Processing** → `event.post_processing()` (hook point, usually skipped)
10. **Publish to NATS** → `BaseEvent._publish_collected_events(tx)` publishes collected payloads to NATS JetStream
11. **HTTP Response** → Return APIResponse with job_data, batch_data
12. **SSE Fan-Out** → `ServerEventManager.enqueue()` routes notification to subscribed browser clients via `GET /notification`

### Sparkplug Ingestion Path

1. **MQTT Subscribe** → `backend/sparkplug_bridge/subscriber.py` listens on `spBv1.0/#` wildcard
2. **Frame Decode** → `decoder.decode_payload()` decodes Eclipse Tahu protobuf, parses topic structure
3. **Session State Machine** → `session_state` functions track bdSeq per group/edge/device, detect seq gaps
4. **KV Bucket Ops** → Write session state, aliases, and metric values to NATS KV buckets
5. **Publish to NATS** → `publisher.publish_metric_data()` to subjects like `progress.sparkplug.plant1.edge1.device1.metric.temperature.data`
6. **Downstream Consumers** → API, UI, timescale wedge, rule engine subscribe to `progress.sparkplug.*` subjects

## Key Abstractions

**BaseEvent:**
- Purpose: Abstract base for all domain events
- Location: `backend/api/events/base_event.py`
- Pattern: Subclass defines InfoModel (Pydantic), implements get_event_type(), get_tx_collections(), apply()
- Examples: `StepCompletedEvent`, `MovementCompletedEvent`, `SerialCreatedEvent`, `TaskCreatedEvent`

**EventType Enum:**
- Purpose: Centralized registry of all event types in the system
- Location: `backend/api/models/event.py`
- Usage: Events reference EventType for validation; utilities use it for reverse lookup

**Singleton Managers (ServerEventManager):**
- Purpose: Application-scoped services for cross-cutting concerns
- Pattern: Static getInstance() returns singleton; initialized in startup_event()
- Lifecycle: Initialized in `main.py` startup_event(); closed in shutdown_event()

**Domain Query Classes:**
- Purpose: Encapsulate AQL templates and transaction patterns
- Examples: `ProductionQueries`, `InventoryQueries`, `SerialQueries` in `backend/api/utils/`
- Pattern: Static methods that return AQL bind_vars dict or execute query within transaction

## Entry Points

**HTTP API (FastAPI):**
- Location: `backend/api/main.py` (port 8000)
- Triggers: HTTP requests from webapps/clients (GET, POST, PUT, DELETE)
- Responsibilities: Validate request, verify JWT, instantiate domain event, return JSON response

**WebSocket / Server-Sent Events:**
- Location: `backend/api/endpoints/notification.py` (`GET /notification?topic=...`)
- Triggers: Browser client SSE connection with topic subscription
- Responsibilities: Maintain connection, deliver queued notifications via ServerEventManager

**NATS Notification Subscriber (Startup Hook):**
- Location: `backend/api/main.py` line 96-104
- Triggers: NATS broker has message on `progress.notification.>` subjects
- Responsibilities: Decode payload, enqueue in ServerEventManager per topic

**Sparkplug MQTT Subscriber:**
- Location: `backend/sparkplug_bridge/subscriber.py:run_subscribe_loop()`
- Triggers: MQTT broker has message on `spBv1.0/#` topics
- Responsibilities: Decode Sparkplug protobuf, publish to NATS JetStream

**Prefect Workflow Execution:**
- Location: `backend/workflow/flows/flowcode/`
- Triggers: Prefect server scheduler or manual trigger
- Responsibilities: Run orchestrated async tasks (ETL, integration syncs, data processing)

## Architectural Constraints

- **Transactions:** All database mutations must occur within ArangoDB transactions; `Event.save()` manages begin/commit/abort
- **Event Idempotency:** Events must be replayable without side effects (required for recovery)
- **Single Event Key Generation:** UUIDs generated once in `__init__()`, used consistently across apply() and store_event()
- **NATS Publishing Timing:** Published only after transaction commit
- **JWT Authentication:** Token required for all endpoints except `/hello`; org_id and user_key extracted from token claims
- **Global State:** Minimal (ServerEventManager singleton, NATS client singleton)
- **Threading Model:** FastAPI async/await; Sparkplug bridge uses asyncio; Prefect agents manage their own execution pools
- **Circular Imports:** Events may spawn child events; handled via `create_as_child()` classmethod to avoid import cycles

## Anti-Patterns

### Bare Exception Handling

**What happens:** Legacy endpoints contain `except:` clauses that catch all exceptions silently

**Why it's wrong:** Masks bugs, makes debugging difficult, obscures error propagation paths

**Do this instead:** Catch specific exceptions, log them with context, re-raise or convert to HTTPException with appropriate status code

### Direct Print Debugging

**What happens:** Some endpoints use `print()` instead of logger

**Why it's wrong:** Print statements don't reach log aggregation, are lost in container logs

**Do this instead:** Use Python logging module with proper logger setup

### Incomplete Error Responses

**What happens:** Errors returned without sufficient context for debugging or user action

**Why it's wrong:** Clients can't distinguish between transient and permanent failures

**Do this instead:** Return HTTPException with status code (409 for conflict, 400 for validation, 500 for server error) and detail dict

## Error Handling

**Strategy:** Validation at boundaries (Pydantic), precondition checks in endpoints, transaction rollback for DB failures

**Patterns:**
- Validation errors → 400 Bad Request (Pydantic raises ValidationError)
- Precondition failures → 409 Conflict (endpoint checks state before creating event)
- Not found → 404 Not Found
- Transaction rollback → finally block in Event.save() aborts if exception occurs during apply()
- NATS publish failures → logged but non-fatal; HTTP response succeeds (fire-and-forget)
- JWT failures → 401 Unauthorized

## Cross-Cutting Concerns

**Logging:** Python logging module with per-module loggers (level INFO by default)

**Validation:** Pydantic at API boundaries (request body validation); Event InfoModel re-validates event-specific data

**Authentication:** JWT tokens in Authorization header; org_id and user_key extracted from token claims; verified by `auth.verify_token()` dependency

**Media Storage:** File uploads handled by `endpoints/media.py`; stored in `backend/api/media/` directory (Docker volume `/media`)

**Notification Routing:** NATS subjects follow `progress.{domain}.{subtopic}` pattern; ServerEventManager fans out via SSE to subscribed clients

**Transaction Coordination:** Event.save() manages lifecycle; multiple events can share a transaction via `create_as_child()` and `spawn_multiple()`

---

*Architecture analysis: 2026-05-08*
