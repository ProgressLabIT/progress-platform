# Architecture

**Analysis Date:** 2026-02-13

## Pattern Overview

**Overall:** Event-sourcing with CQRS-style separation, using immutable event-based state mutations across a microservices architecture.

**Key Characteristics:**
- **Event-driven**: All state changes flow through a single event system that persists to an immutable event log
- **Multi-service**: Decoupled backend (FastAPI), frontend (Vue 3), and workflow (Prefect) services
- **Graph-database centric**: ArangoDB as the system of record with transactional consistency
- **Message-driven communication**: Kafka integration for asynchronous event broadcasting and real-time updates
- **Transaction-scoped**: Multi-collection ArangoDB transactions ensure consistency within event application

## Layers

**Presentation Layer (Frontend):**
- Purpose: User interface for production management, inventory, tasks, quality, and analytics
- Location: `webapps/main/src/`, `webapps/warehouse/src/`
- Contains: Vue 3 components, composables, pages, routes, stores (Pinia + Vuex)
- Depends on: Backend API (REST), WebSocket for real-time updates
- Used by: End users and operators

**API Layer (Backend):**
- Purpose: REST API endpoints that validate requests, dispatch events, and return results
- Location: `backend/api/endpoints/`
- Contains: Route handlers for 20+ domain areas (production, inventory, collaboration, etc.)
- Depends on: Event system, database utilities, auth middleware
- Used by: Frontend, external integrations, CLI tools

**Event System:**
- Purpose: Immutable event log and application of business logic
- Location: `backend/api/events/`
- Contains: 82 event classes organized by domain (production, collaboration, inventory, serial, work_session, admin, wip)
- Depends on: Database transactions, event models
- Used by: Endpoints (to trigger events), post-processing (persists to Kafka)

**Domain Logic Layer:**
- Purpose: Reusable business logic utilities and helpers
- Location: `backend/api/utils/` (domain-specific: `production.py`, `inventory.py`, `collaboration.py`, `traceability.py`, `serial.py`)
- Contains: Query helpers, validation, state computation
- Depends on: Database connection, models
- Used by: Events, endpoints

**Data Layer:**
- Purpose: Database abstraction and persistence
- Location: `backend/api/utils/db.py`, `backend/api/managers/`
- Contains: ArangoDB connection pooling, transaction management, WebSocket manager, Kafka producer/consumer
- Depends on: External services (ArangoDB, Kafka)
- Used by: All layers above

**Workflow Orchestration:**
- Purpose: Schedule and execute batch processes
- Location: `backend/workflow/flows/`
- Contains: Prefect 2.x flow definitions
- Depends on: Backend API, database
- Used by: System for scheduled/periodic operations

## Data Flow

**User Action → Event → State Update → Real-time Broadcast:**

1. User action on frontend (e.g., complete task)
2. Frontend calls `sendEvent()` composable (`webapps/main/src/composables/event.js`)
3. Event data posted to `POST /event` endpoint (`backend/api/endpoints/*.py`)
4. Endpoint validates auth, creates event instance from event class in `backend/api/events/`
5. Event class in `__init__` validates event data via Pydantic model
6. Event `save()` method:
   - Creates ArangoDB transaction with required collections
   - Calls `pre_processing()` (override hook for subclasses)
   - Calls `apply()` - executes business logic (inserts/updates records, validates state)
   - Stores immutable event record in `Event` collection
   - Calls `post_processing()` (override hook)
   - Commits transaction
7. Kafka producer publishes event to topic (async)
8. Kafka consumer in `NotificationsKafkaConsumer` picks up event
9. WebSocket manager broadcasts to connected clients
10. Frontend stores receive updates via WebSocket listener

**State Management (Frontend):**
- Vuex store for session/auth state (`webapps/main/src/boot/store.js`)
- Pinia stores for domain state (`webapps/main/src/stores/*.js`)
- Store persistence via composables (`reStore.js`, task store uses automatic save on unload)

## Key Abstractions

**BaseEvent:**
- Purpose: Base class for all business events, enforces interface contract
- File: `backend/api/events/base_event.py`
- Pattern: Abstract base class with required methods `get_event_type()`, `get_tx_collections()`, `apply()`
- Example implementations: `TaskCreatedEvent`, `BatchCompletedEvent`, `IssueCreatedEvent`

**EventInfoModel (Pydantic):**
- Purpose: Validates event payload data before persistence
- File: `backend/api/models/event.py`
- Pattern: Extends `EventInfoModel` class-by-class to define event-specific fields
- Example: `TaskCreatedEvent.InfoModel` defines task_key, task_type_key, title, assigned_to, etc.

**Endpoint Pattern (FastAPI):**
- Purpose: Accept requests, validate, create events, handle responses
- Files: `backend/api/endpoints/*.py` (admin.py, production.py, collaboration.py, etc.)
- Pattern: `@router.post()` decorator → dependencies=[auth.verify_token] → create event → return response
- Example: `POST /work-order` in `endpoints/production.py` creates WorkOrder

**Domain Utility Functions:**
- Purpose: Shared logic for queries and state transitions
- Files: `backend/api/utils/production.py`, `inventory.py`, etc.
- Pattern: Stateless functions that accept transaction `tx` parameter
- Example: `create_job_record()`, `update_target_queue()` in `utils/production.py`

**ArangoDB Base Models:**
- Purpose: Pydantic models that map to ArangoDB document structure
- File: `backend/api/models/base_models.py`
- Pattern: `FlexModel` (base), `ArangoDocument` (with _id, _key, _rev), `ArangoEdge` (_from, _to)
- Used by: All domain models (WorkOrder, Task, Issue, etc.)

## Entry Points

**Backend API:**
- Location: `backend/api/main.py`
- Triggers: FastAPI app startup on docker-compose up
- Responsibilities:
  - Middleware stack setup (CORS, GZip filtering, notification middleware)
  - Router registration (20+ routers from endpoints/)
  - Kafka producer/consumer initialization
  - WebSocket manager startup

**Frontend Main App:**
- Location: `webapps/main/src/App.vue`
- Triggers: Vue 3 mount
- Responsibilities:
  - Route rendering via `<router-view />`
  - CSS variables setup
  - Session persistence (saves state on beforeunload)
  - Task store recovery

**Frontend Router:**
- Location: `webapps/main/src/router/index.js`
- Triggers: Navigation to any route
- Responsibilities:
  - Permission checking (scope-based via store)
  - Locale detection and i18n setup
  - Task context handling on route change
  - Authentication enforcement (redirects to login if not auth)

**Workflow Service:**
- Location: `backend/workflow/flows/`
- Triggers: Prefect schedule or manual execution
- Responsibilities: Batch processing, report generation, data cleanup

## Error Handling

**Strategy:** Transaction-scoped rollback with explicit exception raising and HTTP error response

**Patterns:**

1. **Validation-level errors** (Pydantic models):
   - Event `__init__` validates via model instantiation
   - Raises `ValueError` if InfoModel validation fails
   - Propagates to endpoint, caught as 422 Unprocessable Entity

2. **Transaction-scoped errors** (Event apply):
   - Event `apply()` method may raise exceptions
   - Transaction auto-aborts via try/finally in `save()`
   - Exception re-raised to endpoint
   - Endpoint catches and returns 500 or custom HTTPError

3. **Business logic errors** (Domain utilities):
   - Utilities raise custom exceptions (e.g., `HTTPError` in `utils/exceptions.py`)
   - Caught by endpoint, converted to HTTP response
   - Example: "Task with code X already exists" → 409 Conflict

4. **Database errors**:
   - Transaction errors bubble up as ArangoDB exceptions
   - Caught in finally block to abort transaction
   - Example: Collection not found, duplicate key → 500 Server Error

**Example (from `backend/api/events/collaboration/task_created.py`):**
```python
def apply(self):
    # Validation error example
    if self.tx.collection('Task').find(dict(code=self.info.code)).count() > 0:
        raise ValueError(f"Task with code {self.info.code} already exists")

    # Exception handling in counter generation
    try:
        task_data.code = _generate_counter(self.tx, counter_key)
    except Exception as e:
        raise Exception("Cannot generate task code...") from e
```

## Cross-Cutting Concerns

**Logging:**
- No structured logging framework detected; uses Python `print()` for debug info
- Kafka consumer logs message topic/offset
- Frontend uses `console.error()` and `console.log()`

**Validation:**
- Pydantic models for schema validation (API requests → models)
- Event InfoModel validation before database write
- Permission validation in router guards (`router/index.js`)
- Domain-level validation in event `apply()` methods

**Authentication:**
- JWT token verification via `auth.verify_token` dependency
- Token validation in `utils/auth.py` (decode and extract user info)
- Session stored in Vuex state (`store.state.session.user`, `store.state.session.session_key`)
- Router redirects unauthenticated requests to login
- Token refreshed on `recognizeMe` action (persisted session recovery)

**Authorization:**
- Scope-based (role-like system) in route meta
- `hasRoutePermission()` in router checks `store.getters.hasPermission(route.meta.scope)`
- Endpoint-level checks possible but not consistently applied

**Real-time Updates:**
- WebSocket connection via NotificationMiddleware
- Kafka events → NotificationsKafkaConsumer → WebSocketManager.enqueue()
- Frontend consumes via WebSocket listener (composable or store subscription)
- Task context automatically attached to events if active task selected

---

*Architecture analysis: 2026-02-13*
