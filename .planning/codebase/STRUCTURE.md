# Codebase Structure

**Analysis Date:** 2026-05-08

## Directory Layout

```
progress-platform/
├── backend/                    # Backend services (Python)
│   ├── api/                    # FastAPI main application (event-driven REST API)
│   ├── sparkplug_bridge/       # MQTT → NATS Sparkplug B ingestion service
│   ├── workflow/               # Prefect workflow orchestration engine
│   ├── reports/                # Report generation (legacy, deprecated)
│   ├── print-service/          # Print job microservice
│   ├── commons/                # Shared Python utilities
│   ├── mock/                   # Mock data generators for testing
│   ├── lte/                    # Long-term evolution (unused)
│   ├── tests/                  # Legacy test directory (deprecated)
│   └── scripts/                # Database initialization and utility scripts
├── webapps/                    # Frontend applications (Vue3/Quasar)
│   ├── main/                   # Desktop SPA (Quasar 2)
│   └── warehouse/              # Mobile app (Quasar + Capacitor)
├── testing/                    # Modern automated test suites
│   ├── pytest/                 # Backend integration tests (testcontainers + ArangoDB)
│   ├── playwright/             # E2E frontend tests (Chromium, Firefox, WebKit)
│   └── locust/                 # Load testing (HTTP, WebSocket)
├── deploy/                     # Docker Compose and deployment configuration
│   ├── compose/                # Docker Compose definitions (base, dev, stack, sparkplug, etc.)
│   ├── config/                 # Runtime configuration (app config, NATS server config)
│   ├── secrets/                # Secret template files (not committed)
│   ├── dashboards/             # Grafana dashboard definitions
│   ├── scripts/                # Deployment scripts and Streamlit reports
│   └── artifacts/              # Build artifacts and container images
├── cli/                        # Command-line tools (Python)
├── db/                         # Database artifacts and migrations
│   ├── migrations/             # ArangoDB schema migrations
│   ├── backup/                 # Database backup files
│   ├── scripts/                # Database utility scripts
│   └── Data Architecture/      # ER diagrams and schema documentation
├── km/                         # Knowledge management (markdown docs)
│   ├── domains/                # Domain-specific documentation (production, inventory, serial)
│   ├── architecture/           # Architecture notes
│   ├── auth/                   # Authentication and authorization docs
│   └── testing/                # Testing strategy and patterns
├── docs/                       # Documentation site (Docusaurus or similar)
│   ├── api/                    # API reference docs
│   ├── events/                 # Event taxonomy and schemas
│   ├── manual/                 # User manual
│   ├── admin/                  # Administration guides
│   └── reference/              # Reference materials
├── scripts/                    # Utility scripts (ad-hoc, setup, etc.)
├── testing/                    # Test configuration and fixtures (see above for detail)
├── .planning/                  # GSD artifacts (workstreams, phases, decisions)
│   ├── codebase/              # Codebase mapping documents (ARCHITECTURE.md, STRUCTURE.md, etc.)
│   └── workstreams/           # Workstream definitions (sparkplug-demo, etc.)
├── .worktrees/                 # Git worktrees for parallel GSD sessions (gitignored)
├── graphify-out/               # Knowledge graph output (graphify cache, wiki) (gitignored)
├── media/                      # File storage volume (attachments, media files)
├── files/                      # File storage volume (uploads, logs, backups)
├── nats_data/                  # NATS JetStream persistence volume
├── workflow_db/                # PostgreSQL data volume (Prefect state)
├── integration_db/             # Test integration database volume (gitignored)
├── cmounts/                    # Container mount points (gitignored)
├── node_modules/               # Node.js dependencies (gitignored)
├── docker-compose.yml          # Main Docker Compose file
├── .env                        # Environment variables (gitignored)
├── .env.example                # Environment template (tracked)
└── package.json                # Root workspace package.json (if monorepo)
```

## Directory Purposes

**`backend/api/`:**
- Purpose: FastAPI REST API server, main entry point for all client requests
- Contains: HTTP endpoints, event system, data models, utilities, middleware
- Key files: `main.py` (app initialization), `endpoints/` (route handlers), `events/` (event classes), `models/` (Pydantic schemas), `utils/` (query helpers, NATS client, auth)

**`backend/api/endpoints/`:**
- Purpose: HTTP route handlers organized by domain
- Contains: 22 route files (production.py, inventory.py, serial.py, collaboration.py, counting.py, auth.py, org.py, etc.)
- Imports: Event classes from `events/`, models from `models/`, utilities from `utils/`

**`backend/api/events/`:**
- Purpose: Event sourcing layer with immutable business logic
- Contains: 50+ event types organized in 6 domain folders (production/, inventory/, serial/, collaboration/, admin/, wip/, work_session/)
- Each event: Defines InfoModel, implements get_event_type(), get_tx_collections(), apply()

**`backend/api/models/`:**
- Purpose: Pydantic data validation schemas
- Contains: `event.py` (EventType enum, EventInfoModel, EventModel), domain models (production.py, inventory.py, serial.py, etc.), request/response models

**`backend/api/utils/`:**
- Purpose: Shared utilities and domain query helpers
- Contains: `db.py` (ArangoDB singleton), `nats_client.py` (NATS wrapper), `auth.py` (JWT), `config.py` (settings), domain query classes (production.py, inventory.py, serial.py, etc.)

**`backend/api/managers/`:**
- Purpose: Singleton manager services
- Contains: `server_event_manager.py` (SSE notification delivery)

**`backend/api/middlewares/`:**
- Purpose: ASGI middleware for request/response processing
- Contains: `gzipfilter_middleware.py` (selective GZip compression, excludes SSE)

**`backend/sparkplug_bridge/`:**
- Purpose: Sparkplug B ingestion service (MQTT → NATS bridge)
- Contains: `main.py` (asyncio entrypoint), `decoder.py` (protobuf), `session_state.py` (state machine), `host_state.py` (heartbeat), `publisher.py` (NATS pub), `kv_store.py` (KV buckets), `heartbeat.py` (periodic heartbeat), `subscriber.py` (MQTT subscribe)

**`backend/workflow/flows/`:**
- Purpose: Prefect flow definitions (system and integration workflows)
- Contains: `flowcode/` (flow implementations), `deployments/` (deployment manifests), `sys_loader.py` (flow registration)

**`webapps/main/src/`:**
- Purpose: Desktop SPA (Vue3/Quasar framework)
- Contains: `pages/`, `components/`, `stores/` (Pinia state), `composables/`, `router/`, `boot/` (app initialization), `assets/`, `css/`

**`webapps/warehouse/src/`:**
- Purpose: Mobile app (Quasar + Capacitor for native iOS/Android)
- Contains: `pages/`, `components/`, `stores/`, `composables/`, `router/`, similar structure to main but with mobile-specific plugins (Capacitor camera, barcode reader)

**`testing/pytest/`:**
- Purpose: Backend integration tests with real ArangoDB (via testcontainers)
- Contains: `tests/` (organized by domain: production/, inventory/, serial/, batch/, movement/, step/, etc.), `conftest.py` (pytest fixtures), `conftest_helpers/` (fixture utilities)

**`testing/playwright/`:**
- Purpose: E2E frontend tests (Chromium, Firefox, WebKit)
- Contains: Page objects, test scenarios, config files

**`testing/locust/`:**
- Purpose: Load/performance testing
- Contains: Load test definitions (HTTP, WebSocket load profiles)

**`deploy/compose/`:**
- Purpose: Docker Compose definitions for different environments
- Contains: `base.yaml` (core services: Traefik, API, DB, NATS), `dev.yaml` (dev overrides), `stack.yaml` (full stack with all services), `sparkplug.yaml` (Sparkplug bridge + MQTT), `workflow.yaml` (Prefect), `reporting.yaml` (Streamlit), `warehouse.yaml` (warehouse app), `print.yaml` (print service), `tls.yaml` (TLS config)

**`deploy/config/`:**
- Purpose: Runtime configuration files
- Contains: `appConfig.js` (injected into webapp at runtime), NATS server config, environment templates

**`deploy/scripts/`:**
- Purpose: Deployment utilities and Streamlit reports
- Contains: Streamlit app definitions (embedded in webapp via `/reports` endpoint), setup scripts

**`db/migrations/`:**
- Purpose: ArangoDB schema migrations
- Contains: Migration scripts (versioned) for collections, indices, initial data

**`km/domains/`:**
- Purpose: Domain-specific knowledge documentation
- Contains: `production/`, `inventory/`, `serial/`, `wip/` subdirectories with markdown docs explaining domain concepts, data flow, event lifecycle

**`.planning/codebase/`:**
- Purpose: GSD codebase mapping documents
- Contains: `ARCHITECTURE.md`, `STRUCTURE.md`, `CONVENTIONS.md`, `TESTING.md`, `STACK.md`, `INTEGRATIONS.md`, `CONCERNS.md`

**`.planning/workstreams/`:**
- Purpose: Workstream definitions (multi-phase features)
- Contains: Per-workstream directories (e.g., `sparkplug-demo/`) with `decisions/`, `phases/`, `PROJECT.md`, `STATE.md`, `ROADMAP.md`

## Key File Locations

**Entry Points:**
- `backend/api/main.py` - FastAPI app initialization, route registration, startup/shutdown hooks
- `backend/sparkplug_bridge/main.py` - Sparkplug service asyncio entrypoint
- `webapps/main/src/App.vue` - Main SPA root component
- `webapps/warehouse/src/App.vue` - Warehouse app root component
- `backend/workflow/flows/sys_loader.py` - Prefect flow registry loader

**Configuration:**
- `backend/api/utils/config.py` - API settings (env vars with pydantic-settings)
- `backend/sparkplug_bridge/config.py` - Sparkplug bridge settings
- `deploy/config/appConfig.js` - Frontend app config (injected at runtime)
- `webapps/main/quasar.config.js` - Quasar build and boot configuration
- `webapps/warehouse/quasar.config.js` - Warehouse app build configuration
- `docker-compose.yml` - Root compose file (imports from deploy/compose/)

**Core Logic:**
- `backend/api/events/base_event.py` - Event base class and transaction lifecycle
- `backend/api/models/event.py` - EventType enum (registry of all event types)
- `backend/api/utils/nats_client.py` - NATS publish/subscribe client wrapper
- `backend/api/utils/db.py` - ArangoDB connection singleton
- `backend/api/utils/auth.py` - JWT token verification and claims extraction

**Testing:**
- `testing/pytest/conftest.py` - pytest fixtures (DB setup, testcontainers, factories)
- `testing/pytest/tests/conftest.py` - per-test-module fixtures
- `testing/pytest/tests/factories/` - Factory classes for creating test data
- `testing/pytest/tests/infrastructure/` - Infrastructure fixtures (test containers, cleanup)
- `testing/playwright/` - E2E test setup and page object models

## Naming Conventions

**Files:**
- Python: `snake_case.py` (e.g., `step_completed.py`, `server_event_manager.py`)
- Vue: `PascalCase.vue` for components (e.g., `StepExecutionCard.vue`, `ProductionPage.vue`)
- JavaScript/TypeScript: `camelCase.js` or `camelCase.ts` for utilities and composables
- Markdown: `UPPERCASE.md` for documentation (e.g., `ARCHITECTURE.md`, `README.md`)

**Directories:**
- Python packages: `lowercase` with underscores if needed (e.g., `events/production/`, `utils/`)
- Vue components: Organized by page or feature (e.g., `components/production/`, `components/shared/`)
- Feature directories: Descriptive names (e.g., `endpoints/`, `managers/`, `composables/`)

**Classes:**
- Python: `PascalCase` (e.g., `StepCompletedEvent`, `ProductionQueries`, `ServerEventManager`)
- TypeScript/Vue: `PascalCase` for components and classes
- Pydantic models: `PascalCase` (e.g., `Job`, `Batch`, `Step`, `EventInfoModel`)

**Functions & Variables:**
- Python: `snake_case` (e.g., `get_job_data()`, `process_batch()`)
- JavaScript: `camelCase` (e.g., `getJobData()`, `processBatch()`)

**Constants:**
- Python: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- Enum values: Used as-is (e.g., `EventType.STEP_COMPLETED`)

## Where to Add New Code

**New API Endpoint:**
1. Create route handler in `backend/api/endpoints/{domain}.py` (or new file if new domain)
2. Create Pydantic request/response models in `backend/api/models/{domain}.py` (if needed)
3. Create Event class in `backend/api/events/{domain}/{event_name}.py` (if mutation)
4. Add query helper to `backend/api/utils/{domain}.py` (if needed)
5. Import router in `backend/api/endpoints/__init__.py`
6. Include router in `backend/api/main.py` line 112-132

**New Event Type:**
1. Create file in `backend/api/events/{domain}/{event_name}.py`
2. Subclass `BaseEvent`
3. Define `InfoModel` (Pydantic)
4. Implement `get_event_type()`, `get_tx_collections()`, `apply()`
5. Optional: override `pre_processing()`, `post_processing()`, `_build_event_payload()`
6. Register in `backend/api/models/event.py` EventType enum
7. Import and export in `backend/api/events/__init__.py`

**New Vue Component:**
1. Create file in `webapps/main/src/components/{feature}/{ComponentName}.vue` or `webapps/warehouse/src/components/{feature}/{ComponentName}.vue`
2. Use `<script setup>` with Composition API (preferred)
3. Import utilities, stores, composables as needed
4. Follow Prettier format (configured in `.prettierrc.json`)
5. Run ESLint: `npm run lint`

**New Composable (Vue3):**
1. Create file in `webapps/main/src/composables/use{Name}.js` (or descriptive name)
2. Export composable function
3. Import in component via `<script setup>`

**New Store (Pinia):**
1. Create file in `webapps/main/src/stores/{name}Store.js` (new preferred approach)
2. Avoid adding to `webapps/main/src/store/` (legacy Vuex — deprecated)

**New Test (Pytest):**
1. Create file in `testing/pytest/tests/{domain}/test_{feature}.py`
2. Use factories from `testing/pytest/tests/factories/`
3. Use fixtures from `conftest.py` (DB, testcontainers, auth)
4. Follow AAA pattern (Arrange, Act, Assert)
5. Run: `uv run pytest tests/{domain}/test_{feature}.py`

**New Test (Playwright):**
1. Create file in `testing/playwright/tests/test_{feature}.spec.ts`
2. Use Page Object Model pattern
3. Use fixtures from `conftest.ts` or custom fixtures
4. Run: `npx playwright test tests/test_{feature}.spec.ts`

**New Streamlit Report:**
1. Create file in `deploy/scripts/{report_name}.py`
2. Import as Python module from main app (`/reports` endpoint)
3. Application iframes the report at `http://localhost:8501/`

**New Workflow (Prefect):**
1. Create directory in `backend/workflow/flows/flowcode/{workflow_name}/`
2. Create `code.py` with flow definition using Prefect 3 syntax
3. Flow is auto-registered by `sys_loader.py` during deployment
4. Reference in UI as "System workflow" or manually manage as "Integration workflow"

## Special Directories

**`media/`, `files/`, `nats_data/`, `workflow_db/`, `integration_db/`:**
- Purpose: Docker volumes for persistent storage
- Generated: Yes (created by Docker Compose on `docker-compose up`)
- Committed: No (gitignored)
- Use: `media/` stores file uploads, `files/` stores logs/backups, `nats_data/` stores NATS JetStream data, `workflow_db/` is PostgreSQL data volume for Prefect, `integration_db/` is test database

**`.planning/`:**
- Purpose: GSD orchestration artifacts (workstreams, phases, decision records)
- Generated: Yes (by GSD commands)
- Committed: Yes (tracked in git)
- Structure: `.planning/config.json` (GSD metadata), `.planning/codebase/` (codebase maps), `.planning/workstreams/` (per-workstream artifacts)

**`.worktrees/`:**
- Purpose: Git worktrees for parallel GSD sessions
- Generated: Yes (by GSD or manual `git worktree add`)
- Committed: No (gitignored)
- Use: Each session works on a `feature/{short-name}` branch with defined file-ownership scope

**`graphify-out/`:**
- Purpose: Knowledge graph output (cached knowledge, wiki)
- Generated: Yes (by `/graphify` command)
- Committed: No (gitignored)
- Use: Read by GSD codebase mapper to understand god nodes and community structure

**`node_modules/`, `__pycache__/`, `.hypothesis/`:**
- Purpose: Dependency and cache directories
- Generated: Yes
- Committed: No (gitignored)

---

*Structure analysis: 2026-05-08*
