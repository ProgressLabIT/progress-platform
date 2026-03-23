# Architecture

**Analysis Date:** 2026-03-12

## Pattern Overview

**Overall:** Event Sourcing with Domain-Driven Design (DDD) + Microservices for webapps

**Key Characteristics:**
- **Immutable event log** — All business logic mutations flow through typed Events rather than direct state updates
- **Event-driven side effects** — Asynchronous reactions via Kafka topic subscriptions and manager patterns
- **Layered backend** — FastAPI endpoints → events → transactional state mutations → database
- **Dual-webapp architecture** — Main desktop app (Quasar) + mobile warehouse app (Quasar + Capacitor)
- **Graph database (ArangoDB)** — Documents + edges for domain entity relationships

## Layers

**API Gateway & Routing:**
- Purpose: HTTP request routing, middleware chain, static file serving, TLS termination
- Location: `backend/api/main.py` (FastAPI app), `deploy/compose/base.yaml` (Traefik proxy)
- Contains: FastAPI router registration, CORS/GZip/notification middleware, startup/shutdown hooks
- Depends on: FastAPI, Starlette middleware, Kafka producer initialization
- Used by: All external clients (webapps, mobile, third-party integrations)

**HTTP Endpoints (Domain-Specific):**
- Purpose: Receive requests and instantiate domain events
- Location: `backend/api/endpoints/*.py` (20+ files: production.py, inventory.py, counting.py, etc.)
- Contains: FastAPI route handlers that validate input, create event objects, return responses
- Depends on: Event classes, Pydantic models, utility functions (auth, db, counter generation)
- Used by: HTTP clients; endpoints are the only entry points for external requests

**Event System (Core Business Logic):**
- Purpose: Execute immutable business logic as transaction-scoped event objects
- Location: `backend/api/events/` (base_event.py + domain-specific event files)
- Contains: BaseEvent abstract class and 50+ concrete event types organized by domain:
  - `backend/api/events/production/` — Job/batch/step state transitions
  - `backend/api/events/inventory/` — Stock movements, warehouse operations
  - `backend/api/events/serial/` — Serial number tracking
  - `backend/api/events/collaboration/` — Issues, messages, tasks
- Depends on: Pydantic models (EventInfoModel, event-specific schemas), ArangoDB transactions
- Used by: Endpoints instantiate events; managers listen to event types

**Event Application (Transaction Scope):**
- Flow: Event.save() → pre_processing() → apply() → store_event() → commit_transaction()
- Atomicity: All DB mutations in apply() occur within a transaction; failure aborts the entire transaction
- Idempotency: Events must be designed to be replayable without side effects (required for recovery)

**Managers (Cross-Cutting Services):**
- Purpose: Handle side effects, async operations, and publish domain events to Kafka
- Location: `backend/api/managers/*.py`
- Contains:
  - `ExecutorManager` — Thread pool for background jobs
  - `NotificationManager` — Broadcasts changes via WebSocket to connected clients
  - `KafkaConsumerManager` — Routes Kafka messages to subscribers
  - `WebsocketManager` — Maintains WebSocket connections and broadcast queue
  - `ServerEventManager` — Server-side event coordination
- Depends on: Kafka producer/consumer, threading
- Used by: Middleware, event post_processing(), startup hooks

**Models (Data Validation & Schemas):**
- Purpose: Pydantic models for API request/response validation and database document structure
- Location: `backend/api/models/*.py` (base_models.py, event.py, product.py, production.py, etc.)
- Contains:
  - BaseModel classes (FlexModel, ArangoDocument, ArangoEdge)
  - EventInfoModel — Base schema for all events
  - EventModel — Storage envelope with metadata
  - Domain models — ProductDetails, WorkOrder, Job, Batch, CountSession, etc.
- Depends on: Pydantic v2, ArangoDB field aliases (_id, _key, _rev, _from, _to)
- Used by: Endpoints for request validation, events for data binding, utilities for queries

**Utilities (Shared Logic):**
- Purpose: Cross-cutting concerns and helper functions
- Location: `backend/api/utils/` (40+ files)
- Contains:
  - `db.py` — ArangoDB client and transaction management
  - `auth.py` — JWT token verification
  - `event.py` — Event class registry and lookup
  - `config.py` — Environment configuration
  - `kafka/` — Kafka producer/consumer/admin utilities
  - `production/`, `inventory/`, `serial/` — Domain-specific query helpers
  - `media.py`, `file.py` — File/attachment handling
- Depends on: External libraries (arango, kafka, fastapi, pydantic)
- Used by: All layers (endpoints, events, managers)

**Middleware:**
- Purpose: Cross-cutting request/response handling
- Location: `backend/api/middlewares/*.py`
- Contains:
  - `NotificationMiddleware` — Triggers global refresh notification on non-GET requests
  - `GZipFilterMiddleware` — Conditional compression (exclude notification endpoint)
- Depends on: Starlette BaseHTTPMiddleware
- Used by: FastAPI app.add_middleware()

## Data Flow

**Create Work Order Flow:**

1. **Endpoint** (`POST /work-order`) receives request with WorkOrderNew model
2. **Validation** — Pydantic validates schema; endpoint checks product exists, wo_code unique
3. **Event Instantiation** — Endpoint creates JobStarted/WorkOrderCreated event with validated data
4. **Transaction** — Event.save() opens ArangoDB transaction with collections [WorkOrder, Job, Queue, Counter]
5. **Apply** — apply() method:
   - Updates WorkOrder document (status='CREATED')
   - Creates Job record in Jobs collection
   - Updates Queue with new job
   - Increments Counter if auto-numbering enabled
6. **Store** — Event metadata written to Event collection
7. **Commit** — ArangoDB transaction commits atomically
8. **Post-Processing** — Event.post_processing() may queue Kafka messages
9. **Response** — Endpoint returns WorkOrder/Job data to client
10. **Notification** — NotificationMiddleware triggers WebSocket broadcast of "refresh" to all connected clients
11. **Kafka Async** — KafkaConsumerManager distributes domain events to subscribers (if enabled per domain)

**Inventory Movement Flow:**

1. Endpoint receives stock movement request (location_from, location_to, quantity)
2. MovementPlanned event created
3. Transaction: MovementPlanned.apply() writes Movement document, updates InventoryPosition quantities
4. Movement event stored
5. Domain may publish to Kafka topic 'inventory' for downstream systems
6. NotificationManager broadcasts to warehouse app clients

**State Management (Query Pattern):**

Endpoints typically load state using query utilities before deciding if an action is allowed:
- `utils.production.Queries.get_job()` — Fetch job with current state
- `utils.inventory.Queries.get_position()` — Fetch location quantity
- Business logic checks preconditions (e.g., "Job must be in RUNNING state")
- If valid, event is created; if not, HTTPException raised

**State Mutation:**

Never direct document updates. Always:
1. Create an event class
2. Event.apply() handles all mutations
3. Store event for audit trail
4. Downstream systems react via Kafka or NotificationManager

## Key Abstractions

**BaseEvent:**
- Purpose: Abstract base for all domain events
- Examples: `backend/api/events/production/job_started.py`, `backend/api/events/inventory/movement_completed.py`
- Pattern:
  - Each event defines event_type, tx_collections, and apply() method
  - InfoModel (Pydantic) validates event-specific data
  - apply() is transactional and idempotent
  - post_processing() handles Kafka publishing (optional)

**EventType Enum:**
- Purpose: Centralized registry of all event types in the system
- Examples: JOB_STARTED, MOVEMENT_COMPLETED, COUNT_SESSION_APPLIED, SERIAL_CREATED
- Location: `backend/api/models/event.py`
- Usage: Events reference EventType for validation; utilities use it for lookup

**Managers (Singleton Pattern):**
- Purpose: Application-scoped services for cross-cutting concerns
- Pattern: getInstance() returns singleton; initialized once on startup
- Examples: NotificationManager broadcasts changes; KafkaConsumerManager subscribes to topics
- Lifecycle: Initialized in main.py startup_event(); closed in shutdown_event()

**Middleware Chain:**
- Purpose: Request/response interception before/after endpoint execution
- Order: CORSMiddleware → GZipFilterMiddleware → NotificationMiddleware
- Effect: NotificationMiddleware automatically notifies clients of state changes

## Entry Points

**HTTP API:**
- Location: `backend/api/main.py` line 49-92
- Triggers: HTTP requests from webapps/clients
- Responsibilities:
  - Initialize FastAPI app with middleware
  - Register 20+ domain endpoint routers
  - Start Kafka producer, WebSocket manager, notification consumer on startup
  - Gracefully close resources on shutdown

**WebSocket:**
- Location: `backend/api/managers/websocket_manager.py`
- Triggers: Client WebSocket connections
- Responsibilities: Maintain client connections, broadcast notifications, handle disconnections

**Kafka Consumers:**
- Location: `backend/api/managers/kafka_consumer_manager.py`
- Triggers: Kafka broker has messages
- Responsibilities: Route topics to registered subscribers (NotificationsKafkaConsumer, ChatKafkaConsumer, etc.)

**Database Transactions:**
- Triggered by: Event.save() calls
- Scope: Single event application (atomicity boundary)
- Commits: Only if all logic succeeds; aborts on exception

## Error Handling

**Strategy:** Fail-fast with transaction rollback

**Patterns:**
- **Validation errors** — Endpoint returns 400 with HTTPException detail before creating event
- **Precondition failures** — Endpoint checks state; returns 409 if action not allowed
- **Transaction rollback** — Event.save() finally block aborts transaction if exception occurs
- **Kafka failures** — Non-blocking; exceptions in post_processing() do not fail the event
- **HTTP exceptions** — Pydantic validation or endpoint logic raises HTTPException with status code and detail

**Example:**
```python
# endpoint checks precondition
job = Queries.get_job(job_id)
if job.status != 'IDLE':
    raise HTTPException(status_code=409, detail="Job must be IDLE to start")

# if check passes, event is created (transaction manages atomicity)
event = JobStarted(info={...})
event.save()  # Atomic: succeeds or rolls back entirely
```

## Cross-Cutting Concerns

**Logging:** Console output only; no structured logging framework detected. Exceptions logged via Python traceback module.

**Validation:**
- Request level: Pydantic models in endpoints validate schema
- Event level: Event-specific InfoModel validates event data
- Business level: Endpoints check preconditions (state, permissions, constraints)

**Authentication:**
- Method: JWT tokens in Authorization header
- Verification: `utils.auth.verify_token()` dependency in FastAPI routes
- Scope: Token-dependent endpoints; /hello endpoint is public

**Authorization:**
- Org-scoped access control (implied by queries filtering by org_id)
- Role-based access (stored in token claims; checked at endpoint level)

**Media/Files:**
- Attachment storage: `backend/api/media/` directory (Docker volume `/media`)
- Upload: `endpoints/media.py` handles multipart form uploads
- Retrieval: FastAPI serves files directly via `/media/{path}`

**Transactions:**
- All state mutations occur within ArangoDB transactions
- Collections specified via Event.get_tx_collections()
- Coordinator: Event.save() manages begin/commit/abort lifecycle

---

*Architecture analysis: 2026-03-12*
