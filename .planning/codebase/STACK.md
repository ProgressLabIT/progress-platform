# Technology Stack

**Analysis Date:** 2026-04-15

## Languages

**Primary:**
- Python 3.11 - Backend API (`backend/api/`), workflow engine (`backend/workflow/`), print service (`backend/print-service/`)
- JavaScript (ES Modules) - Main webapp (`webapps/main/`), warehouse mobile app (`webapps/warehouse/`)

**Secondary:**
- Vue 3 SFC (`.vue` files) - All frontend components
- AQL (ArangoDB Query Language) - Database queries embedded in Python utils and endpoints
- YAML - Docker Compose orchestration (`deploy/compose/`)
- SCSS - Styling (`webapps/main/src/css/app.scss`)

## Runtime

**Backend:**
- Python 3.11-slim (Docker base image) - `backend/api/Dockerfile`
- Gunicorn + Uvicorn (production) - `CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", ...]`
- Uvicorn standalone (development) - via debugpy in `deploy/compose/dev.yaml`

**Frontend:**
- Node.js ^20.19.0 || ^22 - specified in `engines` of both `package.json` files
- Vite 5.4.0 - dev server and build tool via `@quasar/app-vite`

**Package Managers:**
- pip - Python dependencies via `requirements.txt` (no lockfile)
- Yarn >= 1.22.0 - JS dependencies with `yarn.lock` at project root
- npm >= 10.0.0 - alternative JS package manager

## Frameworks

**Core:**
- FastAPI 0.x - REST API framework (`backend/api/main.py`)
- Starlette >= 0.13 - ASGI underpinning (middleware, SSE)
- Quasar 2.16.0 - Vue 3 UI framework for both webapps
- Vue 3.4.18 - Reactive frontend framework
- Prefect 3.x - Workflow orchestration engine (`backend/workflow/`)

**State Management:**
- Pinia 2.1.7 - Preferred store (newer) (`webapps/main/src/stores/`)
- Vuex 4.x - Legacy store (still in deps, avoid for new code) (`webapps/main/src/store/`)

**Routing:**
- Vue Router 4.0.0 - Client-side routing (history mode)
- FastAPI router - Server-side route registration in `backend/api/main.py`

**Build/Dev:**
- Vite 5.4.0 - Frontend bundler and dev server
- esbuild 0.21.0 - JS bundler (used by Vite internally)
- `@quasar/app-vite` 2.0.0 - Quasar CLI with Vite integration
- ESLint 8.57.0 - JS/Vue linting
- Prettier 3.1.1 (main) / 2.5.1 (warehouse) - Code formatting

**Testing:**
- Vitest 4.1.0 - Component testing (`webapps/main/package.json`)
- `@vue/test-utils` 2.4.6 - Vue component test utilities
- happy-dom 17.0.0 - DOM environment for tests
- pytest >= 8.0 - Python testing (print-service)

**Mobile:**
- Capacitor 6.0.0 - Native bridge for warehouse Android app (`webapps/warehouse/`)

## Key Dependencies

### Backend API (`backend/api/requirements.txt`)

**Database:**
- `python-arango` 8.x - ArangoDB client (`backend/api/utils/db.py`)

**Messaging:**
- `nats-py` (latest) - NATS message broker client (`backend/api/utils/nats_client.py`)

**Auth & Security:**
- `bcrypt` 4.3.x - Password hashing
- `passlib` 1.7.2 - Password hashing context (bcrypt scheme)
- `PyJWT` 2.0.x - JWT token encode/decode
- `python-jose` - JOSE implementation (JWT verification)
- `cryptography` 41.0.x - Cryptographic operations

**HTTP/ASGI:**
- `uvicorn` >= 0.11 - ASGI server
- `uvloop` >= 0.14 - High-performance event loop
- `gunicorn` >= 20.0 - Process manager (4 workers in production via `deploy/compose/stack.yaml`)
- `httptools` - C-accelerated HTTP parsing
- `h11` 0.x - HTTP/1.1 protocol implementation
- `httpx` 0.x - Async HTTP client

**Data Validation:**
- `pydantic` 2.x - Request/response validation, model definitions
- `pydantic-settings` 2.x - Configuration from env vars (`backend/api/utils/config.py`)

**Document Generation:**
- `weasyprint` 66.x - HTML-to-PDF conversion (requires system libs: pango, cairo, fontconfig per `backend/api/Dockerfile`)
- `reportlab` 4.x - Programmatic PDF creation
- `pypdf` 4.x - PDF merging/manipulation
- `openpyxl` 3.x - Excel import/export

**Utilities:**
- `python-dateutil` 2.8.x - Date/time parsing
- `python-multipart` 0.0.x - Multipart form data
- `click` 7.1.x - CLI framework
- `chardet` 3.0.x - Character encoding detection
- `six` 1.15.0 - Python 2/3 compatibility (legacy dep)

### Workflow Engine (`backend/workflow/requirements.txt`)

- `prefect` 3.x - Workflow orchestration
- `python-arango` 8.x - Database access for workflow state
- `httpx` - Async HTTP client

### Print Service (`backend/print-service/requirements.txt`)

- `nats-py` >= 2.0, < 3.0 - NATS messaging
- `pydantic` >= 2.0, < 3.0 - Data validation
- `pydantic-settings` >= 2.0, < 3.0 - Configuration
- `pytest` >= 8.0 - Testing
- `pytest-asyncio` >= 0.23 - Async test support

### Main Webapp (`webapps/main/package.json`)

**UI Components:**
- `quasar` ^2.16.0 - Component library (dark mode default, MDI v7 icons)
- `@quasar/extras` ^1.16.8 - Icon packs
- `sortablejs` ^1.15.0 - Drag-and-drop list reordering

**PDF:**
- `@pdfme/ui` ^5.5.0, `@pdfme/generator`, `@pdfme/schemas`, `@pdfme/common` - PDF template editor and generator
- `vue-pdf-embed` 1.1.6 - PDF viewer

**Code Editor:**
- `codemirror` ^6.0.1 with `@codemirror/lang-json`, `@codemirror/language`, `@codemirror/lint`, `@codemirror/state`, `@codemirror/view` - JSON editor

**Communication:**
- `axios` ^1.7.0 - HTTP client
- `socket.io-client` ^4.7.5 - WebSocket client (legacy dep, SSE now preferred)
- `vue-sse` ^2.5.2 - Server-Sent Events

**Utilities:**
- `luxon` ^3.0.4 - DateTime manipulation
- `xlsx` ^0.18.5 - Excel file handling
- `file-saver` ^2.0.5 - Client-side file saving
- `jwt-decode` ^3.1.2 - JWT token parsing (client-side)
- `@vueuse/core` ^11.1.0 - Vue 3 composition utilities
- `vue-i18n` ^9.0.0 - Internationalization
- `vue-cookies` ^1.8.4 - Cookie management
- `video.js` ^8.17.4 - Video player
- `prismjs` ^1.30.0 - Syntax highlighting
- `nodemon` ^3.1.0 - Dev file watcher (misplaced in deps, should be devDeps)

### Warehouse Webapp (`webapps/warehouse/package.json`)

**Mobile-specific:**
- `@capacitor/core` ^6.0.0, `@capacitor/app`, `@capacitor/cli`, `@capacitor/splash-screen` - Native mobile bridge
- `@zxing/browser` ^0.1.5, `@zxing/library` ^0.21.3 - Barcode/QR scanning
- `browserprint-es` ^0.0.5 - Direct printer control (Zebra)

Shares core deps with main webapp (vue, quasar, pinia, vuex, axios, pdfme, luxon, vue-i18n, vue-cookies, jwt-decode).

## Configuration

**Backend Configuration (`backend/api/utils/config.py`):**
- Pydantic Settings with `PROGRESS_` env prefix
- Docker secrets from `/run/secrets/` directory
- `.env` file support (optional)
- Key settings: `arango_url`, `api_root_path`, `media_path`, `db_name`, `webapp_url`, `nats_url`, `jwt_secret`, `cors_allowed_origins`, `api_db_username`, `api_db_pwd`

**Frontend Configuration:**
- `window.API_CONFIG` object injected via `deploy/config/appConfig.js` (mounted as Docker volume)
- Quasar config at `webapps/main/quasar.config.js`
- Path aliases: `@` -> `./src`, `views` -> `./src/views`
- Boot files loaded in order: store, registerRouter, pinia, i18n, axios, filters, form, theme

**Build Configuration:**
- Browser targets: es2019, edge88, firefox78, chrome87, safari13.1
- Node target: node20
- Vue Router mode: history
- Dark mode enabled by default

## Infrastructure

**Container Images (Production):**
- `python:3.11-slim` - Backend API (`backend/api/Dockerfile`)
- `arangodb:3.11` - Graph database
- `nats:2-alpine` (dev) / `nats:latest` (prod) - Message broker with JetStream enabled
- `traefik:v2.11` - Reverse proxy and load balancer
- `prefecthq/prefect:3-latest` - Workflow server
- `postgres:15.2-alpine` - Workflow database (Prefect backend)
- `quay.io/jupyter/base-notebook` - Jupyter notebooks (optional)
- `python:3.11-slim` - Reporting / Streamlit (optional)
- nginx - Frontend SPA serving (implied by app/warehouse deployment)

**Docker Volumes (all external):**
- `media` - File attachments and uploads
- `db_data` - ArangoDB data
- `db_backup` - ArangoDB backups
- `workflow_db` - PostgreSQL data for Prefect
- `workflow_config` - Prefect configuration
- `flows` - Workflow flow definitions
- `reports` - Streamlit reporting app
- `notebooks` - Jupyter notebooks
- `cmounts` - Customer-specific mount points
- `letsencrypt` - TLS certificates

**CI/CD:**
- GitLab CI/CD (`.gitlab-ci.yml`)
- Docker-in-Docker (docker:24.0.5-dind) for image builds
- GitLab Container Registry at `registry.gitlab.com/progresslab/progress-platform/`
- Version tagging: `v*.*.*` pattern triggers builds (supports `a`, `b`, `rc` pre-release suffixes)
- Built images: `api`, `app`, `warehouse`, `wf-sys-worker`, `print-service`
- Print service also packaged as zip artifact to GitLab generic packages

---

*Stack analysis: 2026-04-15*
