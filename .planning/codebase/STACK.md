# Technology Stack

**Analysis Date:** 2026-03-12

## Languages

**Primary:**
- **Python 3.11** - Backend API and workflow orchestration
- **JavaScript/Node.js 20.19.0** - Web applications (Quasar-based SPA)
- **Vue.js 3** - Frontend framework for reactive UIs

**Secondary:**
- **YAML** - Docker Compose and deployment configuration

## Runtime

**Environment:**
- **Python 3.11-slim** - Backend container base image from `backend/api/Dockerfile`
- **Node.js 20.19.0** - Web application runtime specified in `.nvmrc` files at `webapps/main/.nvmrc` and `webapps/warehouse/.nvmrc`

**Package Managers:**
- **pip** - Python dependency management with `requirements.txt`
- **Yarn** - Node.js package management with `yarn.lock` at project root
- **npm** - Node.js package manager (minimum version 10.0.0)

## Frameworks

**Backend:**
- **FastAPI 0.x** - Modern async REST API framework at `backend/api/main.py`
- **Starlette** - ASGI framework (dependency of FastAPI)
- **Uvicorn** - ASGI server for running FastAPI applications

**Frontend:**
- **Quasar Framework 2.16.0** - Vue 3-based UI framework with SSR/SPA/PWA support at `webapps/main/` and `webapps/warehouse/`
  - Web application at `webapps/main/` - Main MES/production management interface
  - Mobile application at `webapps/warehouse/` - Mobile warehouse management app with Capacitor integration
- **Pinia 2.1.7** - State management (replacement for Vuex)
- **Vue Router 4.0.0** - Client-side routing
- **Vue I18n 9.0.0** - Internationalization support

**Workflow:**
- **Prefect 3.x** - Workflow orchestration engine in `backend/workflow/`
  - Server image: `prefecthq/prefect:3-latest` at `deploy/compose/workflow.yaml`
  - PostgreSQL 15.2 backend for workflow state

**PDF/Document Generation:**
- **WeasyPrint 66.x** - HTML to PDF conversion at `backend/api/requirements.txt`
- **ReportLab 4.x** - PDF creation library for generated content
- **PyPDF 4.x** - PDF manipulation and merging
- **PDFme 5.5.0** - Client-side PDF template library in both web and warehouse apps

## Key Dependencies

### Backend API (`backend/api/requirements.txt`)

**Database:**
- `python-arango==8.*` - ArangoDB multi-model database client at `backend/api/utils/db.py`

**Web Framework:**
- `fastapi==0.*`
- `starlette>=0.13`
- `uvicorn>=0.11`
- `uvloop>=0.14` - Performance optimization
- `h11==0.*`
- `httptools` - C-accelerated HTTP parsing

**Authentication & Security:**
- `bcrypt==4.3.*` - Password hashing
- `passlib==1.7.2` - Password schemes
- `PyJWT==2.0.*` - JWT token generation and validation
- `python-jose` - JWT/JOSE implementation
- `cryptography==41.0.*` - Cryptographic operations

**Message Queue & Events:**
- `confluent_kafka` - Apache Kafka producer/consumer client at `backend/api/utils/kafka/`

**Real-time Communication:**
- `websockets` - WebSocket protocol support

**PDF Generation:**
- `weasyprint==66.*`
- `reportlab==4.*`
- `pypdf==4.*`

**Data Processing:**
- `openpyxl==3.*` - Excel import/export
- `pydantic==2.*` - Data validation and settings management
- `pydantic-settings==2.*` - Configuration management at `backend/api/utils/config.py`

**Utilities:**
- `httpx==0.*` - HTTP client for async requests
- `python-multipart==0.0.*` - Multipart form data parsing
- `python-dateutil==2.8.*` - Date/time utilities
- `click==7.1.*` - CLI framework
- `six==1.15.0` - Python 2/3 compatibility
- `chardet==3.0.*` - Character encoding detection

**Server:**
- `gunicorn>=20.0` - WSGI HTTP Server

### Workflow Engine (`backend/workflow/requirements.txt`)

- `prefect==3.*` - Workflow orchestration framework
- `python-arango==8.*` - Database access for workflow state
- `httpx` - HTTP client for async operations

### Frontend Web App (`webapps/main/package.json`)

**Core UI:**
- `vue@3.4.18` - Progressive JavaScript framework
- `quasar@2.16.0` - Vue 3 UI component framework
- `vue-router@4.0.0` - Client-side routing
- `pinia@2.1.7` - State management

**HTTP & Real-time:**
- `axios@1.7.0` - HTTP client library
- `socket.io-client@4.7.5` - WebSocket client for real-time communication
- `vue-sse@2.5.2` - Server-Sent Events support

**PDF & Document:**
- `@pdfme/ui@5.5.0` - PDF template editor UI
- `@pdfme/generator@5.5.0` - PDF generation
- `@pdfme/schemas@5.5.0` - PDF template schemas
- `@pdfme/common@5.5.0` - Common utilities
- `vue-pdf-embed@1.1.6` - PDF viewer component

**Code Editing:**
- `codemirror@6.0.1` - Advanced code editor
- `@codemirror/*` - Syntax highlighting, language support, linting

**Utilities:**
- `luxon@3.0.4` - DateTime manipulation
- `xlsx@0.18.5` - Excel file handling
- `vue-i18n@9.0.0` - Internationalization
- `vue-cookies@1.8.4` - Cookie management
- `sortablejs@1.15.0` - Drag-and-drop lists
- `video.js@8.17.4` - HTML5 video player
- `file-saver@2.0.5` - Save files client-side
- `jwt-decode@3.1.2` - JWT token parsing
- `@vueuse/core@11.1.0` - Vue 3 composition function utilities

**Build & Dev:**
- `@quasar/app-vite@2.0.0` - Vite-based Quasar CLI
- `vite@5.4.0` - Frontend build tool
- `esbuild@0.21.0` - JavaScript bundler

**Code Quality:**
- `eslint@8.57.0` - JavaScript linter
- `prettier@3.1.1` - Code formatter
- `postcss@8.4.14` - CSS transformations

### Warehouse Mobile App (`webapps/warehouse/package.json`)

Extends web app with:

**Mobile/Native:**
- `@capacitor/core@6.0.0` - Native bridge for mobile features
- `@capacitor/cli@6.0.0` - Capacitor CLI
- `@capacitor/app@6.0.0` - App lifecycle management
- `@capacitor/splash-screen@6.0.0` - Splash screen control

**Hardware:**
- `@zxing/browser@0.1.5` - Barcode/QR code reading from camera
- `@zxing/library@0.21.3` - ZXing library for barcode decoding
- `browserprint-es@0.0.5` - Direct printer control

(Shares other dependencies with main web app)

## Configuration

**Environment Variables:**
- Backend configuration via `PROGRESS_*` prefixed environment variables at `backend/api/utils/config.py`
- Key settings: `PROGRESS_ARANGO_URL`, `PROGRESS_MEDIA_PATH`, `PROGRESS_API_ROOT_PATH`, `PROGRESS_DB_NAME`
- Docker secrets for sensitive values: `progress_api_db_pwd`, `progress_admin_pwd`, `progress_jwt_secret`
- Frontend configuration via `window.API_CONFIG` object injected from `deploy/config/appConfig.js`

**Build Configuration:**
- **Frontend:** Quasar config at `webapps/main/quasar.config.js`
- **Backend:** Python module loading, no explicit build configuration
- **ESLint:** `.eslintrc.js` at `webapps/main/.eslintrc.js`
- **Prettier:** `.prettierrc.json` at `webapps/main/.prettierrc.json` and `webapps/warehouse/.prettierrc`

## Platform Requirements

**Development:**
- Docker and Docker Compose (as per readme.md)
- Docker volumes for: `media`, `db_data`, `db_backup`, `logs`
- Python 3.11 (backend)
- Node.js 20.19.0+ (webapps)
- Yarn package manager

**Production:**
- Docker and Docker Compose orchestration
- Kubernetes-ready deployment via Traefik reverse proxy at `deploy/compose/base.yaml`
- External volumes for persistent data
- GitLab CI/CD pipeline at `.gitlab-ci.yml` for Docker image builds
- GitLab registry for image storage

## Build & Deployment

**Container Images:**
- `python:3.11-slim` - Backend API
- `arangodb:3.11` - Database (Intel and ARM64 variants available)
- `apache/kafka:latest` - Message broker
- `traefik:v2.11` - Reverse proxy
- `prefecthq/prefect:3-latest` - Workflow server
- `postgres:15.2-alpine` - Workflow database
- Custom images built via GitLab CI at `registry.gitlab.com/progresslab/progress-platform/`

**Build Process:**
- GitLab CI with Docker-in-Docker for building container images
- Version-based tagging with semantic versioning
- Push to GitLab registry on version tags matching `v*.*.*` pattern

---

*Stack analysis: 2026-03-12*
