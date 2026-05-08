# External Integrations

**Analysis Date:** 2026-05-08

## APIs & External Services

**Prefect Workflow Orchestration:**
- Service: Prefect 3.x workflow server
- Purpose: Schedule, deploy, and monitor automated workflows
- SDK/Client: `prefect==3.*` in `backend/workflow/requirements.txt`
- Server deployment: `deploy/compose/workflow.yaml` (Prefect 3 image)
- API endpoint: `http://wf-server:4200/workflow/api` (configured via `PREFECT_API_URL`)
- Frontend access: Traefik routes `/workflow` → `wf-server:4200`, `/wf-api` → `wf-server:4200/workflow/api`
- Database: PostgreSQL 15.2 at `postgresql+asyncpg://postgres:postgres@workflow-db:5432/prefect`
- Flow definitions: External volume `flows` mounted in workflow container

**Progress Platform API (Internal):**
- Service: FastAPI REST at `backend/api/main.py`
- Purpose: Central business logic, data operations, event management
- Routers in `backend/api/main.py` lines 112-132:
  - `admin`, `auth`, `bom`, `config`, `file`, `form`, `serial`, `media`, `org`, `print`, `process`, `product`, `production`, `tag`, `collaboration`, `traceability`, `counter`, `notification`, `inventory`, `counting`
- Client: Axios from `webapps/main/src/boot/axios.js` and `webapps/warehouse/`
- Health check: `GET /hello` (public)

## Message Broker - NATS JetStream (Canonical)

**Service:**
- Image: `nats:2-alpine` (dev) / `nats:latest` (production)
- JetStream enabled via `-js` flag (persistent event streaming)
- Ports: 4222 (client), 1883 (MQTT bridge), 8222 (monitoring)
- Hostname: `broker` in Docker Compose
- Config: `PROGRESS_NATS_URL` env var (default `nats://broker:4222`)

**Backend Client (`backend/api/utils/nats_client.py`):**
- Module-level singleton `NatsClient` with auto-reconnect (max_reconnect_attempts=-1, reconnect_time_wait=2s)
- Connected at startup in `backend/api/main.py` line 98
- Async publishing: `publish(subject, data)`
- Sync-from-async: `publish_sync(subject, data)` (via asyncio.run_coroutine_threadsafe)
- Request-reply pattern: `request(subject, data, timeout=10.0)`
- Graceful shutdown: `drain()` with subscription cleanup
- Wildcard subscription at startup: `progress.notification.>` (all notification topics)

**Topic Structure (Legacy Naming → NATS Subjects):**
- `progress.notification.inventory` - Inventory position changes
- `progress.notification.serial` - Serial traceability updates
- `progress.notification.task` - Collaboration tasks
- `progress.notification.production` - Production job/batch events
- `progress.notification.message` - Chat/messaging
- `progress.notification.health.sparkplug.bridge` - Sparkplug bridge healthcheck
- `progress.notification.health.sparkplug.historian` - Sparkplug historian healthcheck
- Generic format: `progress.sparkplug.*` - Sparkplug B metric events (from MQTT bridge)

**Event Flow (NATS → SSE → Frontend):**
1. Backend event/manager publishes to NATS via `nats_client.publish_sync()` or async `publish()`
2. API startup subscription (`progress.notification.>`) receives all messages
3. `ServerEventManager.enqueue()` dispatches to per-topic async queues
4. SSE endpoint streams events to connected clients via `push_events()` generator
5. Frontend `vue-sse` consumes stream; wildcard subscriptions with `{prefix}:*` fan-out

**Print Service Integration:**
- Separate `nats-py` client in `backend/print-service/main.py`
- Subscribes to print-related NATS subjects
- Request-reply pattern for print job dispatch (timeout configurable per job copies)

**Deprecated Kafka (Legacy - Do Not Use):**
- `confluent-kafka` present in test suite `testing/pytest/pyproject.toml` line 29
- No active usage in production code; treat as dead code left over from migration to NATS
- All new event publishing must use NATS

## IoT & Industrial Automation - Sparkplug B Bridge

**Service: Sparkplug B MQTT ↔ NATS Bridge**
- Container: `progress-sparkplug-bridge:dev` (built from `backend/sparkplug_bridge/Dockerfile`)
- Location: `backend/sparkplug_bridge/main.py`
- Purpose: Bridge industrial MQTT devices (Sparkplug B v1.0 spec) to NATS events
- Startup dependencies: NATS broker healthy, MQTT broker healthy
- Healthcheck: Verifies heartbeat on `progress.notification.health.sparkplug.bridge` (every 5s, timeout 8s)

**Configuration (`backend/sparkplug_bridge/config.py`):**
- MQTT URL: `PROGRESS_MQTT_URL` (default `tcp://broker:1883`)
- NATS URL: `PROGRESS_NATS_URL` (default `nats://broker:4222`)
- MQTT client ID: `PROGRESS_MQTT_CLIENT_ID`
- Host ID: `PROGRESS_BRIDGE_HOST_ID`
- Heartbeat interval: `PROGRESS_BRIDGE_HEARTBEAT_INTERVAL_SEC` (default 5s)
- Gap tolerance: `PROGRESS_BRIDGE_GAP_TOLERANCE`, `PROGRESS_BRIDGE_GAP_WINDOW_SEC`

**MQTT/Sparkplug Ingest (`backend/sparkplug_bridge/subscriber.py`):**
- Async MQTT client: `aiomqtt 2.5.1` with SSL/TLS support
- Topic subscription: `spBv1.0/#` (all Sparkplug B messages)
- Message types: NBIRTH (Node Birth), NDATA (Node Data), NDEATH (Node Death), DBIRTH (Device Birth), DDATA (Device Data), DDEATH (Device Death)
- Decoding: Vendored Eclipse Tahu protobuf (protobuf >=5.28.2)
- INGEST-07: Bounded asyncio.Queue (depth 256, drop-oldest policy)

**Decoding & State Management (`backend/sparkplug_bridge/decoder.py`, `session_state.py`):**
- Protobuf message decoding to JSON
- Metric alias resolution (dynamic tag number → metric name mapping)
- Session state machine: bdSeq tracking per NBIRTH/NDEATH cycles
- Stale metric detection and propagation
- State persistence: KV bucket caches for aliases, session state, metric values

**NATS Publishing (`backend/sparkplug_bridge/publisher.py`):**
- Metric BIRTH: `progress.sparkplug.nodes.{group}.{edge}` (NBIRTH payloads)
- Metric DATA: `progress.sparkplug.metrics.{group}.{edge}.[{device}].{metric_name}` (NDATA/DDATA)
- Session online/offline: `progress.sparkplug.sessions.{group}.{edge}.{state}`
- Cascade detection on NDEATH: fanout stale metrics to downstream systems

**Historian Integration (`backend/sparkplug_bridge/historian/`):**
- Service: `historian_ingester` container (same image as sparkplug_bridge, different entrypoint)
- Purpose: Persist Sparkplug B metrics to TimescaleDB for historical queries and dashboards
- Startup: `python -m sparkplug_bridge.historian`
- Healthcheck: Verifies heartbeat on `progress.notification.health.sparkplug.historian`
- Configuration (`historian/config.py`):
  - Admin URL: `PROGRESS_HISTORIAN_ADMIN_URL` (PostgreSQL system DB for setup)
  - DB URL: `PROGRESS_HISTORIAN_DB_URL` (progress_historian database)
  - Database name: `PROGRESS_HISTORIAN_DB_NAME` (default `progress_historian`)
  - Batch size: `PROGRESS_HISTORIAN_BATCH_SIZE` (default 500 rows)
  - Flush interval: `PROGRESS_HISTORIAN_FLUSH_MS` (default 100ms)
  - Heartbeat: `PROGRESS_HISTORIAN_HEARTBEAT_INTERVAL_SEC` (default 5s)
- Bootstrap (`historian/bootstrap.py`):
  - Creates database and `progress_historian` user on first run
  - Creates TimescaleDB extension (version check, skip if already installed)
  - Idempotent DDL: `CREATE DATABASE IF NOT EXISTS`, `CREATE EXTENSION IF NOT EXISTS timescaledb`
- Schema (`historian/schema.py`):
  - `metric_samples` hypertable (time-series optimized)
  - Compression policies (automatic per TimescaleDB best practices)
  - Continuous aggregates for downsampling (1m, 1h, 1d buckets)
  - Indexes on (device_id, metric_name, time)
- Ingestion subscriber (`historian/ingester.py`):
  - Consumes from NATS topics: `progress.sparkplug.metrics.>` (all metric DATA events)
  - Batches inserts: collects up to `BATCH_SIZE` rows before flush
  - Async insert: `INSERT INTO metric_samples (...)` at configured interval

**Simulator (`backend/sparkplug_bridge/simulator/`):**
- Service: Optional `sparkplug_sim` container for UAT/testing
- Purpose: Generates synthetic Sparkplug B NBIRTH/NDATA/NDEATH messages
- Configuration: `simulator/scenario.yaml` (topology, metrics, sequences)
- Runtime: Loops topology, publishes to MQTT at configured interval

## Data Storage

**Primary Database - ArangoDB 3.11:**
- Type: Multi-model (document + graph + search)
- Image: `arangodb:3.11`
- Client: `python-arango==8.*` at `backend/api/utils/db.py`
- Connection: `ArangoClient(hosts=conf.arango_url, serializer=encoder)`
- Authentication: `db = client.db(conf.db_name, username=conf.api_db_username, password=conf.api_db_pwd)`
- Config env vars:
  - `PROGRESS_ARANGO_URL` (default `http://localhost:8529`)
  - `PROGRESS_DB_NAME` (default `PROGRESS_TEST`; production: `PROGRESS_PROD`)
  - `PROGRESS_API_DB_USERNAME`, `PROGRESS_API_DB_PWD`
- Development: `ARANGO_NO_AUTH=1` in `deploy/compose/dev.yaml`
- Production auth: `/run/secrets/progress_db_root_pwd` mounted as secret
- Web UI: Traefik routes `/_db` → `db:8529/`
- Volumes: `db_data` (persistent), `db_backup` (backups)
- Custom serializer: Strips null `_id`/`_key` fields using `jsonable_encoder` from Pydantic

**Workflow Database - PostgreSQL 15.2-alpine + TimescaleDB:**
- Purpose: Prefect workflow engine state + Sparkplug historian metrics
- Service name: `workflow-db` in `deploy/compose/workflow.yaml`
- Connection string: `postgresql+asyncpg://postgres:postgres@workflow-db:5432/prefect` (Prefect)
- Historian connection: `postgresql://postgres:postgres@workflow-db:5432/progress_historian`
- Volume: `workflow_db` for persistent data
- TimescaleDB extension: Enables hypertable for time-series metrics (`metric_samples`)

**File Storage:**
- Type: Local filesystem via Docker volume
- Volume name: `media`
- Mount point: `PROGRESS_MEDIA_PATH` (default `/media`)
- Upload endpoint: `backend/api/endpoints/media.py` (multipart form handling)
- Access:
  - FastAPI direct file serving (via starlette.staticfiles or FastAPI FileResponse)
  - Mounted into webapp containers (`app`, `warehouse`) for static serving
- Backup: Separate `db_backup` volume for ArangoDB snapshots

**Caching:**
- None - no Redis, Memcached, or external cache layer
- Application state managed via ArangoDB + NATS event streams

## Authentication & Identity

**Auth Provider: Custom JWT-based**
- Implementation: `backend/api/utils/auth.py`
- Algorithm: HS256 (symmetric)
- Token endpoint: `POST /api/auth` (OAuth2 password grant)
- Secret: `progress_jwt_secret` Docker secret, loaded via `get_config().jwt_secret`

**Token Lifecycle:**
- **Generation** (`issue_token()`): Creates JWT with claims:
  - `token_key`, `consumer_key`, `consumer_type`, `context`, `scope`, `issued_at`, `expires_at`
  - Records token in ArangoDB `Token` collection
- **Verification** (`verify_token()` FastAPI dependency):
  - Checks JWT signature (HS256)
  - Verifies DB record existence
  - Checks signature match and revocation status
- **Revocation** (`revoke_token()`): Sets `revoked=True` in Token document
- **Sessions** (`UserSession` collection):
  - Tracks login/logout; `close_session()` atomically updates
  - Used for session-based access control

**Token Contexts:**
- `TokenContext.USER_SESSION` - User authentication
- `TokenContext.API` - Service tokens (cannot use user endpoints)

**Scopes:**
- `admin` - System settings, user management
- `library` - Product management
- `production` - Production plan access
- `operator` - Operator panel and shift declarations
- `print_service` - Print service authentication

**ACL System:**
- Permission-based via `configure_permissions()` / `Permission` dependency
- ACL tuples: `(Allow/Deny, principal, permissions)`
- Built-in principals: `Everyone`, `Authenticated`
- Wildcard principal: `_AllPermissions` (matches any permission check)

**Frontend Integration:**
- JWT storage: Vuex store state (legacy, migrate to Pinia)
- Axios interceptor: Adds `Authorization: Bearer {token}` header (boot/axios.js)
- Auto-logout: 401 responses trigger logout (except `whoami`, `session` endpoints)
- Client decode: `jwt-decode` ^3.1.2

## Real-time Communication

**Server-Sent Events (SSE) - Primary:**
- Backend: `ServerEventManager` singleton at `backend/api/managers/server_event_manager.py`
- Architecture: Per-topic async queues with 14-second keepalive (SSE comment pings)
- Endpoint: `endpoints.notification` router (`backend/api/endpoints/notification.py`)
- NATS integration: `ServerEventManager.enqueue(data)` called from NATS subscriber callback
- Frontend library: `vue-sse` ^2.5.2
- Topic subscription: Wildcard pattern `{prefix}:*` for fan-out within a scope

**WebSocket (Legacy):**
- `socket.io-client` ^4.7.5 present in dependencies
- No Socket.IO server detected in production; SSE has replaced it
- Deprecate for new code

## Monitoring & Observability

**Error Tracking:**
- None - no Sentry, DataDog, or similar integration

**Logging:**
- Docker JSON file driver: dev mode max 1k size, 3 files (rotate policy)
- Vector log aggregator: Optional, config at `deploy/config/vector.toml`
- Python `logging` module: Application log output
- Gunicorn: Access logs to stdout (`--access-logfile -` in production)
- NATS client: Logs at INFO level via Python logging
- Sparkplug bridge: Logs at INFO level, includes state transitions and heartbeats

**Metrics:**
- Prometheus config: `deploy/config/prometheus.yml` scraping ArangoDB metrics
- Traefik metrics: Dashboard at port 8080 (dev mode)
- No application-level APM (Datadog, New Relic, etc.)

## Reverse Proxy & Routing - Traefik v2.11

**Service Routing (Docker labels in stack.yaml):**
- `/api` → `api:8000` (FastAPI, prefix stripped)
- `/workflow` → `wf-server:4200` (Prefect UI)
- `/wf-api` → `wf-server:4200/workflow/api` (CORS bypass for CORS-sensitive clients)
- `/` → `app:80` (Main webapp, lowest priority=1)
- `/wh` → `warehouse:80` (Warehouse mobile app)
- `/_db` → `db:8529` (ArangoDB web UI)
- `/reports` → `reporting:8501` (Streamlit, iframe-only via CSP headers)
- `/notebooks` → `notebooks:8888` (Jupyter, optional)

**TLS Configuration (`deploy/compose/tls.yaml`):**
- Let's Encrypt automatic certificates (HTTP-01 challenge)
- Custom certificate support via file provider
- HTTP → HTTPS redirect
- Per-service TLS via router labels

**Middleware:**
- Strip prefix: `/api` → remove prefix before sending to backend
- CSP headers: `/reports` only allow iframing from self or specified host
- Authentication: Optional auth middleware per route

## CI/CD & Deployment

**Hosting Platforms:**
- Docker Swarm (production): `--providers.docker.swarmMode` in Traefik config
- Docker Compose (development): `deploy/compose/dev.yaml`

**CI/CD Pipeline (`.gitlab-ci.yml`):**
- Executor: Docker-in-Docker (`docker:24.0.5-dind`)
- Trigger: Version tags matching `v[0-9]+.[0-9]+.(a|b|rc)?[0-9]+`
- Stages: `.pre` (version extraction), `build` (Docker images), `package` (artifacts)
- Built services:
  - `api` - Backend REST API
  - `app` - Main webapp (Quasar SPA)
  - `warehouse` - Warehouse mobile app
  - `wf-sys-worker` - Prefect worker (optional)
  - `print-service` - Print service
- Tagging:
  - `{MAJOR.MINOR}-latest` (floating)
  - Exact version tag (e.g., `v1.2.3`)
- Registry: `registry.gitlab.com/progresslab/progress-platform/`
- Print service artifact: Also packaged as `.zip` to GitLab generic packages

## Environment Configuration

**Required Backend Env Vars:**
- `PROGRESS_ARANGO_URL` - ArangoDB endpoint (default `http://localhost:8529`)
- `PROGRESS_DB_NAME` - Database name (default `PROGRESS_TEST`)
- `PROGRESS_MEDIA_PATH` - Media storage location (default `/media`)
- `PROGRESS_API_ROOT_PATH` - API prefix (default `/api`)
- `PROGRESS_NATS_URL` - NATS broker URL (default `nats://broker:4222`)

**Required Docker Secrets (Production):**
- `progress_api_db_pwd` - ArangoDB user password
- `progress_admin_pwd` - Admin user initial password
- `progress_jwt_secret` - JWT signing secret
- `progress_db_root_pwd` - ArangoDB root password
- `progress_historian_db_pwd` - Historian database password (recommended for ADR-0005)

**Deployment Env Vars:**
- `VERSION` - Container image version tag
- `HOST` - Hostname for Traefik routing
- `PROTOCOL` - Scheme (`http` or `https`, default `https`)
- `PREFECT_API_URL` - Workflow server API endpoint
- `TLS_EMAIL` - Let's Encrypt registration email

**Sparkplug Bridge Env Vars:**
- `PROGRESS_MQTT_URL` - MQTT broker for device connections (default `tcp://broker:1883`)
- `PROGRESS_MQTT_CLIENT_ID` - Client identifier for MQTT connection
- `PROGRESS_BRIDGE_HEARTBEAT_INTERVAL_SEC` - Health signal interval (default 5s)
- `PROGRESS_BRIDGE_HOST_ID` - Bridge instance identifier
- `PROGRESS_BRIDGE_GAP_TOLERANCE`, `PROGRESS_BRIDGE_GAP_WINDOW_SEC` - Session stale detection

**Frontend Configuration:**
- Runtime config: `window.API_CONFIG` injected via `/config.js` (mounted from `deploy/config/appConfig.js`)
- Properties: `baseURL` (API host), `basePath` (API prefix, default `/api`)
- Fallback: Localhost detection in `webapps/main/src/boot/axios.js`

## Webhooks & Callbacks

**Incoming Webhooks:**
- None detected

**Outgoing Webhooks:**
- None detected (events flow via NATS pub/sub, not HTTP webhooks)

---

*Integration audit: 2026-05-08*
