# Technology Stack

**Analysis Date:** 2026-02-13

## Languages

**Primary:**
- Python 3.11 - Backend API and workflow services (`/backend/api`, `/backend/workflow`)
- JavaScript/ES6+ - Frontend webapps and testing (`/webapps/main`, `/webapps/warehouse`, `/testing`)
- Vue 3 - Frontend component framework with Composition API

**Secondary:**
- AQL - ArangoDB query language (`/db/migrations`)
- Robot Framework - BDD testing framework (`/testing/robot-test`)

## Runtime

**Environment:**
- Node.js 20.19.0 (specified in `.nvmrc`)
- Python 3.11 (specified in `/backend/.python-version`)
- Docker containerization (all services run in Docker Compose)

**Package Managers:**
- npm/yarn for Node.js projects (main app `engine: "node": "^20.19.0 || ^22"`, warehouse `engine: "node": "^20.19.0 || ^22"`)
- pip for Python projects
- Lockfiles: `yarn.lock` present at project root

## Frameworks

**Backend:**
- FastAPI 0.x - REST API framework (`/backend/api/main.py`)
- Uvicorn/Gunicorn - ASGI web server
- Prefect 3.x - Workflow orchestration (`/backend/workflow`, prefect image: `prefecthq/prefect:3-latest`)

**Frontend:**
- Quasar 2.16+ - Vue 3 UI framework with integrated build tools
  - Main app: v2.16.0 (`/webapps/main`)
  - Warehouse: v2.16.0 (`/webapps/warehouse`)
- Pinia 2.x - State management (`pinia: ^2.1.7`, `pinia: ^2.0.11`)
- Vue Router 4.x - Client-side routing
- Vue I18n 9.0.0 - Internationalization (English, Italian)

**Testing:**
- Mocha 10.2.0 - JavaScript test runner (`/testing/package.json`)
- Chai 4.3.7 - Assertion library
- Cypress 13.10.0 - E2E testing
- Robot Framework - BDD/keyword-driven testing (`/testing/robot-test`)

**Build/Dev:**
- Vite 5.4.0 - Frontend bundler
- Quasar CLI/App Vite 2.x - Quasar build system
- ESLint 8.57.0 - JavaScript linting (`.eslintrc.js`)
- Prettier 3.1.1 (main), 2.5.1 (warehouse) - Code formatting
- PostCSS 8.4.14 - CSS processing
- Esbuild 0.21.0 - JavaScript bundler

## Key Dependencies

**Critical Backend:**
- `python-arango==8.*` - ArangoDB Python driver (`/backend/api/requirements.txt`)
- `pydantic==2.*` - Data validation using Python type annotations (`/backend/api/requirements.txt`)
- `pydantic-settings==2.*` - Configuration management from environment (`/backend/api/requirements.txt`)
- `confluent_kafka` - Kafka producer/consumer (`/backend/api/requirements.txt`)
- `PyJWT==2.0.*` - JWT token handling for authentication (`/backend/api/requirements.txt`)
- `passlib==1.7.2` - Password hashing with bcrypt (`/backend/api/requirements.txt`)
- `websockets` - WebSocket support for real-time updates
- `sse_starlette` - Server-sent events support
- `python-jose` - JOSE (JWT) implementation
- `httpx==0.*` - Async HTTP client (`/backend/api/requirements.txt`)

**PDF & Document Generation:**
- `weasyprint==66.*` - HTML to PDF conversion
- `pypdf==4.*` - PDF manipulation
- `reportlab==4.*` - PDF generation
- `openpyxl==3.*` - Excel file handling

**Frontend:**
- `axios: ^1.7.0` - HTTP client for API calls
- `socket.io-client: ^4.7.5` - WebSocket client (unused in current exploration but declared)
- `vue-sse: ^2.5.2` - Server-sent events client
- `@pdfme/common`, `@pdfme/generator`, `@pdfme/schemas`, `@pdfme/ui: ^5.5.0` - PDF template engine (recently upgraded to v5)
- `vue-pdf-embed: 1.1.6` - PDF viewing component
- `vue-router: ^4.0.0` - Routing
- `vue-i18n: ^9.0.0` - Translation framework
- `luxon: ^3.0.4` - Date/time manipulation
- `sortablejs: ^1.15.0` - Drag-and-drop list reordering
- `file-saver: ^2.0.5` - File download utilities
- `xlsx: ^0.18.5` - Excel file handling
- `jwt-decode: ^3.1.2` - JWT parsing (without verification)
- `video.js: ^8.17.4` - Video player
- `codemirror: ^6.0.1` - Code editor
- `@vueuse/core: ^11.1.0` - Vue composables utility library

**Warehouse App Specific:**
- `@capacitor/core, @capacitor/app, @capacitor/cli, @capacitor/splash-screen: ^6.0.0` - Capacitor for mobile (Android)
- `@zxing/browser, @zxing/library: ^0.21.3` - Barcode/QR code scanning
- `browserprint-es: ^0.0.5` - Print functionality

## Configuration

**Environment:**
- Configuration loaded via Pydantic Settings with environment prefix `PROGRESS_` (see `/backend/api/utils/config.py`)
- Environment variables or `.env` file support
- Docker secrets support for sensitive values (jwt_secret, admin_pwd, api_db_pwd)
- .env file support documented in `env.dev`

**Key Configuration Variables:**
- `PROGRESS_ARANGO_URL` - ArangoDB connection URL (default: `http://localhost:8529`)
- `PROGRESS_DB_NAME` - Database name selection (dev: `PROGRESS_TEST`, prod: `PROGRESS_PROD`)
- `PROGRESS_API_DB_PWD` - Database password (docker secret)
- `PROGRESS_MEDIA_PATH` - Media files directory (default: `/media`)
- `PROGRESS_KAFKA_BOOTSTRAP_SERVER` - Kafka broker (default: `broker:19092`)
- `PROGRESS_WEBAPP_URL` - Frontend URL for CORS and redirects

**Build:**
- `Dockerfile` in `/backend/api` - Python 3.11-slim with system deps for WeasyPrint
- `webapp.prod.Dockerfile` in `/webapps/main` - Production build
- `Dockerfile` in `/webapps/warehouse` - Warehouse app build
- ESLint config: `.eslintrc.js` in webapps
- Prettier config: `.prettierrc.json` (single quotes enabled)

## Platform Requirements

**Development:**
- Docker & Docker Compose
- Node.js 20.19.0 (or 22+)
- Python 3.11
- ArangoDB 3.11 (Intel/x86_64 or arm64v8 for M1-M3 Apple Silicon)
- Apache Kafka (latest, KRaft mode - no ZooKeeper)
- PostgreSQL 15.2 (for Prefect workflow database)
- Traefik 2.11 (reverse proxy/load balancer)

**Production:**
- Docker Swarm or Kubernetes deployment
- GitLab Container Registry for image storage
- All services containerized and orchestrated
- Production compose files: `/deploy/compose/stack.yaml`, `/deploy/compose/stack-dev.yaml`
- TLS support available via `/deploy/compose/tls.yaml`

## Key Service Versions

- **ArangoDB:** 3.11 (Intel: `arangodb:3.11`, ARM: `arm64v8/arangodb:3.11`)
- **Apache Kafka:** latest (KRaft mode, no ZooKeeper required)
- **PostgreSQL:** 15.2-alpine (for Prefect)
- **Prefect:** 3.x (`prefecthq/prefect:3-latest`)
- **Traefik:** 2.11
- **Docker:** 24.0.5

## Lockfiles & Dependency Management

- `yarn.lock` present at project root (for Node.js monorepo)
- Python requirements split by service:
  - `/backend/api/requirements.txt` - API dependencies
  - `/backend/workflow/requirements.txt` - Workflow service dependencies
  - `/testing/robot-test/requirements.txt` - Testing dependencies
- Node dependencies managed per webapp:
  - `/webapps/main/package.json`
  - `/webapps/warehouse/package.json`
  - `/testing/package.json`

---

*Stack analysis: 2026-02-13*
