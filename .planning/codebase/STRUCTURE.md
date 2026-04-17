# Codebase Structure

**Analysis Date:** 2026-04-15

## Directory Layout

```
progress-platform/
├── backend/                # All backend services
│   ├── api/                # Main FastAPI application (core)
│   └── workflow/           # Prefect 3.x workflow engine
├── webapps/                # Frontend applications
│   ├── main/               # Primary MES desktop app (Vue3/Quasar SPA)
│   └── warehouse/          # Warehouse mobile app (Vue3/Quasar + Capacitor)
├── deploy/                 # Infrastructure and deployment
│   ├── compose/            # Docker Compose stack files
│   ├── config/             # Service configuration (appConfig.js, etc.)
│   ├── dashboards/         # ArangoDB monitoring views
│   ├── artifacts/          # Build artifacts
│   └── scripts/            # Deployment helper scripts
├── testing/                # Legacy test suites (Cypress, Robot Framework)
├── db/                     # Database definitions and migrations
│   ├── migrations/         # DB migration scripts
│   ├── scripts/            # DB utility scripts
│   ├── backup/             # DB backups
│   └── Data Architecture/  # Data model documentation
├── cli/                    # CLI tools
├── files/                  # Local file storage
├── media/                  # Media file storage (Docker volume mount)
├── km/                     # Knowledge management docs
└── .planning/              # GSD planning documents
    └── codebase/           # Codebase map documents (this file)
```

## Directory Purposes

### Backend API (`backend/api/`)

```
backend/api/
├── main.py                 # FastAPI app entry point, routers, middleware, NATS lifecycle
├── endpoints/              # Route handlers (one file per domain, 20 modules)
│   ├── __init__.py         # Imports all routers for main.py registration
│   ├── production.py       # Work orders, jobs, batches, steps (26KB)
│   ├── process.py          # Process definition management (21KB)
│   ├── counting.py         # Inventory counting sessions (20KB)
│   ├── product.py          # Product/BOM management (15KB)
│   ├── serial.py           # Serial number management (13KB)
│   ├── inventory.py        # Warehouse movements (13KB)
│   ├── traceability.py     # DHR, traceability queries (12KB)
│   ├── collaboration.py    # Issues, messages, tasks (10KB)
│   ├── auth.py             # Login, session, JWT (8KB)
│   ├── print.py            # Print template management (7KB)
│   ├── org.py              # Organization settings (9KB)
│   ├── admin.py            # Admin operations (5KB)
│   ├── form.py             # Form field management (5KB)
│   ├── file.py             # File upload/download (5KB)
│   ├── config.py           # System configuration (4KB)
│   ├── bom.py              # Bill of materials (3KB)
│   ├── media.py            # Media file endpoints (3KB)
│   ├── tag.py              # Tagging system (3KB)
│   ├── counter.py          # Counter management (2KB)
│   └── notification.py     # SSE notification stream (0.5KB)
├── events/                 # Domain event classes (60+ events)
│   ├── base_event.py       # BaseEvent ABC (transaction lifecycle, NATS publish)
│   ├── __init__.py         # Auto-registers all event classes on import
│   ├── production/         # 16 files: StepCompleted, BatchCompleted, JobStarted, etc.
│   │   ├── base_production.py  # Shared production event logic
│   │   ├── commons/        # Shared helpers for production events
│   │   ├── step_completed.py
│   │   ├── batch_completed.py
│   │   ├── job_started.py
│   │   ├── job_closed.py
│   │   └── ...
│   ├── inventory/          # 23 files: movements, counting, warehouse lists
│   │   ├── base_inventory.py
│   │   ├── movement_completed.py
│   │   ├── count_session_applied.py
│   │   └── ...
│   ├── collaboration/      # 17 files: issues, tasks, messages
│   │   ├── base_collaboration.py
│   │   ├── issue_created.py
│   │   ├── task_completed.py
│   │   └── ...
│   ├── serial/             # 8 files: serial CRUD and linking
│   │   ├── base_serial.py
│   │   ├── serial_created.py
│   │   └── ...
│   ├── wip/                # 4 files: WIP booking/removal
│   ├── work_session/       # 3 files: work session lifecycle
│   └── admin/              # 6 files: admin overrides and resets
├── managers/               # Singleton services
│   ├── server_event_manager.py  # SSE fan-out (per-topic async queues)
│   └── __init_.py          # (empty, note: typo in actual filename)
├── models/                 # Pydantic models (20 files)
│   ├── event.py            # EventType enum, EventInfoModel, EventModel
│   ├── production.py       # Job, Batch, WorkOrder models
│   ├── collaboration.py    # Issue, Task, Message models
│   ├── serial.py           # Serial number models
│   ├── print.py            # Print template models
│   ├── base_models.py      # Shared base model definitions
│   ├── inventory/          # Inventory-specific models (subdirectory)
│   └── ...                 # bom, company, config, counter, document, form, org, etc.
├── middlewares/            # Custom middleware
│   └── gzipfilter_middleware.py  # Conditional GZip (excludes /notification)
└── utils/                  # Shared utilities (~28 files)
    ├── db.py               # ArangoDB client singleton
    ├── config.py           # Settings via pydantic-settings
    ├── auth.py             # JWT verification (13KB)
    ├── nats_client.py      # NATS connection, publish/subscribe
    ├── event.py            # Event class registry/lookup
    ├── production.py       # Production AQL queries (20KB)
    ├── inventory.py        # Inventory AQL queries (20KB)
    ├── serial.py           # Serial AQL queries (14KB)
    ├── dhr.py              # Device History Record generation (44KB, largest file)
    ├── traceability.py     # Traceability queries (12KB)
    ├── collaboration.py    # Issue/task queries (12KB)
    ├── process.py          # Process definition queries (7KB)
    ├── counter.py          # Auto-incrementing counter generation
    ├── bom.py              # BOM queries
    ├── product.py          # Product queries
    ├── kpi.py              # KPI calculations
    ├── search.py           # Search utilities
    ├── file.py             # File handling
    ├── media.py            # Media handling
    ├── exceptions.py       # Custom exception classes (HTTPError)
    ├── api.py              # APIResponse helper
    ├── dt.py               # Date/time utilities
    ├── org.py              # Organization utilities
    ├── print.py            # Print utilities
    ├── api_auth_manager.py # API auth management
    └── delayedqueue/       # Delayed queue utilities (subdirectory)
```

### Backend Workflow (`backend/workflow/`)

```
backend/workflow/
├── Dockerfile              # Prefect worker container
├── requirements.txt        # python-arango, httpx
├── flows/
│   ├── flowcode/
│   │   ├── apply_inventory_counts.py   # Apply count session results
│   │   ├── cleanup_disposable_positions.py  # Clean temp positions
│   │   └── pause_offline_jobs.py       # Auto-pause stale jobs
│   └── deployments/        # Prefect deployment configs
├── integration_db/         # DB integration helpers
├── sys_loader.py           # System path loader for imports
└── utils.py                # Shared workflow utilities
```

### Main Webapp (`webapps/main/`)

```
webapps/main/src/
├── App.vue                 # Root Vue component
├── boot/                   # Quasar boot files (initialization order matters)
│   ├── axios.js            # Axios instance + auth interceptor + 401 handling
│   ├── store.js            # Vuex store initialization
│   ├── pinia.js            # Pinia store initialization
│   ├── i18n.js             # Vue I18n setup
│   ├── theme.js            # Theme initialization
│   ├── filters.js          # Global Vue filters
│   ├── form.js             # Form boot
│   └── registerRouter.js   # Router registration
├── router/                 # Vue Router configuration
│   ├── routes.js           # Root route tree (imports all sub-routes)
│   ├── index.js            # Router instance + navigation guards
│   ├── adminRoutes.js      # Admin section routes
│   ├── productionRoutes.js # Production routes
│   ├── warehouseRoutes.js  # Warehouse section routes
│   ├── traceabilityRoutes.js
│   ├── operatorRoutes.js   # Operator view routes
│   ├── libraryRoutes.js    # Library/settings routes
│   ├── qualityRoutes.js
│   ├── taskRoutes.js
│   └── reportRoutes.js
├── store/                  # Vuex store (legacy, 13 modules)
│   ├── index.js            # Store root + session persistence
│   ├── session.js          # Auth, login, session lock
│   ├── product.js          # Product state
│   ├── process.js          # Process definitions
│   ├── job.js              # Job state
│   ├── warehouse.js        # Warehouse state
│   ├── traceability.js     # Traceability state
│   ├── serial.js           # Serial state
│   ├── workorder.js        # Work order state
│   ├── quality.js          # Quality state
│   ├── bom.js              # BOM state
│   ├── form.js             # Form state
│   ├── org.js              # Organization state
│   └── user.js             # User state
├── stores/                 # Pinia stores (newer, 4 stores)
│   ├── config.js           # System configuration
│   ├── countSession.js     # Count session management (22KB)
│   ├── task.js             # Task management
│   └── taskType.js         # Task type definitions
├── views/                  # Page-level view components
│   ├── MainLayout.vue      # App shell layout (sidebar, header)
│   ├── LoginScreen.vue     # Login page
│   ├── ProductionOverview.vue  # Production dashboard
│   ├── ProductHome.vue     # Product detail (29KB, largest view)
│   ├── TaskScreen.vue      # Task detail screen (35KB)
│   ├── TaskOverview.vue    # Task list
│   ├── QualityRoot.vue     # Quality section root
│   ├── settings/           # Settings views
│   │   ├── GeneralSettings.vue
│   │   ├── counter/        # Counter settings
│   │   └── printers/       # Printer settings
│   ├── traceability/       # Traceability views
│   │   └── TraceabilityRoot.vue
│   └── warehouse/          # Warehouse views
│       ├── WarehouseRoot.vue
│       ├── counting/       # Count session views
│       ├── inventory/      # Inventory views
│       ├── lists/          # Warehouse list views
│       ├── movements/      # Movement views
│       └── positions/      # Position views
├── components/             # Reusable UI components
│   ├── Base*.vue           # Base components (15+ Base-prefixed)
│   │   ├── BaseAutocomplete*.vue  # Domain-specific autocompletes (12 variants)
│   │   ├── BaseDialog.vue
│   │   ├── BaseModalForm.vue
│   │   ├── BaseModalScreen.vue
│   │   ├── BaseConfirmationDialog.vue
│   │   └── ...
│   ├── job/                # Job-specific components
│   ├── workorderscreen/    # Work order screen components
│   ├── process-steps/      # Process step editor components
│   │   ├── ProcessSteps.vue
│   │   ├── StepForm.vue
│   │   ├── counters/       # Counter components
│   │   └── printers/       # Printer components
│   ├── traceability/       # Serial/traceability components
│   │   ├── SerialDetail.vue
│   │   ├── SerialForm.vue
│   │   ├── SerialTree.vue
│   │   └── ...
│   ├── warehouse/          # Warehouse components
│   │   ├── counting/
│   │   ├── inventory/
│   │   ├── movement/
│   │   └── position/
│   ├── settings/           # Settings components
│   │   ├── APITokenLibrary.vue
│   │   └── SerialFieldLibrary.vue
│   ├── AppBar.vue          # Top navigation bar
│   ├── AppFooter.vue       # Footer
│   ├── FilterDrawer.vue    # Filter sidebar
│   └── EntityPicker.vue    # Generic entity picker
├── composables/            # Vue 3 composition functions
│   ├── useSSE.js           # SSE subscription (ref-counted EventSource)
│   ├── usePrefectAPI.js    # Prefect API integration
│   ├── useCountRecordAggregation.js  # Count record aggregation (19KB)
│   ├── useCountRecordExport.js       # Count record export
│   ├── useCountRecordFilters.js      # Count record filtering
│   ├── useUncountedInventory.js      # Uncounted inventory tracking
│   ├── warehouse.js        # Warehouse composable (11KB)
│   ├── productionAdminActions.js     # Admin action composable (20KB)
│   ├── taskNavigation.js   # Task navigation
│   ├── event.js            # sendEvent() for user action tracking
│   ├── reStore.js          # Store restoration utilities
│   ├── traceability.js     # Traceability composable
│   ├── task.js             # Task composable
│   ├── form.js             # Form utilities
│   ├── drawer.js           # Drawer state
│   ├── print-template.js   # Print template utilities
│   ├── theme.js            # Theme utilities
│   ├── useCSSVars.js       # CSS variable injection
│   └── useWildcardToRegex.js  # Wildcard pattern matching
├── lib/                    # Utility libraries
│   ├── print/              # Print-related utilities
│   ├── queryModelFactory.js # Dynamic query model builder
│   ├── dateUtils.js        # Date formatting
│   ├── duration.js         # Duration formatting
│   ├── xlsxDownload.js     # Excel export
│   ├── media.js            # Media helpers
│   ├── apiCall.js          # API call wrapper
│   ├── appRouter.js        # Router access
│   ├── loadScript.js       # Dynamic script loading
│   └── ...
├── mixins/                 # Vue mixins (legacy)
│   ├── form.js             # Form mixin
│   ├── issues.js           # Issues mixin
│   ├── CSSVars.js          # CSS vars mixin
│   ├── NonExistentOperationGuard.js
│   └── NonExistentUserGuard.js
├── types/                  # TypeScript type definitions
│   └── form.d.ts           # Form field types
├── i18n/                   # Internationalization files
├── assets/                 # Static assets (images, icons)
└── css/                    # Global stylesheets
```

### Warehouse Webapp (`webapps/warehouse/`)

```
webapps/warehouse/src/
├── App.vue
├── boot/                   # Quasar boot files
├── router/                 # Vue Router
├── store/                  # Vuex (legacy, 2 modules: index.js, session.js)
├── stores/                 # Pinia stores (7 stores)
│   ├── config.js
│   ├── counting.js
│   ├── incoming.js
│   ├── inventory.js
│   ├── lists.js
│   ├── navigation.js
│   ├── shipment.js
│   └── transfer.js
├── views/                  # Page views
│   ├── MainLayout.vue
│   ├── LoginScreen.vue
│   ├── incoming/           # Incoming goods views
│   ├── inventory/          # Inventory views
│   ├── lists/              # Warehouse list views
│   ├── shipment/           # Shipment views
│   ├── transfering/        # Transfer views
│   └── warehouse/          # Warehouse root
├── components/             # Reusable components
│   ├── barcode-reader/     # Barcode/QR scanning (ZXing)
│   ├── counting/           # Count session components
│   ├── incoming/           # Incoming goods components
│   ├── lists/              # List components
│   ├── print/              # Print components
│   ├── shipment/           # Shipment components
│   ├── transfer/           # Transfer components
│   ├── AppBar.vue
│   ├── AppFooter.vue
│   ├── SearchOrScan.vue    # Scan-or-type input
│   └── QuantitySelector.vue
├── composables/            # Vue composables
├── mixins/                 # Legacy mixins
├── lib/                    # Utilities
├── i18n/                   # Translations
├── assets/                 # Static assets
└── css/                    # Styles
```

### Deploy (`deploy/`)

```
deploy/
├── compose/                # Docker Compose stack files
│   ├── base.yaml           # Core services (API, DB, Traefik)
│   ├── stack.yaml          # Full production stack
│   ├── dev.yaml            # Development overrides
│   ├── tls.yaml            # TLS/HTTPS configuration
│   ├── workflow.yaml       # Prefect + PostgreSQL
│   ├── warehouse.yaml      # Warehouse app
│   ├── reporting.yaml      # Reporting services
│   ├── integration.yaml    # Integration services
│   ├── print.yaml          # Print services
│   └── notebooks.yaml      # Jupyter notebooks
├── config/                 # Service configuration files
├── dashboards/             # ArangoDB monitoring views
├── scripts/                # Deployment helper scripts
├── artifacts/              # Build artifacts
├── single_node_setup.yaml  # Single-node deployment config
└── single_node_setup_local.yaml  # Local deployment config
```

## Key File Locations

**Entry Points:**
- `backend/api/main.py`: FastAPI application, router registration, NATS lifecycle
- `webapps/main/src/App.vue`: Main webapp root component
- `webapps/warehouse/src/App.vue`: Warehouse app root component
- `backend/workflow/flows/flowcode/*.py`: Prefect scheduled flows

**Configuration:**
- `backend/api/utils/config.py`: Backend settings (pydantic-settings, `PROGRESS_` prefix)
- `deploy/config/appConfig.js`: Frontend API config (`window.API_CONFIG`)
- `webapps/main/quasar.config.js`: Quasar framework config
- `webapps/main/.eslintrc.js`: ESLint configuration
- `webapps/main/.prettierrc.json`: Prettier configuration
- `.gitlab-ci.yml`: CI/CD pipeline
- `db/arango.conf`: ArangoDB configuration

**Core Business Logic:**
- `backend/api/events/base_event.py`: Event system foundation
- `backend/api/events/__init__.py`: Event auto-registration
- `backend/api/models/event.py`: EventType enum + EventInfoModel
- `backend/api/utils/production.py`: Production domain queries
- `backend/api/utils/inventory.py`: Inventory domain queries
- `backend/api/utils/dhr.py`: Device History Record (largest single file, 44KB)

**Authentication:**
- `backend/api/utils/auth.py`: JWT verification and user resolution
- `webapps/main/src/boot/axios.js`: Axios auth interceptor
- `webapps/main/src/store/session.js`: Session state (Vuex)

**Real-Time:**
- `backend/api/utils/nats_client.py`: NATS pub/sub client
- `backend/api/managers/server_event_manager.py`: SSE fan-out manager
- `backend/api/endpoints/notification.py`: SSE endpoint
- `webapps/main/src/composables/useSSE.js`: Frontend SSE subscription

## Naming Conventions

**Files:**
- Backend Python: `snake_case.py` (e.g., `step_completed.py`, `base_event.py`)
- Vue components: `PascalCase.vue` (e.g., `ProductHome.vue`, `BaseDialog.vue`)
- Composables: `use{Name}.js` or descriptive `camelCase.js` (e.g., `useSSE.js`, `warehouse.js`)
- Stores (Pinia): `camelCase.js` (e.g., `countSession.js`, `taskType.js`)
- Route files: `{domain}Routes.js` (e.g., `productionRoutes.js`)

**Directories:**
- Backend: `snake_case/` (e.g., `work_session/`, `base_event.py`)
- Frontend: `kebab-case/` for component groups (e.g., `process-steps/`, `barcode-reader/`)
- Frontend: `lowercase/` for domain sections (e.g., `counting/`, `inventory/`)

## Where to Add New Code

**New Backend Endpoint:**
- Create route handler: `backend/api/endpoints/{domain}.py`
- Register router in `backend/api/endpoints/__init__.py`
- Include router in `backend/api/main.py` with `app.include_router()`

**New Domain Event:**
- Create event class: `backend/api/events/{domain}/{event_name}.py`
- Inherit from domain base (e.g., `BaseProductionEvent`) or `BaseEvent`
- Define inner `InfoModel(EventInfoModel)` with domain fields
- Implement `get_event_type()`, `get_tx_collections()`, `apply()`
- Add `EventType` entry to `backend/api/models/event.py`
- Import in `backend/api/events/__init__.py` (auto-registered)

**New Pydantic Model:**
- Add to existing domain file: `backend/api/models/{domain}.py`
- Or create new file and add to models directory

**New Vue View/Page (Main App):**
- Create view: `webapps/main/src/views/{ViewName}.vue`
- Add route in appropriate route file: `webapps/main/src/router/{domain}Routes.js`
- Use `<script setup>` with Composition API

**New Vue Component (Main App):**
- Reusable: `webapps/main/src/components/{ComponentName}.vue`
- Domain-specific: `webapps/main/src/components/{domain}/{ComponentName}.vue`
- Base/generic: prefix with `Base` (e.g., `BaseAutocompleteProduct.vue`)

**New Composable:**
- Create: `webapps/main/src/composables/use{Name}.js`
- Export named function: `export function use{Name}() { ... }`

**New Pinia Store:**
- Create: `webapps/main/src/stores/{storeName}.js`
- Do NOT add to Vuex (`webapps/main/src/store/`) -- legacy

**New Utility (Backend):**
- Add query helpers: `backend/api/utils/{domain}.py`
- Add shared helper: `backend/api/utils/{name}.py`

**New Warehouse Feature:**
- Pinia store: `webapps/warehouse/src/stores/{feature}.js`
- Views: `webapps/warehouse/src/views/{feature}/`
- Components: `webapps/warehouse/src/components/{feature}/`

## Special Directories

**`media/`:**
- Purpose: User-uploaded files (attachments, images)
- Generated: Yes (runtime uploads)
- Committed: No (Docker volume, `.gitignore`)

**`files/`:**
- Purpose: Local file storage
- Generated: Yes
- Committed: No

**`db/migrations/`:**
- Purpose: ArangoDB migration scripts
- Generated: No (manually authored)
- Committed: Yes

**`testing/`:**
- Purpose: Legacy test suites (Cypress, Robot Framework)
- Note: Being replaced by pytest + Vitest + Playwright unified stack
- Committed: Yes

**`km/`:**
- Purpose: Knowledge management documentation
- Committed: Yes

**`.planning/`:**
- Purpose: GSD workflow planning artifacts
- Committed: Partial (codebase maps yes, debug artifacts no)

---

*Structure analysis: 2026-04-15*
