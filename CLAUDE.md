<!-- GSD:project-start source:PROJECT.md -->
## Project

**Progress Platform Test Suite**

A comprehensive automated test suite for the Progress Platform — a manufacturing execution system (MES) built on FastAPI + ArangoDB + Vue 3/Quasar. The project replaces the existing fragmented testing approach (Mocha/Cypress/Robot Framework) with a modern, unified stack: pytest with testcontainers for backend, Vitest + Playwright for frontend, Schemathesis for API fuzzing, and Locust for load testing.

**Core Value:** Catch regressions in the critical production event chain (StepCompleted -> BatchCompleted -> JobClosed, inventory movements, WIP cascades, serial traceability) before they reach users.

### Constraints

- **Database:** Must use real ArangoDB (via testcontainers), not mocks — per testing strategy principle #4
- **Python:** 3.11 (matching backend container)
- **Node.js:** 20.19.0 (matching webapp runtime)
- **Isolation:** Tests must be fully isolated — no shared state between test classes
- **Docker:** Required for testcontainers (ArangoDB) and Playwright browsers
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- **Python 3.11** - Backend API and workflow orchestration
- **JavaScript/Node.js 20.19.0** - Web applications (Quasar-based SPA)
- **Vue.js 3** - Frontend framework for reactive UIs
- **YAML** - Docker Compose and deployment configuration
## Runtime
- **Python 3.11-slim** - Backend container base image from `backend/api/Dockerfile`
- **Node.js 20.19.0** - Web application runtime specified in `.nvmrc` files at `webapps/main/.nvmrc` and `webapps/warehouse/.nvmrc`
- **pip** - Python dependency management with `requirements.txt`
- **Yarn** - Node.js package management with `yarn.lock` at project root
- **npm** - Node.js package manager (minimum version 10.0.0)
## Frameworks
- **FastAPI 0.x** - Modern async REST API framework at `backend/api/main.py`
- **Starlette** - ASGI framework (dependency of FastAPI)
- **Uvicorn** - ASGI server for running FastAPI applications
- **Quasar Framework 2.16.0** - Vue 3-based UI framework with SSR/SPA/PWA support at `webapps/main/` and `webapps/warehouse/`
- **Pinia 2.1.7** - State management (replacement for Vuex)
- **Vue Router 4.0.0** - Client-side routing
- **Vue I18n 9.0.0** - Internationalization support
- **Prefect 3.x** - Workflow orchestration engine in `backend/workflow/`
- **WeasyPrint 66.x** - HTML to PDF conversion at `backend/api/requirements.txt`
- **ReportLab 4.x** - PDF creation library for generated content
- **PyPDF 4.x** - PDF manipulation and merging
- **PDFme 5.5.0** - Client-side PDF template library in both web and warehouse apps
## Key Dependencies
### Backend API (`backend/api/requirements.txt`)
- `python-arango==8.*` - ArangoDB multi-model database client at `backend/api/utils/db.py`
- `fastapi==0.*`
- `starlette>=0.13`
- `uvicorn>=0.11`
- `uvloop>=0.14` - Performance optimization
- `h11==0.*`
- `httptools` - C-accelerated HTTP parsing
- `bcrypt==4.3.*` - Password hashing
- `passlib==1.7.2` - Password schemes
- `PyJWT==2.0.*` - JWT token generation and validation
- `python-jose` - JWT/JOSE implementation
- `cryptography==41.0.*` - Cryptographic operations
- `confluent_kafka` - Apache Kafka producer/consumer client at `backend/api/utils/kafka/`
- `websockets` - WebSocket protocol support
- `weasyprint==66.*`
- `reportlab==4.*`
- `pypdf==4.*`
- `openpyxl==3.*` - Excel import/export
- `pydantic==2.*` - Data validation and settings management
- `pydantic-settings==2.*` - Configuration management at `backend/api/utils/config.py`
- `httpx==0.*` - HTTP client for async requests
- `python-multipart==0.0.*` - Multipart form data parsing
- `python-dateutil==2.8.*` - Date/time utilities
- `click==7.1.*` - CLI framework
- `six==1.15.0` - Python 2/3 compatibility
- `chardet==3.0.*` - Character encoding detection
- `gunicorn>=20.0` - WSGI HTTP Server
### Workflow Engine (`backend/workflow/requirements.txt`)
- `prefect==3.*` - Workflow orchestration framework
- `python-arango==8.*` - Database access for workflow state
- `httpx` - HTTP client for async operations
### Frontend Web App (`webapps/main/package.json`)
- `vue@3.4.18` - Progressive JavaScript framework
- `quasar@2.16.0` - Vue 3 UI component framework
- `vue-router@4.0.0` - Client-side routing
- `pinia@2.1.7` - State management
- `axios@1.7.0` - HTTP client library
- `socket.io-client@4.7.5` - WebSocket client for real-time communication
- `vue-sse@2.5.2` - Server-Sent Events support
- `@pdfme/ui@5.5.0` - PDF template editor UI
- `@pdfme/generator@5.5.0` - PDF generation
- `@pdfme/schemas@5.5.0` - PDF template schemas
- `@pdfme/common@5.5.0` - Common utilities
- `vue-pdf-embed@1.1.6` - PDF viewer component
- `codemirror@6.0.1` - Advanced code editor
- `@codemirror/*` - Syntax highlighting, language support, linting
- `luxon@3.0.4` - DateTime manipulation
- `xlsx@0.18.5` - Excel file handling
- `vue-i18n@9.0.0` - Internationalization
- `vue-cookies@1.8.4` - Cookie management
- `sortablejs@1.15.0` - Drag-and-drop lists
- `video.js@8.17.4` - HTML5 video player
- `file-saver@2.0.5` - Save files client-side
- `jwt-decode@3.1.2` - JWT token parsing
- `@vueuse/core@11.1.0` - Vue 3 composition function utilities
- `@quasar/app-vite@2.0.0` - Vite-based Quasar CLI
- `vite@5.4.0` - Frontend build tool
- `esbuild@0.21.0` - JavaScript bundler
- `eslint@8.57.0` - JavaScript linter
- `prettier@3.1.1` - Code formatter
- `postcss@8.4.14` - CSS transformations
### Warehouse Mobile App (`webapps/warehouse/package.json`)
- `@capacitor/core@6.0.0` - Native bridge for mobile features
- `@capacitor/cli@6.0.0` - Capacitor CLI
- `@capacitor/app@6.0.0` - App lifecycle management
- `@capacitor/splash-screen@6.0.0` - Splash screen control
- `@zxing/browser@0.1.5` - Barcode/QR code reading from camera
- `@zxing/library@0.21.3` - ZXing library for barcode decoding
- `browserprint-es@0.0.5` - Direct printer control
## Configuration
- Backend configuration via `PROGRESS_*` prefixed environment variables at `backend/api/utils/config.py`
- Key settings: `PROGRESS_ARANGO_URL`, `PROGRESS_MEDIA_PATH`, `PROGRESS_API_ROOT_PATH`, `PROGRESS_DB_NAME`
- Docker secrets for sensitive values: `progress_api_db_pwd`, `progress_admin_pwd`, `progress_jwt_secret`
- Frontend configuration via `window.API_CONFIG` object injected from `deploy/config/appConfig.js`
- **Frontend:** Quasar config at `webapps/main/quasar.config.js`
- **Backend:** Python module loading, no explicit build configuration
- **ESLint:** `.eslintrc.js` at `webapps/main/.eslintrc.js`
- **Prettier:** `.prettierrc.json` at `webapps/main/.prettierrc.json` and `webapps/warehouse/.prettierrc`
## Platform Requirements
- Docker and Docker Compose (as per readme.md)
- Docker volumes for: `media`, `db_data`, `db_backup`, `logs`
- Python 3.11 (backend)
- Node.js 20.19.0+ (webapps)
- Yarn package manager
- Docker and Docker Compose orchestration
- Kubernetes-ready deployment via Traefik reverse proxy at `deploy/compose/base.yaml`
- External volumes for persistent data
- GitLab CI/CD pipeline at `.gitlab-ci.yml` for Docker image builds
- GitLab registry for image storage
## Build & Deployment
- `python:3.11-slim` - Backend API
- `arangodb:3.11` - Database (Intel and ARM64 variants available)
- `apache/kafka:latest` - Message broker
- `traefik:v2.11` - Reverse proxy
- `prefecthq/prefect:3-latest` - Workflow server
- `postgres:15.2-alpine` - Workflow database
- Custom images built via GitLab CI at `registry.gitlab.com/progresslab/progress-platform/`
- GitLab CI with Docker-in-Docker for building container images
- Version-based tagging with semantic versioning
- Push to GitLab registry on version tags matching `v*.*.*` pattern
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Naming Conventions
### Backend (Python)
- Files: `snake_case.py`
- Functions/variables: `snake_case`
- Classes/models: `PascalCase` (Pydantic models)
- Constants: `UPPER_SNAKE_CASE`
- Endpoint files named after domain: `production.py`, `inventory.py`
### Frontend (Vue3/JS)
- Vue components: `PascalCase.vue` (e.g., `PrintTemplateCard.vue`)
- Composables: `use{Name}.js` or descriptive name in `composables/`
- Stores (Pinia): `camelCase` module names
- Pages: descriptive PascalCase (e.g., `ProductionPage.vue`)
- Utility files: `camelCase.js`
## Backend Patterns
### FastAPI Endpoints
- One file per domain in `backend/api/endpoints/`
- Routes registered via router, imported in `main.py`
- Pydantic models for request/response validation in `backend/api/models/`
- Auth via JWT middleware — see `backend/api/utils/auth.py`
### Event System
- Events processed in `backend/api/events/`
- Business logic in `backend/api/managers/`
- Separation: endpoints call managers, managers emit events
### Error Handling (Current — problematic)
- Bare `except:` clauses common throughout endpoint files (known issue)
- Errors often swallowed silently
- **Preferred pattern** (use this for new code):
### Logging
- Use Python's `logging` module (not `print()`)
- `print()` debug statements exist in legacy code — do not add more
## Frontend Patterns
### Vue3 Composition API
- Prefer `<script setup>` with Composition API for new components
- Legacy components use Options API — do not refactor unless changing
- Composables extract reusable logic: `webapps/main/src/composables/`
### Event Logging
- Use the `sendEvent()` composable for user action tracking
- Located at `webapps/main/src/composables/event.js`
### State Management
- **Pinia stores** (newer): `webapps/main/src/stores/` — use for new state
- **Vuex store** (legacy): `webapps/main/src/store/` — avoid adding to this
- Prefer Pinia for any new state management
### API Calls
- Axios configured in boot files: `webapps/main/src/boot/`
- API calls made through store actions or composables, not directly in components
### Import Organization
- ESLint enforces import ordering (configured with `eslint-plugin-import`)
- External deps → internal modules → relative imports
- Use path aliases for internal imports (configured in Quasar)
## Code Style
### Backend
- PEP 8 formatting (Python standard)
- FastAPI dependency injection for shared concerns (auth, db)
- Pydantic for all data validation at boundaries
### Frontend
- Prettier for formatting (configured in `.prettierrc` or `package.json`)
- ESLint with `vue/vue3-recommended` ruleset
- No unused imports (enforced by ESLint)
## Patterns to Follow
## Patterns to Avoid
- Wildcard imports (`from module import *`) — use explicit imports
- Debug `print()` statements — use logger
- Bare `except:` clauses — catch specific exceptions
- Adding to legacy Vuex store — use Pinia instead
- Options API for new components — use Composition API
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- **Immutable event log** — All business logic mutations flow through typed Events rather than direct state updates
- **Event-driven side effects** — Asynchronous reactions via Kafka topic subscriptions and manager patterns
- **Layered backend** — FastAPI endpoints → events → transactional state mutations → database
- **Dual-webapp architecture** — Main desktop app (Quasar) + mobile warehouse app (Quasar + Capacitor)
- **Graph database (ArangoDB)** — Documents + edges for domain entity relationships
## Layers
- Purpose: HTTP request routing, middleware chain, static file serving, TLS termination
- Location: `backend/api/main.py` (FastAPI app), `deploy/compose/base.yaml` (Traefik proxy)
- Contains: FastAPI router registration, CORS/GZip/notification middleware, startup/shutdown hooks
- Depends on: FastAPI, Starlette middleware, Kafka producer initialization
- Used by: All external clients (webapps, mobile, third-party integrations)
- Purpose: Receive requests and instantiate domain events
- Location: `backend/api/endpoints/*.py` (20+ files: production.py, inventory.py, counting.py, etc.)
- Contains: FastAPI route handlers that validate input, create event objects, return responses
- Depends on: Event classes, Pydantic models, utility functions (auth, db, counter generation)
- Used by: HTTP clients; endpoints are the only entry points for external requests
- Purpose: Execute immutable business logic as transaction-scoped event objects
- Location: `backend/api/events/` (base_event.py + domain-specific event files)
- Contains: BaseEvent abstract class and 50+ concrete event types organized by domain:
- Depends on: Pydantic models (EventInfoModel, event-specific schemas), ArangoDB transactions
- Used by: Endpoints instantiate events; managers listen to event types
- Flow: Event.save() → pre_processing() → apply() → store_event() → commit_transaction()
- Atomicity: All DB mutations in apply() occur within a transaction; failure aborts the entire transaction
- Idempotency: Events must be designed to be replayable without side effects (required for recovery)
- Purpose: Handle side effects, async operations, and publish domain events to Kafka
- Location: `backend/api/managers/*.py`
- Contains:
- Depends on: Kafka producer/consumer, threading
- Used by: Middleware, event post_processing(), startup hooks
- Purpose: Pydantic models for API request/response validation and database document structure
- Location: `backend/api/models/*.py` (base_models.py, event.py, product.py, production.py, etc.)
- Contains:
- Depends on: Pydantic v2, ArangoDB field aliases (_id, _key, _rev, _from, _to)
- Used by: Endpoints for request validation, events for data binding, utilities for queries
- Purpose: Cross-cutting concerns and helper functions
- Location: `backend/api/utils/` (40+ files)
- Contains:
- Depends on: External libraries (arango, kafka, fastapi, pydantic)
- Used by: All layers (endpoints, events, managers)
- Purpose: Cross-cutting request/response handling
- Location: `backend/api/middlewares/*.py`
- Contains:
- Depends on: Starlette BaseHTTPMiddleware
- Used by: FastAPI app.add_middleware()
## Data Flow
- `utils.production.Queries.get_job()` — Fetch job with current state
- `utils.inventory.Queries.get_position()` — Fetch location quantity
- Business logic checks preconditions (e.g., "Job must be in RUNNING state")
- If valid, event is created; if not, HTTPException raised
## Key Abstractions
- Purpose: Abstract base for all domain events
- Examples: `backend/api/events/production/job_started.py`, `backend/api/events/inventory/movement_completed.py`
- Pattern:
- Purpose: Centralized registry of all event types in the system
- Examples: JOB_STARTED, MOVEMENT_COMPLETED, COUNT_SESSION_APPLIED, SERIAL_CREATED
- Location: `backend/api/models/event.py`
- Usage: Events reference EventType for validation; utilities use it for lookup
- Purpose: Application-scoped services for cross-cutting concerns
- Pattern: getInstance() returns singleton; initialized once on startup
- Examples: NotificationManager broadcasts changes; KafkaConsumerManager subscribes to topics
- Lifecycle: Initialized in main.py startup_event(); closed in shutdown_event()
- Purpose: Request/response interception before/after endpoint execution
- Order: CORSMiddleware → GZipFilterMiddleware → NotificationMiddleware
- Effect: NotificationMiddleware automatically notifies clients of state changes
## Entry Points
- Location: `backend/api/main.py` line 49-92
- Triggers: HTTP requests from webapps/clients
- Responsibilities:
- Location: `backend/api/managers/websocket_manager.py`
- Triggers: Client WebSocket connections
- Responsibilities: Maintain client connections, broadcast notifications, handle disconnections
- Location: `backend/api/managers/kafka_consumer_manager.py`
- Triggers: Kafka broker has messages
- Responsibilities: Route topics to registered subscribers (NotificationsKafkaConsumer, ChatKafkaConsumer, etc.)
- Triggered by: Event.save() calls
- Scope: Single event application (atomicity boundary)
- Commits: Only if all logic succeeds; aborts on exception
## Error Handling
- **Validation errors** — Endpoint returns 400 with HTTPException detail before creating event
- **Precondition failures** — Endpoint checks state; returns 409 if action not allowed
- **Transaction rollback** — Event.save() finally block aborts transaction if exception occurs
- **Kafka failures** — Non-blocking; exceptions in post_processing() do not fail the event
- **HTTP exceptions** — Pydantic validation or endpoint logic raises HTTPException with status code and detail
```python
```
## Cross-Cutting Concerns
- Request level: Pydantic models in endpoints validate schema
- Event level: Event-specific InfoModel validates event data
- Business level: Endpoints check preconditions (state, permissions, constraints)
- Method: JWT tokens in Authorization header
- Verification: `utils.auth.verify_token()` dependency in FastAPI routes
- Scope: Token-dependent endpoints; /hello endpoint is public
- Org-scoped access control (implied by queries filtering by org_id)
- Role-based access (stored in token claims; checked at endpoint level)
- Attachment storage: `backend/api/media/` directory (Docker volume `/media`)
- Upload: `endpoints/media.py` handles multipart form uploads
- Retrieval: FastAPI serves files directly via `/media/{path}`
- All state mutations occur within ArangoDB transactions
- Collections specified via Event.get_tx_collections()
- Coordinator: Event.save() manages begin/commit/abort lifecycle
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Generated by GSD from session_analysis. Run `/gsd-profile-user --refresh` to update.

| Dimension | Rating | Confidence |
|-----------|--------|------------|
| Communication | mixed | HIGH |
| Decisions | fast-intuitive | HIGH |
| Explanations | concise | HIGH |
| Debugging | hypothesis-driven | MEDIUM |
| UX Philosophy | pragmatic | MEDIUM |
| Vendor Choices | opinionated | HIGH |
| Frustrations | instruction-adherence | LOW |
| Learning | self-directed | HIGH |

**Directives:**
- **Communication:** Match communication depth to the task: respond concisely to short directives and bug reports, but provide structured, thorough responses when the developer initiates architecture or design discussions with detailed context.
- **Decisions:** Present options concisely and expect a fast decision. When trade-offs are minor, make a recommendation and proceed. For significant architectural choices, present options clearly but do not over-elaborate -- this developer decides quickly.
- **Explanations:** Provide brief explanations of approach and key decisions alongside code. Focus on the 'why' and trade-offs rather than step-by-step walkthroughs. Go deeper only when the developer explicitly asks for more detail or is exploring an unfamiliar domain.
- **Debugging:** When debugging, engage with the developer's hypothesis first -- confirm or refute it with evidence. Provide root cause analysis, not just fixes. When the developer asks investigative questions, answer precisely and help narrow the diagnosis.
- **UX Philosophy:** Ensure UI implementations are usable and logically organized. Pay attention to edge cases that could confuse users or produce incorrect data. Standard styling is fine -- focus on clear information architecture and preventing user errors over visual polish.
- **Vendor Choices:** Respect this developer's stated tool preferences -- do not suggest alternatives unless asked. When the developer names a specific tool, use it. If a recommendation conflicts with their known preferences (declarative config, uv, modern tooling), explain why before proceeding.
- **Frustrations:** Follow instructions precisely and verify that implementations match the stated requirements before presenting them. When the developer reports that something is 'not solved' or behavior is wrong, re-read the original requirement carefully before attempting a fix. Low frustration count suggests good rapport -- maintain it by being precise.
- **Learning:** Treat this developer as a knowledgeable peer. When they bring external research or their own analysis, engage with the substance of their argument rather than restating basics. Provide targeted insights they might have missed rather than broad overviews. When they ask 'what do you think?', give a genuine critical assessment.
<!-- GSD:profile-end -->


# Behavioral instructions
- Do not add Claude as co-author of commits
