# External Integrations

**Analysis Date:** 2026-04-15

## APIs & External Services

**Prefect Workflow API:**
- Service: Prefect 3.x Workflow Orchestration
- Purpose: Schedule, deploy, and monitor automated workflows
- SDK/Client: `prefect==3.*` in `backend/workflow/requirements.txt`
- Endpoint: Configured via `PREFECT_API_URL` env var (default `http://wf-server:4200/workflow/api`)
- Frontend access: Proxied through Traefik at `/wf-api` path (rewritten to `/workflow/api`)
- UI: Prefect dashboard served at `/workflow/` path
- Database: PostgreSQL 15.2 at `postgresql+asyncpg://postgres:postgres@workflow-db:5432/prefect`

**Backend API (Internal):**
- Service: FastAPI REST API at `backend/api/main.py`
- Purpose: Central service for all business logic, data operations, and integrations
- Routers registered in `backend/api/main.py` (lines 59-79):
  - `endpoints.admin` - Administration
  - `endpoints.auth` - Security (OAuth2 password grant)
  - `endpoints.bom` - Bill of Materials (prefix `/product`)
  - `endpoints.config` - Administration config
  - `endpoints.file` - Attachments
  - `endpoints.form` - Quality forms
  - `endpoints.serial` - Serial number management
  - `endpoints.media` - Media attachments
  - `endpoints.org` - Organization
  - `endpoints.print` - Print/label operations
  - `endpoints.process` - Process definitions
  - `endpoints.product` - Product management (prefix `/product`)
  - `endpoints.production` - Production operations
  - `endpoints.tag` - Tagging
  - `endpoints.collaboration` - Collaboration
  - `endpoints.traceability` - Traceability
  - `endpoints.counter` - Counter generation
  - `endpoints.notification` - SSE notification streaming
  - `endpoints.inventory` - Warehouse inventory
  - `endpoints.counting` - Warehouse counting
- Access: Axios HTTP client from frontends at `webapps/main/src/boot/axios.js`
- Health check: `GET /hello` (unauthenticated)

## Data Storage

**Primary Database - ArangoDB 3.11:**
- Type: Multi-model (document + graph + search)
- Client: `python-arango==8.*` at `backend/api/utils/db.py`
- Connection: `ArangoClient(hosts=conf.arango_url, serializer=encoder)`
- Auth: `db = client.db(conf.db_name, username=conf.api_db_username, password=conf.api_db_pwd)`
- Config env vars: `PROGRESS_ARANGO_URL` (default `http://localhost:8529`), `PROGRESS_DB_NAME` (default `PROGRESS_TEST`)
- Production DB name: `PROGRESS_PROD` (set in `deploy/compose/dev.yaml` and `deploy/compose/stack.yaml`)
- Dev mode: `ARANGO_NO_AUTH=1` (no auth in dev compose)
- Production auth: `ARANGO_ROOT_PASSWORD_FILE=/run/secrets/progress_db_root_pwd`
- Web UI: Exposed through Traefik at `/_db` path
- Volumes: `db_data` (data), `db_backup` (backups)
- Custom serializer in `backend/api/utils/db.py`: strips null `_id`/`_key` fields, uses `jsonable_encoder`

**Workflow Database - PostgreSQL 15.2-alpine:**
- Purpose: Prefect workflow engine state storage
- Service: `workflow-db` in `deploy/compose/workflow.yaml`
- Connection: `postgresql+asyncpg://postgres:postgres@workflow-db:5432/prefect`
- Volume: `workflow_db` for persistent data

**File Storage:**
- Local filesystem via Docker volume `media` mounted at `PROGRESS_MEDIA_PATH` (default `/media`)
- Upload endpoint: `backend/api/endpoints/media.py`
- Frontend access: Files served directly by FastAPI and also mounted into app/warehouse nginx containers
- Backup volume: `db_backup` for ArangoDB backups

**Caching:**
- None - no Redis or external caching layer

## Message Broker - NATS

**Service:**
- Image: `nats:2-alpine` (dev) / `nats:latest` (base)
- JetStream enabled via `-js` flag
- Ports: 4222 (client), 8222 (monitoring)
- Hostname: `broker`
- Config env var: `PROGRESS_NATS_URL` (default `nats://broker:4222`)

**Backend Client (`backend/api/utils/nats_client.py`):**
- Module-level singleton `NatsClient` with auto-reconnect (`max_reconnect_attempts=-1`, `reconnect_time_wait=2`)
- Connected at startup in `backend/api/main.py` line 45
- Supports both async (`publish()`) and sync-from-async (`publish_sync()`) publishing
- Request-reply pattern via `request()` method
- Graceful shutdown: `drain()` with 5-second timeout, fallback to `close()`

**Topic Structure:**
- `progress.notification.inventory` - Inventory change notifications
- `progress.notification.serial` - Serial number notifications
- `progress.notification.task` - Task notifications
- `progress.notification.production` - Production notifications
- `progress.notification.message` - Chat/messaging notifications
- `progress.notification.>` - Wildcard subscription for all notifications (used by API server)

**Event Flow (NATS -> SSE):**
1. Backend event/manager publishes to NATS subject via `nats_client.publish_sync()` or `nats_client.publish()`
2. API server's wildcard subscription (`progress.notification.>`) receives message
3. `ServerEventManager.enqueue()` dispatches to per-topic async queues
4. SSE endpoint streams events to connected frontend clients via `push_events()` generator
5. Supports exact-topic and wildcard fan-out (`{prefix}:*` pattern) for client subscriptions

**Print Service (`backend/print-service/main.py`):**
- Separate NATS client connecting to broker
- Subscribes to print-related subjects
- Uses NATS request-reply for print job communication

## Authentication & Identity

**Auth Provider: Custom JWT-based**
- Implementation: `backend/api/utils/auth.py`
- Algorithm: HS256
- Token URL: `/api/auth` (OAuth2 password grant)
- Secret: `progress_jwt_secret` Docker secret, loaded via `get_config().jwt_secret`

**Token Lifecycle:**
- Generation: `issue_token()` creates JWT with `token_key`, `consumer_key`, `consumer_type`, `context`, `scope`, `issued_at`, `expires_at`
- Storage: Token records stored in ArangoDB `Token` collection
- Verification: `verify_token()` FastAPI dependency checks JWT signature, DB record existence, signature match, and revocation status
- Revocation: `revoke_token()` sets `revoked=True` in DB
- Sessions: `UserSession` collection tracks login/logout with `close_session()` transaction

**Token Contexts:**
- `TokenContext.USER_SESSION` - Regular user authentication
- `TokenContext.API` - Service tokens (cannot use user endpoints)

**Scopes:**
- `admin` - System settings and user management
- `library` - Product management
- `production` - Production plan access
- `operator` - Operator panel and declarations
- `print_service` - Print service authentication (verified via `verify_print_service_token()`)

**ACL System:**
- Permission-based access control via `configure_permissions()` / `Permission` dependency
- ACL tuples: `(Allow/Deny, principal, permissions)`
- Built-in principals: `Everyone`, `Authenticated`
- Wildcard: `_AllPermissions` class matches any permission check

**Frontend Integration:**
- JWT stored in Vuex store state
- Axios request interceptor adds `Authorization: Bearer {token}` header (`webapps/main/src/boot/axios.js`)
- 401 responses trigger automatic logout (except `whoami` and `session` endpoints)
- Client-side decode via `jwt-decode` ^3.1.2

## Real-time Communication

**Server-Sent Events (SSE) - Primary:**
- Backend: `ServerEventManager` singleton at `backend/api/managers/server_event_manager.py`
- Pattern: Per-topic async queues, 14-second keepalive timeout with SSE comments
- Frontend: `vue-sse` ^2.5.2 for SSE consumption
- Endpoint: `endpoints.notification` router

**Socket.IO - Legacy:**
- `socket.io-client` ^4.7.5 still in frontend dependencies
- No Socket.IO server detected in backend - SSE has replaced WebSocket for notifications

## Monitoring & Observability

**Error Tracking:**
- None - no Sentry or similar service integration

**Logs:**
- Docker JSON file driver (dev: max 1k size, 3 files)
- Vector log aggregator available at `deploy/config/vector.toml`
- Python `logging` module for application logs
- Gunicorn access logs to stdout (`--access-logfile -` in production)

**Metrics:**
- Prometheus config at `deploy/config/prometheus.yml` scraping ArangoDB metrics
- Traefik dashboard at port 8080 (dev) for routing metrics

## Reverse Proxy - Traefik v2.11

**Routing Rules (Docker labels):**
- `/api` -> `api:8000` (strip prefix)
- `/` -> `app:80` (main webapp, lowest priority)
- `/wh` -> `warehouse:80` (strip prefix)
- `/workflow` -> `wf-server:4200` (Prefect UI)
- `/wf-api` -> `wf-server:4200/workflow/api` (API bypass for CORS)
- `/_db` -> `db:8529` (ArangoDB web UI)
- `/reports` -> `reporting:8501` (Streamlit, iframe-only)
- `/notebooks` -> `notebooks:8888` (Jupyter)

**TLS (`deploy/compose/tls.yaml`):**
- Let's Encrypt automatic certificates (HTTP challenge)
- Custom certificate support via file provider
- HTTP-to-HTTPS redirect
- Per-service TLS configuration via router labels

## CI/CD & Deployment

**Hosting:**
- Docker Swarm (production) - indicated by `swarmMode` in stack.yaml Traefik config
- Docker Compose (development) - `deploy/compose/dev.yaml`

**CI Pipeline (`.gitlab-ci.yml`):**
- GitLab CI with Docker-in-Docker (docker:24.0.5-dind)
- Triggers on version tags matching `v[0-9]+.[0-9]+.(a|b|rc)?[0-9]+`
- Stages: `.pre` (version extraction), `build` (Docker images), `package` (artifacts)
- Built services: `app`, `warehouse`, `api`, `wf-sys-worker`, `print-service`
- Tagging: `{MAJOR.MINOR}-latest` and exact version tags
- Registry: `registry.gitlab.com/progresslab/progress-platform/`
- Print service additionally packaged as zip to GitLab generic packages

## Environment Configuration

**Required env vars (backend):**
- `PROGRESS_ARANGO_URL` - ArangoDB connection (default: `http://localhost:8529`)
- `PROGRESS_DB_NAME` - Database name (default: `PROGRESS_TEST`)
- `PROGRESS_MEDIA_PATH` - Media storage path (default: `/media`)
- `PROGRESS_API_ROOT_PATH` - API prefix (default: `/api`)
- `PROGRESS_NATS_URL` - NATS broker URL (default: `nats://broker:4222`)

**Docker secrets (production):**
- `progress_api_db_pwd` - Database password
- `progress_admin_pwd` - Admin user password
- `progress_jwt_secret` - JWT signing secret
- `progress_db_root_pwd` - ArangoDB root password

**Deployment env vars:**
- `VERSION` - Image tag for deployment
- `HOST` - Hostname for Traefik routing rules
- `PROTOCOL` - `http` or `https` (default: `https`)
- `PREFECT_API_URL` - Workflow server endpoint
- `TLS_EMAIL` - Let's Encrypt registration email

**Frontend configuration:**
- `window.API_CONFIG` injected at runtime via `/config.js` (mounted from `deploy/config/appConfig.js`)
- Properties: `baseURL` (API host), `basePath` (API prefix, normally `/api`)
- Fallback: localhost detection in `webapps/main/src/boot/axios.js`

---

*Integration audit: 2026-04-15*
