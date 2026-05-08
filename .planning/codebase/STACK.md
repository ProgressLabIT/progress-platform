# Technology Stack

**Analysis Date:** 2026-05-08

## Languages

**Primary:**
- Python 3.11 - Backend API (`backend/api/`), workflow orchestration (`backend/workflow/`), Sparkplug B bridge (`backend/sparkplug_bridge/`), print service (`backend/print-service/`)
- JavaScript (ES Modules) - Main webapp (`webapps/main/`), warehouse mobile app (`webapps/warehouse/`), E2E tests (`testing/playwright/`)

**Secondary:**
- Vue 3 SFC (`.vue` files) - All frontend components
- AQL (ArangoDB Query Language) - Database queries in `backend/api/utils/`
- YAML - Docker Compose orchestration (`deploy/compose/`)
- SCSS - Styling at `webapps/main/src/css/`
- Protocol Buffers - Sparkplug B message encoding (vendored Eclipse Tahu at `backend/sparkplug_bridge/`)

## Runtime

**Backend:**
- Python 3.11-slim (Docker base image) - `backend/api/Dockerfile`
- Gunicorn + Uvicorn (production) - 4 worker processes in `deploy/compose/stack.yaml`
- Uvicorn standalone (development) - via debugpy in `deploy/compose/dev.yaml`

**Frontend:**
- Node.js ^20.19.0 || ^22 - specified in `engines` of both `package.json` files
- Vite 5.4.0 - dev server and build tool via `@quasar/app-vite`

**Package Managers:**
- pip - Python dependencies via `requirements.txt` (no lockfile for backend services)
- uv - Modern Python package manager with lockfile at `testing/pytest/uv.lock`
- Yarn >= 1.22.0 - JS dependencies with `yarn.lock` at project root
- npm >= 10.0.0 - alternative JS package manager

## Frameworks

**Core Backend:**
- FastAPI 0.x - REST API framework at `backend/api/main.py`
- Starlette >= 0.13 - ASGI underpinning (middleware, SSE support)
- Uvloop >= 0.14 - High-performance event loop optimization

**Frontend:**
- Quasar 2.16.0 - Vue 3 UI framework (SPA mode) for both webapps
- Vue 3.4.18 - Reactive frontend framework
- Vue Router 4.0.0 - Client-side routing (history mode)
- Pinia 2.1.7 - Preferred state management at `webapps/main/src/stores/` (use for new code)
- Vuex 4.x - Legacy state management at `webapps/main/src/store/` (avoid for new code)
- Vue I18n 9.0.0 - Internationalization support

**Workflow Orchestration:**
- Prefect 3.x - Workflow orchestration engine at `backend/workflow/`, server in `deploy/compose/workflow.yaml`
- PostgreSQL 15.2-alpine with TimescaleDB extension - Workflow metadata + metrics storage

**Testing Infrastructure:**
- pytest >= 9.0 - Python test runner at `testing/pytest/` (pythonpath configured via pyproject.toml)
- pytest-asyncio >= 0.21 - Async test execution with auto mode
- testcontainers >= 4.14 - Container lifecycle management (spins real ArangoDB for integration tests)
- pytest-cov >= 7.1 - Code coverage measurement
- Playwright @1.51.0 - E2E browser testing at `testing/playwright/` (Chromium headless)
- Vitest 4.1.0 - Component tests for Vue (optional, in `webapps/main/`)
- @vue/test-utils 2.4.6 - Vue component test utilities
- happy-dom 17.0.0 - Lightweight DOM for tests
- Schemathesis >= 4.15 - API property-based testing (fuzz testing)
- Locust >= 2.0 - Load testing framework

**Data Validation & Serialization:**
- Pydantic 2.x - Request/response validation at `backend/api/models/`
- Pydantic Settings 2.x - Configuration management at `backend/api/utils/config.py`

**Messaging & Event Streaming:**
- nats-py (latest, pinned >=2.0,<3.0) - NATS JetStream client at `backend/api/utils/nats_client.py` (canonical messaging broker)
- confluent-kafka - **Legacy/deprecated** Kafka client (present in test suite but not actively used; treat as transitional dead code)

**IoT & Industrial Automation:**
- aiomqtt 2.5.1 - Async MQTT client for Sparkplug B bridge at `backend/sparkplug_bridge/`
- protobuf >= 5.28.2 - Protobuf serialization for Sparkplug B messages
- asyncpg 0.31.0 - Async PostgreSQL driver for TimescaleDB (Sparkplug historian at `backend/sparkplug_bridge/historian/`)

**Document & Report Generation:**
- WeasyPrint 66.x - HTML to PDF conversion (requires libcairo2, libpango, libfontconfig system dependencies)
- ReportLab 4.x - Programmatic PDF creation
- PyPDF 4.x - PDF manipulation and merging
- PDFme 5.5.0 - Client-side PDF template editor/generator (both webapps)
- openpyxl 3.x - Excel import/export

**Real-Time Communication:**
- socket.io-client 4.7.5 - WebSocket client (legacy; SSE now preferred)
- vue-sse 2.5.2 - Server-Sent Events support for notifications at `backend/api/endpoints/notification.py`
- @microsoft/fetch-event-source ^2.0.1 - EventSource polyfill for fetch API

**Embedded Reporting:**
- Streamlit - Dashboard framework at `deploy/scripts/reports/main.py` (embedded via iframe at `/reports` route)
- Runs in `python:3.11-slim` container with custom entrypoint script

**Database Access:**
- python-arango 8.x - ArangoDB client for document/graph queries at `backend/api/utils/db.py`

**Cryptography & Authentication:**
- PyJWT 2.0.x - JWT token encode/decode
- python-jose - JOSE implementation for JWT verification
- passlib >= 1.7.2 - Password hashing context manager
- bcrypt 4.3.x - bcrypt algorithm backend
- cryptography 41.0.x - Cryptographic operations

**HTTP Clients:**
- httpx 0.x - Async HTTP client for Python
- axios 1.7.0 - Promise-based HTTP client for JavaScript (Print job API calls)

**Code Quality & Formatting:**
- ESLint 8.57.0 - JavaScript/Vue linting at `webapps/main/.eslintrc.js`
- Prettier 3.1.1 (main) / 2.5.1 (warehouse) - Code formatter (config at `.prettierrc.json` / `.prettierrc`)

**Build & Module Bundling:**
- Vite 5.4.0 - Frontend bundler and dev server
- @quasar/app-vite 2.0.0 - Quasar CLI with Vite integration
- esbuild 0.21.0 - JavaScript bundler/transformer
- PostCSS 8.4.14 - CSS transformations
- Autoprefixer 10.4.2 - Vendor prefixes for CSS

**Mobile Support:**
- @capacitor/core 6.0.0 - Native bridge for iOS/Android
- @capacitor/cli 6.0.0 - Capacitor build tool
- @capacitor/app 6.0.0 - App lifecycle management
- @capacitor/splash-screen 6.0.0 - Splash screen control
- @zxing/browser 0.1.5 - Barcode/QR code scanning from camera
- @zxing/library 0.21.3 - ZXing barcode decoding library
- browserprint-es 0.0.5 - Direct thermal printer control (Zebra-compatible)

**UI Utilities:**
- sortablejs 1.15.0 - Drag-and-drop list reordering
- codemirror 6.0.1 - Advanced code editor (CodeMirror 6 with plugins)
- @codemirror/lang-json, @codemirror/language, @codemirror/lint, @codemirror/state, @codemirror/view - CodeMirror language and UI support
- @lezer/highlight - Lezer parser highlighting
- video.js 8.17.4 - HTML5 video player
- prismjs 1.30.0 - Syntax highlighting library

**Date/Time & Data Utilities:**
- luxon 3.0.4 - DateTime manipulation (JavaScript)
- xlsx 0.18.5 - Excel file reading/writing
- file-saver 2.0.5 - Client-side file downloads
- jwt-decode 3.1.2 - JWT token parsing (browser-side)
- @vueuse/core 11.1.0 - Vue 3 Composition API utilities
- vue-i18n 9.0.0 - Internationalization
- vue-cookies 1.8.4 - Cookie management
- python-dateutil 2.8.x - Date/time parsing (Python)
- chardet 3.0.x - Character encoding detection

**CLI & Utilities:**
- Click 7.1.x - CLI framework (Python)
- Typer >= 0.25.1 - Modern async CLI framework (test utilities)

**Reverse Proxy & Load Balancing:**
- Traefik v2.11 - Layer 7 reverse proxy, service routing, middleware at `deploy/compose/stack.yaml`

## Configuration

**Backend API (`backend/api/utils/config.py`):**
- Pydantic Settings with `PROGRESS_` env prefix
- Docker secrets from `/run/secrets/` directory
- `.env` file support (optional)
- Key settings:
  - `arango_url` - ArangoDB connection URL
  - `nats_url` - NATS broker URL (default: `nats://broker:4222`)
  - `api_root_path` - API mount path
  - `db_name` - ArangoDB database name
  - `api_db_username`, `api_db_pwd` - ArangoDB credentials
  - `jwt_secret` - JWT signing secret (via `/run/secrets/progress_jwt_secret`)
  - `cors_allowed_origins` - CORS whitelist

**Sparkplug Bridge (`backend/sparkplug_bridge/config.py`):**
- MQTT URL: `PROGRESS_MQTT_URL` (default: `tcp://broker:1883`)
- NATS URL: `PROGRESS_NATS_URL` (default: `nats://broker:4222`)
- MQTT client ID: `PROGRESS_MQTT_CLIENT_ID`
- Heartbeat interval: `PROGRESS_BRIDGE_HEARTBEAT_INTERVAL_SEC` (default: 5s)
- Host ID: `PROGRESS_BRIDGE_HOST_ID`

**Sparkplug Historian (`backend/sparkplug_bridge/historian/config.py`):**
- Admin DB URL: `PROGRESS_HISTORIAN_ADMIN_URL` (postgres system DB)
- Historian DB URL: `PROGRESS_HISTORIAN_DB_URL` (progress_historian database)
- Batch size: `PROGRESS_HISTORIAN_BATCH_SIZE` (default: 500)
- Flush interval: `PROGRESS_HISTORIAN_FLUSH_MS` (default: 100ms)

**Frontend Configuration:**
- Quasar config at `webapps/main/quasar.config.js`
- Runtime config injected via Docker volume: `deploy/config/appConfig.js` → `window.API_CONFIG`
- ESLint config at `webapps/main/.eslintrc.js`
- Prettier config at `webapps/main/.prettierrc.json`, `webapps/warehouse/.prettierrc`
- Vitest component config at `webapps/main/vitest.component.config.js` (optional)
- Path aliases: `@` → `./src`, `views` → `./src/views`
- Dark mode enabled by default

**Testing (`testing/pytest/pyproject.toml`):**
- pytest async mode: `auto`
- pythonpath configured to include `backend/api`
- Integration test marker for tests requiring full stack

## Platform Requirements

**Development:**
- Docker and Docker Compose (required for testcontainers spinning ArangoDB)
- Python 3.11 (matching backend container)
- Node.js 20.19.0 or ^22
- Yarn >= 1.22.0 or npm >= 10.0.0

**Production Deployment:**
- Docker + Docker Swarm (or Kubernetes)
- Traefik v2.11 for TLS termination and request routing
- NATS broker (JetStream enabled) - port 4222 for clients, 1883 for MQTT
- ArangoDB 3.11 - port 8529 (can run as single-node or cluster)
- PostgreSQL 15.2-alpine with TimescaleDB extension - port 5432 (for Prefect workflow DB and Sparkplug historian)
- External volumes (all declared as external in stack files):
  - `media` - File uploads and attachments
  - `db_data` - ArangoDB persistence
  - `db_backup` - ArangoDB backups
  - `workflow_db` - PostgreSQL data
  - `workflow_config` - Prefect configuration
  - `flows` - Workflow definitions
  - `reports` - Streamlit app code
  - `letsencrypt` - TLS certificates

## Container Images

**Platform Services (from GitLab registry):**
- `registry.gitlab.com/progresslab/progress-platform/api:{VERSION}` - Backend API
- `registry.gitlab.com/progresslab/progress-platform/app:{VERSION}` - Main webapp (Quasar SPA, nginx)
- `registry.gitlab.com/progresslab/progress-platform/warehouse:{VERSION}` - Warehouse mobile app (Quasar + Capacitor)
- `progress-sparkplug-bridge:dev` - Sparkplug B MQTT↔NATS bridge (built locally from `backend/sparkplug_bridge/Dockerfile`)

**Infrastructure (public registries):**
- `arangodb:3.11` - Document/graph database
- `timescale/timescaledb:latest-pg15` - PostgreSQL 15 + TimescaleDB (for historian)
- `prefecthq/prefect:3-latest` - Workflow orchestration server
- `nats:2-alpine` (dev) / `nats:latest` (prod) - NATS message broker (JetStream-enabled)
- `traefik:v2.11` - Reverse proxy and load balancer
- `python:3.11-slim` - Streamlit reports container

## Build & Deployment

**CI/CD Pipeline (GitLab):**
- Configuration: `.gitlab-ci.yml` (Docker-in-Docker executor)
- Docker image builder: `docker:24.0.5-dind`
- Registry: `registry.gitlab.com/progresslab/progress-platform/`
- Trigger: Version tags matching `v*.*.*` (supports `a`, `b`, `rc` pre-release suffixes)
- Artifacts: Built images (`api`, `app`, `warehouse`, `wf-sys-worker`, `print-service`)
- Print service also published as `.zip` to GitLab generic packages

---

*Stack analysis: 2026-05-08*
