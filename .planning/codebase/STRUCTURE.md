# Codebase Structure

**Analysis Date:** 2026-02-13

## Directory Layout

```
progress-platform/
├── backend/                    # Backend services (Python)
│   ├── api/                    # FastAPI main application
│   │   ├── main.py            # Entry point, middleware, router registration
│   │   ├── endpoints/         # 20+ domain-specific route handlers
│   │   ├── events/            # Event-sourcing system (82 event classes)
│   │   ├── models/            # Pydantic models (domain objects)
│   │   ├── utils/             # Domain logic, database, auth, helpers
│   │   ├── managers/          # WebSocket, Kafka, Executor managers
│   │   ├── middlewares/       # Notification, GZip filtering
│   │   └── media/             # File/media handling
│   ├── workflow/              # Prefect 2.x orchestration flows
│   ├── commons/               # Shared utilities
│   ├── scripts/               # Dev/CLI scripts
│   └── lte/, mock/, reports/  # Legacy/specialized modules
│
├── webapps/                    # Frontend applications
│   ├── main/                  # Main production webapp (Quasar + Vue 3)
│   │   ├── src/
│   │   │   ├── App.vue        # Root component
│   │   │   ├── components/    # 90+ Vue components by feature
│   │   │   ├── composables/   # 18 reusable logic modules
│   │   │   ├── pages/         # Page views
│   │   │   ├── views/         # Feature views (57 directories)
│   │   │   ├── router/        # Route definitions (feature-based splitting)
│   │   │   ├── stores/        # Pinia stores (task, config, countSession, taskType)
│   │   │   ├── store/         # Vuex store (session, auth)
│   │   │   ├── boot/          # Plugin initialization
│   │   │   ├── i18n/          # Translations (en.js, it.js)
│   │   │   ├── layouts/       # Layout components
│   │   │   ├── css/           # Global styles
│   │   │   ├── assets/        # Static assets
│   │   │   ├── lib/           # Utility libraries
│   │   │   ├── plugins/       # Custom Vue plugins
│   │   │   ├── types/         # TypeScript definitions
│   │   │   └── utils/         # Utility functions
│   │   └── quasar.conf.js     # Quasar config
│   │
│   └── warehouse/             # Mobile warehouse app (Quasar + Capacitor)
│       └── src/               # Same structure as main
│
├── db/                        # Database artifacts
│   ├── migrations/            # AQL migration scripts (numbered: 226-*.aql)
│   ├── scripts/               # Database initialization scripts
│   ├── backup/                # Database backup files
│   ├── DB Queries/            # Reference queries
│   └── Data Architecture/     # Schema documentation
│
├── deploy/                    # Deployment configuration
│   ├── compose/               # Docker Compose files
│   │   ├── base.yaml          # Core services (Traefik, API, DB, Kafka)
│   │   ├── dev.yaml           # Dev overrides (hot-reload, mounts)
│   │   ├── dev.debug.yaml     # Remote debugging config
│   │   ├── workflow.yaml      # Prefect server + PostgreSQL
│   │   ├── stack.yaml         # Production Swarm config
│   │   ├── tls.yaml           # TLS configuration
│   │   └── [other].yaml       # Integration, warehouse, reporting configs
│   └── [dockerfile locations]
│
├── testing/                   # Testing artifacts and data
├── files/, media/             # File/media storage
├── plans/, cli/               # Planning tools, CLI scripts
├── km/                        # Knowledge management / documentation
└── .planning/                 # GSD planning outputs
    └── codebase/              # This directory (architecture docs)
```

## Directory Purposes

**backend/api/:**
- Purpose: Core FastAPI REST API
- Contains: Request handlers, events, data models, domain logic
- Key files: `main.py` (app setup), `endpoints/*.py` (route groups), `events/base_event.py` (event base)

**backend/api/endpoints/:**
- Purpose: REST route handlers organized by domain
- Contains: 20+ files mapping to features:
  - `production.py` - Work orders, jobs, batches
  - `inventory.py` - Warehouse stock movements
  - `collaboration.py` - Tasks, issues, messages
  - `traceability.py` - Serial tracking
  - `process.py` - Process definitions
  - `product.py` - Product master data
  - `auth.py`, `admin.py`, `org.py`, `form.py`, `serial.py`, `counting.py`, etc.
- Files: Router object named after module, always imported in `main.py` via `app.include_router()`

**backend/api/events/:**
- Purpose: Event-sourcing system with immutable event log
- Contains: 82 event classes in domain folders
  - `base_event.py` - BaseEvent abstract class
  - `production/` (11 events) - Job/batch lifecycle
  - `collaboration/` (13 events) - Task/issue/message lifecycle
  - `inventory/` (13 events) - Movement/counting/warehouse
  - `serial/` (8 events) - Serial number tracking
  - `work_session/`, `wip/`, `admin/` - Specialized events
- Pattern: Each event extends BaseEvent, implements InfoModel, apply() method, get_event_type(), get_tx_collections()

**backend/api/models/:**
- Purpose: Pydantic schema definitions for API and database
- Contains: 24 files by domain
  - `base_models.py` - FlexModel, ArangoDocument, ArangoEdge
  - `production.py` - WorkOrder, Job, Batch models
  - `collaboration.py` - Task, Issue, Message models
  - `event.py` - EventInfoModel, EventType enum (116 event types)
  - Domain folders: `inventory/`, etc.

**backend/api/utils/:**
- Purpose: Domain logic, database utilities, helpers
- Contains: 34 files
  - `db.py` - ArangoDB connection singleton
  - `auth.py` - JWT validation and user extraction
  - Domain helpers:
    - `production.py` - Queries, job/WO creation
    - `inventory.py` - Movement validation, counting helpers
    - `collaboration.py` - Task/issue utilities
    - `traceability.py` - Serial tracking logic
  - `kafka/` (6 files) - Kafka producer, consumer, admin
  - `delayedqueue/` - Queue management
  - `dhr.py` - Large helper file (44KB)

**backend/api/managers/:**
- Purpose: Singleton managers for system-wide resources
- Contains: 5 files
  - `websocket_manager.py` - WebSocket connection pooling
  - `kafka_consumer_manager.py` - Consumer lifecycle
  - `executor_manager.py` - Async task execution
  - `server_event_manager.py` - Server-sent events
  - `notification_manager.py` - Notification dispatch

**webapps/main/src/components/:**
- Purpose: Reusable Vue 3 components
- Contains: 90+ `.vue` files organized by feature:
  - Production components (work orders, jobs, phases)
  - Inventory components (movements, counting)
  - Collaboration components (tasks, issues, chat)
  - Form components (fields, layouts)
  - UI components (modals, dialogs, tables)
- Naming: `[Feature][Component].vue` (e.g., `ProductionJobDialog.vue`)

**webapps/main/src/composables/:**
- Purpose: Reusable Vue 3 composition API logic
- Contains: 18 files
  - `event.js` - `sendEvent()`, `sendEventsBulk()` for triggering events
  - `reStore.js` - Store persistence utilities
  - `taskNavigation.js` - Task context handling on route changes
  - `productionAdminActions.js` - Production admin operations (20KB)
  - `useCountRecordAggregation.js`, `useCountRecordFilters.js`, `useCountRecordExport.js` - Counting features
  - `useUncountedInventory.js`, `warehouse.js` - Inventory features

**webapps/main/src/stores/:**
- Purpose: Pinia stores (modern state management)
- Contains: 4 files
  - `task.js` - Task state (tasks array, activeTaskKey, loading)
  - `config.js` - Configuration state
  - `countSession.js` - Counting session state
  - `taskType.js` - Task type definitions

**webapps/main/src/store/:**
- Purpose: Vuex store (legacy state management, being phased out)
- Contains: Session, auth, user preferences
- Location: `store/` (separate from Pinia `stores/`)

**webapps/main/src/router/:**
- Purpose: Vue Router definitions with role-based code splitting
- Contains: 11 files
  - `index.js` - Main router setup, guards, permission checking
  - `routes.js` - Route collection
  - Feature-specific route files:
    - `adminRoutes.js` - Admin features
    - `productionRoutes.js` - Production features
    - `warehouseRoutes.js` - Warehouse features
    - `qualityRoutes.js`, `taskRoutes.js`, `traceabilityRoutes.js`, `operatorRoutes.js`
  - `libraryRoutes.js` - Reference/library features

**webapps/main/src/i18n/:**
- Purpose: Translation files for internationalization
- Contains: 5 files
  - `en.js` - English translations (complete set)
  - `it.js` - Italian translations (complete set)
  - Used by router to detect locale and app to switch languages

**webapps/main/src/boot/:**
- Purpose: Plugin initialization and boot modules
- Contains: 8 files
  - `axios.js` - HTTP client setup with base URL, headers, interceptors
  - `pinia.js` - Pinia store initialization
  - `store.js` - Vuex store initialization
  - `i18n.js` - i18n plugin setup
  - `theme.js` - Theme initialization
  - `filters.js` - Custom Vue filters
  - `form.js` - Form plugin setup

**db/migrations/:**
- Purpose: Database schema evolution
- Contains: Numbered AQL scripts (e.g., `226-process-steps-to-custom-fields.aql`)
- Pattern: Run sequentially during deployment; immutable once created
- Examples: Collection creation, edge definitions, data transformations

**deploy/compose/:**
- Purpose: Docker Compose orchestration
- Contains: 12 files
  - `base.yaml` - Core services (Traefik reverse proxy, API, ArangoDB, Kafka, media volumes)
  - `dev.yaml` - Development overrides (source code mounts for hot-reload)
  - `dev.debug.yaml` - Remote debugging setup (port mappings)
  - `workflow.yaml` - Prefect server + PostgreSQL for orchestration
  - `stack.yaml` - Production Swarm deployment config
  - `tls.yaml` - HTTPS/TLS setup
  - Domain-specific: `warehouse.yaml`, `integration.yaml`, `reporting.yaml`

## Key File Locations

**Entry Points:**
- `backend/api/main.py` - FastAPI app initialization, middleware, router registration
- `webapps/main/src/App.vue` - Vue 3 root component, router view
- `webapps/main/src/router/index.js` - Router initialization, auth guards
- `webapps/main/quasar.conf.js` - Quasar build configuration

**Configuration:**
- `backend/api/utils/config.py` - Environment config loading
- `webapps/main/quasar.conf.js` - Build settings, dev server config
- `webapps/main/src/boot/*.js` - Plugin/library setup
- `deploy/compose/base.yaml` - Service definitions

**Core Logic:**
- `backend/api/events/base_event.py` - Event-sourcing pattern
- `backend/api/utils/production.py` - Work order/job utilities (20KB)
- `backend/api/utils/dhr.py` - Large domain helper (44KB)
- `webapps/main/src/composables/event.js` - Event dispatching
- `webapps/main/src/composables/taskNavigation.js` - Task context handling

**Testing:**
- `testing/` - Test files and fixtures
- Test location convention: Test files co-located with source (patterns suggest `.test.py` or `.spec.js` naming)

## Naming Conventions

**Files:**
- Python: snake_case (e.g., `production.py`, `base_event.py`, `kafka_producer.py`)
- Vue/JS: PascalCase for components (e.g., `TaskDialog.vue`, `ProductionJobTable.vue`), camelCase for JS modules (e.g., `eventbus.js`, `reStore.js`)
- Models: PascalCase class names, snake_case filenames (e.g., `models/production.py` contains `WorkOrder`, `Job` classes)
- Events: PascalCase with `Event` suffix (e.g., `TaskCreatedEvent`, `BatchCompletedEvent`)

**Directories:**
- Feature-based (e.g., `production/`, `inventory/`, `collaboration/`)
- Utility grouping (e.g., `utils/`, `managers/`, `models/`)
- Layer-based (e.g., `endpoints/`, `events/`, `components/`, `views/`)

**Classes:**
- Base classes: `Base` prefix or `Base` suffix (e.g., `BaseEvent`, `FlexModel`)
- Models: Domain name (e.g., `WorkOrder`, `Task`, `Issue`)
- Events: Domain action (e.g., `TaskCreatedEvent`, `JobStartedEvent`)
- Managers: Resource + `Manager` suffix (e.g., `WebsocketManager`, `KafkaConsumerManager`)

**Functions:**
- camelCase in JavaScript (e.g., `sendEvent()`, `hasRoutePermission()`)
- snake_case in Python (e.g., `create_job_record()`, `_generate_counter()`)

**Constants/Enums:**
- UPPER_SNAKE_CASE (e.g., `EventType.TASK_CREATED`, `BATCH_COMPLETED`)

## Where to Add New Code

**New Feature (Complete Feature):**
- **Primary code:**
  - Backend event: `backend/api/events/[domain]/[action].py`
  - Endpoint: `backend/api/endpoints/[domain].py` (add route to existing file)
  - Model: `backend/api/models/[domain].py` (extend existing)
- **Tests:**
  - `testing/[domain]_test.py` (or co-located with source)
- **Frontend:**
  - Component: `webapps/main/src/components/[Feature][Component].vue`
  - Composable: `webapps/main/src/composables/use[Feature].js`
  - Store (Pinia): `webapps/main/src/stores/[feature].js`
  - Route: `webapps/main/src/router/[featureArea]Routes.js`
  - View: `webapps/main/src/views/[Feature]/` (folder with subcomponents)

**New Component/Module:**
- **Implementation:** Create in appropriate `src/components/`, `src/composables/`, `src/utils/`
- **Usage:** Import in parent component or composable
- **Exporting:** Vue components exported implicitly via `<template>`, JS modules use ES6 `export`

**New Domain Utilities (Python):**
- **Shared helpers:** `backend/api/utils/[domain].py`
- **Database queries:** Add query functions to domain utils file
- **Validation:** Add validation logic to event `apply()` method or utils

**New Event Type:**
1. Create class in `backend/api/events/[domain]/[action].py`
2. Add `EventType` enum value in `backend/api/models/event.py`
3. Define `InfoModel` inner class with validation fields
4. Implement `get_event_type()`, `get_tx_collections()`, `apply()` methods
5. (Optional) Add route handler in `backend/api/endpoints/[domain].py`

**Shared Utilities (Reusable):**
- **Python:** `backend/api/utils/` (organize by domain or cross-cutting concern)
- **JavaScript:** `webapps/main/src/composables/` (Vue composables) or `webapps/main/src/lib/` (utility libraries)

**Configuration:**
- **Backend:** `backend/api/utils/config.py` (load from environment)
- **Frontend:** `webapps/main/src/stores/config.js` (Pinia store) or env vars in `quasar.conf.js`

## Special Directories

**backend/api/events/:**
- Purpose: Immutable event-sourcing log
- Generated: No (manually created)
- Committed: Yes (part of source)
- Notes: Event classes must declare collections in `get_tx_collections()`, implement `apply()` method

**webapps/main/src/views/:**
- Purpose: Feature-specific page views (57 subdirectories)
- Generated: No
- Committed: Yes
- Notes: Often contain multiple sub-components; mirror router structure

**db/migrations/:**
- Purpose: Database schema versioning
- Generated: No (manually created)
- Committed: Yes
- Notes: Immutable; never modify once numbered; run by deployment scripts

**deploy/compose/:**
- Purpose: Docker orchestration configuration
- Generated: No (manually maintained)
- Committed: Yes
- Notes: Base configs in base.yaml; feature/env overrides in feature files

**backend/api/managers/:**
- Purpose: System-wide resource singletons
- Generated: No
- Committed: Yes
- Notes: Typically implement getInstance() pattern; manage lifecycle (startup/shutdown)

**webapps/main/src/store/ vs webapps/main/src/stores/:**
- `store/` - Vuex store (legacy, being phased out)
- `stores/` - Pinia stores (modern, preferred)
- Migration: Move state to Pinia when refactoring components

---

*Structure analysis: 2026-02-13*
