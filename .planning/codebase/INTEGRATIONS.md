# External Integrations

**Analysis Date:** 2026-02-13

## APIs & External Services

**Third-Party API Clients:**
- None detected - No Stripe, SendGrid, Twilio, Slack, or similar SaaS integrations in codebase
- HTTP requests use standard `httpx` and `requests` libraries for generic API calls

**Internal Service Communication:**
- Custom implementations only (`/backend/api/utils/auth.py`, `/backend/api/managers/`)
- No external SaaS integrations for auth, payment, or messaging

## Data Storage

**Databases:**

**Primary - ArangoDB (Graph Database):**
- Provider: Self-hosted ArangoDB 3.11
- Connection: `PROGRESS_ARANGO_URL` env var (default: `http://localhost:8529`)
- Client: `python-arango==8.*` (Python driver)
- Dev mode: Runs without authentication (`ARANGO_NO_AUTH=1`)
- Volumes: `db_data` (persistent storage), `db_backup` (backup directory)
- Collections: WorkOrder, Job, Queue, Product, Phase, Process, Batch, WIP, Event, StepExecutionData, WorkSession, CustomField, Config, Inventory, Movement, Counting, and others (graph relationships maintained via edges)
- Transactional support: Multi-collection transactions via event `apply()` methods in `/backend/api/events/`

**Workflow Database - PostgreSQL:**
- Provider: PostgreSQL 15.2-alpine
- Purpose: Prefect workflow orchestration database
- Connection: `PREFECT_API_DATABASE_CONNECTION_URL=postgresql+asyncpg://postgres:postgres@workflow-db:5432/prefect`
- Used only by Prefect server and workers
- Located at: `/deploy/compose/workflow.yaml` service `workflow-db`
- Credentials: Default postgres user (dev config only)

**File Storage:**
- Local filesystem only
- Media volume: `/media` mounted in `/deploy/compose/base.yaml`
- Path configured via `PROGRESS_MEDIA_PATH` env var (default: `/media`)
- Endpoints: `/backend/api/endpoints/media.py`, `/backend/api/endpoints/file.py`
- Handlers: `utils/media.py` for media operations

**Caching:**
- None detected - No Redis, Memcached, or caching layer implemented
- Database queries executed directly against ArangoDB

## Authentication & Identity

**Auth Provider:**
- Custom implementation (no OAuth2/SAML/third-party provider)
- Location: `/backend/api/utils/auth.py`, `/backend/api/endpoints/auth.py`

**Implementation Details:**
- JWT tokens using HS256 algorithm
- Token secret from docker secret `progress_jwt_secret` (or hardcoded in dev)
- Bcrypt password hashing via `passlib` library
- OAuth2 Bearer token scheme via FastAPI `OAuth2PasswordBearer`
- JWT validation middleware intercepts requests
- Scopes defined for authorization: admin, library, production, operator
- Frontend stores JWT in store and sends via Authorization header in axios interceptors (`/webapps/main/src/boot/axios.js`)

**Password Management:**
- Bcrypt hashing with `passlib==1.7.2`
- Password context configured in `/backend/api/utils/auth.py`

## Monitoring & Observability

**Error Tracking:**
- None detected - No Sentry, Rollbar, or similar error tracking service

**Logs:**
- Console/stdout logging (default FastAPI behavior)
- Structured logging via `logging` module
- Development: JSON-file driver with rotation in `/deploy/compose/dev.yaml`
  - `max-size: "1k"`, `max-file: "3"` for log rotation
- API logs available via docker logs: `docker logs progress_lab_dev-api-1`

**Performance Monitoring:**
- Traefik provides HTTP request metrics on port 8080 (dashboard accessible in dev)
- Kafka JMX metrics exposed on port 9101
- No application-level APM detected

## CI/CD & Deployment

**Hosting:**
- Docker Swarm (production mode via `/deploy/compose/stack.yaml`)
- Could be adapted to Kubernetes
- GitLab Container Registry (images stored in `registry.gitlab.com/progresslab/progress-platform/`)

**CI Pipeline:**
- GitLab CI (`.gitlab-ci.yml`)
- Triggers on semantic version tags: `v[0-9]+.[0-9]+.(a|b|rc)?[0-9]+`
- Build stages:
  - `version-info` - Parse version from git tag
  - `build:webapp` - Build main web app
  - `build:warehouse` - Build warehouse mobile app
  - `build:api` - Build API service
  - `build:workflow` - Build workflow worker service
- Images tagged with both branch version (`$BRANCH_VERSION-latest`) and full version (`$VERSION`)
- All images pushed to `registry.gitlab.com/progresslab/progress-platform/`

**Deployment:**
- Docker Compose files for different environments:
  - `/deploy/compose/base.yaml` - Core services (Traefik, API, DB, Kafka, media)
  - `/deploy/compose/dev.yaml` - Development overrides (source mounts, hot-reload)
  - `/deploy/compose/dev.debug.yaml` - Remote debugging
  - `/deploy/compose/workflow.yaml` - Prefect server + PostgreSQL
  - `/deploy/compose/stack.yaml` - Production swarm deployment
  - `/deploy/compose/kafka.dev.yaml` - Standalone Kafka (KRaft mode)
  - `/deploy/compose/integration.yaml`, `/deploy/compose/reporting.yaml`, `/deploy/compose/notebooks.yaml` - Optional services
- Traefik 2.11 as reverse proxy with Docker provider
- Health checks via docker inspect (not configured in compose)

## Environment Configuration

**Required Environment Variables:**
- `PROGRESS_ARANGO_URL` - ArangoDB connection
- `PROGRESS_DB_NAME` - Database name (PROGRESS_TEST, PROGRESS_PROD, etc.)
- `PROGRESS_MEDIA_PATH` - Media directory path
- `PROGRESS_API_ROOT_PATH` - API root path (default: `/api`)
- `PROGRESS_KAFKA_BOOTSTRAP_SERVER` - Kafka broker address
- `PROGRESS_WEBAPP_URL` - Frontend URL for CORS
- `PREFECT_API_URL` - Prefect workflow server API

**Secrets Location:**
- Docker secrets (production): `/run/secrets/` mounted in containers
  - `progress_api_db_pwd` - ArangoDB password (not used in dev, required in prod)
  - `progress_jwt_secret` - JWT signing secret
  - `progress_admin_pwd` - Admin user password
- .env file (development): `env.dev` provides local defaults
- See `/backend/api/utils/config.py` for Pydantic settings configuration

**Env Var Prefix:**
- All Progress-specific env vars use `PROGRESS_` prefix
- Loaded by Pydantic with `env_prefix="progress_"`
- Can also load from docker secrets directory

## Webhooks & Callbacks

**Incoming:**
- Kafka message consumption via `KafkaConsumerManager` (`/backend/api/managers/kafka_consumer_manager.py`)
- Notification channel subscriptions via WebSocket
- No HTTP webhooks implemented

**Outgoing:**
- Kafka message production via `KafkaProducer` (`/backend/api/utils/kafka/kafka_producer.py`)
- Events streamed to Kafka from all business logic operations
- WebSocket broadcasts to connected clients via `WebsocketManager` (`/backend/api/managers/websocket_manager.py`)

**Kafka Topics:**
- `notifications` - Auto-created on startup via `KafkaAdmin.getInstance().create_topic("notifications")`
- Other topics created dynamically by event system
- Broker: `apache/kafka:latest` in KRaft mode (no ZooKeeper)
- Bootstrap servers:
  - Dev: `broker:19092` (internal docker network)
  - Production: Configured via `PROGRESS_KAFKA_BOOTSTRAP_SERVER` env var

## Event-Driven Architecture

**Event System:**
- Base classes: `/backend/api/events/base_event.py`
- All domain events inherit from base and implement:
  - `get_event_type()` - Returns event type string
  - `get_tx_collections()` - Collections involved in transaction
  - `apply()` - Business logic executed in ArangoDB transaction
- Event types: production, collaboration, work_session, wip, inventory, serial, traceability
- Events persisted in immutable `Event` collection
- Events streamed to Kafka for external consumption/audit

**Workflow Integration:**
- Prefect 3.x orchestration server (`prefecthq/prefect:3-latest`)
- Workflow system worker: `wf-sys-worker` (custom image from `/backend/workflow`)
- Prefect API: `PREFECT_API_URL` configured for workers to connect
- PostgreSQL 15.2 backing Prefect database
- Traefik routes `/workflow/*` to Prefect server on port 4200
- Base path: `/workflow` for UI, `/workflow/api` for API

## Real-Time Communication

**WebSockets:**
- Native FastAPI WebSocket support (`fastapi.WebSocket`)
- Manager: `WebsocketManager` (`/backend/api/managers/websocket_manager.py`)
- Active connection pool maintained in memory
- Messages queued via `asyncio.Queue` with max 100 items
- Used for live notifications and server events
- Frontend receives updates via WebSocket connections (declared in package.json)

**Server-Sent Events (SSE):**
- `sse_starlette` library for SSE endpoints
- Alternative to WebSocket for one-way server-to-client updates
- Endpoint: `/backend/api/endpoints/notification.py`

## Cross-Service Communication

**Internal Service Boundaries:**
- API (`/backend/api`) - REST endpoints, WebSocket, Kafka producer
- Workflow (`/backend/workflow`) - Prefect flows as standalone service
- Frontend (`/webapps/main`, `/webapps/warehouse`) - HTTP/WebSocket clients

**Message Bus:**
- Apache Kafka - Event streaming and async communication
- All business events published to Kafka
- KafkaConsumerManager subscribes to relevant topics
- Enables eventual consistency and event sourcing patterns

## Media & File Handling

**Storage:**
- Local filesystem at `/media` volume (externally managed volume)
- Direct file access via endpoints in `/backend/api/endpoints/file.py`, `/backend/api/endpoints/media.py`
- No CDN or external file storage (S3, Azure Blob, GCS)

**Formats Supported:**
- PDF: Generation via WeasyPrint, PyPDF, ReportLab; viewing via vue-pdf-embed
- Excel: openpyxl for read/write operations
- Images: Handled via file upload/download
- Video: video.js player for streaming

---

*Integration audit: 2026-02-13*
