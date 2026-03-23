# External Integrations

**Analysis Date:** 2026-03-12

## APIs & External Services

**Prefect Workflow API:**
- Service: Prefect 3.x Workflow Orchestration
- Purpose: Schedule, deploy, and monitor automated workflows
- SDK/Client: `prefect==3.*` in `backend/workflow/requirements.txt`
- Endpoint: Configured via environment variable `PREFECT_API_URL`
- Frontend integration: `webapps/main/src/composables/usePrefectAPI.js` for monitoring deployments and flow runs
- Authentication: Bearer token via Prefect server configuration

**Backend API (Internal):**
- Service: FastAPI REST API at `backend/api/main.py`
- Purpose: Central service for all business logic, data operations, and integrations
- Endpoints: Multiple routers for inventory, production, form, quality, traceability, etc.
- Access: Axios HTTP client from frontends at `webapps/main/src/boot/axios.js`
- Authentication: JWT Bearer tokens

## Data Storage

**Databases:**
- **ArangoDB 3.11** - Multi-model database (document, graph, search)
  - Connection: `python-arango==8.*` client at `backend/api/utils/db.py`
  - Configuration: `PROGRESS_ARANGO_URL` environment variable (default: `http://localhost:8529`)
  - Database name: `PROGRESS_TEST` (dev/test), `PROGRESS_PROD` (production) - configured via `PROGRESS_DB_NAME`
  - Authentication: User/password via `progress_api_db_username` and `progress_api_db_pwd` (Docker secrets)
  - Port: 8529 (internal), exposed for direct access during development
  - Web UI: Accessible at `/_db` endpoint through Traefik proxy
  - Metrics: Prometheus metrics exposed at `/_db/{database}/_admin/metrics/v2`

**Workflow State Database:**
- **PostgreSQL 15.2-alpine** - Workflow engine backend
  - Service name: `workflow-db` in `deploy/compose/workflow.yaml`
  - Connection: `postgresql+asyncpg://postgres:postgres@workflow-db:5432/prefect`
  - Credentials: Default postgres/postgres (deployment-specific)
  - Purpose: Stores Prefect flow runs, deployments, and execution state

**File Storage:**
- **Local filesystem** - Bind-mounted volumes
  - Media path: `/media` volume mounted at `PROGRESS_MEDIA_PATH` environment variable
  - Backup path: `/db_backup` volume for ArangoDB backups
  - Log path: `/logs` volume for application logs

**Caching:**
- No explicit caching layer configured (local memory state in Kafka consumer managers)

## Authentication & Identity

**Auth Provider:**
- **Custom JWT-based** - Built-in implementation
  - Implementation: `backend/api/utils/auth.py` with FastAPI OAuth2PasswordBearer
  - Token generation: PyJWT with `PyJWT==2.0.*`
  - Password hashing: `bcrypt==4.3.*` via passlib
  - Token secret: `progress_jwt_secret` stored as Docker secret
  - Bearer scheme: HTTP Authorization header with `Bearer {token}` format
  - Scopes: Defined at `backend/api/models/auth.py`
  - Token validation: Custom `verify_token()` dependency at `backend/api/utils/auth.py`
  - User database: Stored in ArangoDB, managed at `backend/api/models/auth.py`

**Frontend Integration:**
- JWT tokens stored in browser state (Vuex store)
- Axios interceptor adds token to all API requests at `webapps/main/src/boot/axios.js`
- 401 responses trigger logout (except whoami/session endpoints)

## Message Queue & Event System

**Event Broker:**
- **Apache Kafka (KRaft mode)** - Distributed event streaming
  - Image: `apache/kafka:latest` at `deploy/compose/base.yaml`
  - Port: 9092 (host), 19092 (internal)
  - JMX Port: 9101 for monitoring
  - Configuration: Single-node KRaft cluster (node ID 1)
  - Topics: Auto-created including `notifications` topic at startup in `backend/api/main.py`
  - Consumer group: `backend` with ID `backend-service-consumer`
  - Producer client: ID `backend-service-producer`

**Backend Integration:**
- Producer: `backend/api/utils/kafka/kafka_producer.py` - Singleton instance initialized at startup
- Consumer: `backend/api/utils/kafka/kafka_consumer.py` with consumer manager at `backend/api/managers/kafka_consumer_manager.py`
- Admin: `backend/api/utils/kafka/kafka_admin.py` - Topic management via REST API at `backend/api/endpoints/admin.py`
- Endpoints: `PUT/DELETE /kafka/topic/{topic}`, `GET /kafka/topics` for Kafka administration

**Real-time Features:**
- **Kafka Consumers:**
  - Notifications consumer: `backend/api/utils/notification_kafka_consumer.py` - Subscribes to notifications topic
  - Chat consumer: `backend/api/utils/chat_kafka_consumer.py` - Subscribes to chat messages
- **WebSocket Manager:** `backend/api/managers/websocket_manager.py` - Maintains active WebSocket connections
- **Notification Middleware:** `backend/api/middlewares/notification_middleware.py` - Processes and broadcasts messages
- **Events:** Server-sent messages queued via `ServerEventManager` at `backend/api/managers/server_event_manager.py`

**Frontend Real-time:**
- Socket.IO client at `socket.io-client@4.7.5` in both web and warehouse apps
- Server-Sent Events support via `vue-sse@2.5.2`
- Notification display via Quasar Notify component

## Monitoring & Observability

**Error Tracking:**
- Not configured - no Sentry/similar service integration detected

**Logs:**
- **Docker JSON File Driver:** Configured at `deploy/compose/dev.yaml` for backend API
  - Max file size: 1k, max files: 3 (limited log retention)
- **Vector Log Aggregator:** Docker log collector at `deploy/config/vector.toml`
  - Source: Docker Swarm logs
  - Sink: File output with date-based rotation (`/out/vector-%Y-%m-%d.log`)
  - Alternative: Grafana Cloud Loki integration available (commented out)
- **Application Logging:** Standard Python logging to stdout/stderr, captured by Docker

**Metrics:**
- **Prometheus:** Metrics scraping configuration at `deploy/config/prometheus.yml`
  - ArangoDB metrics: Scraped from `/_db/PROGRESS_PROD/_admin/metrics/v2` every 5 seconds
  - Query port: 8529
  - Interval: 15s default, 5s for database

**Dashboards:**
- Grafana dashboards available at `deploy/dashboards/` directory
- Grafana Cloud integration configured (commented out in vector.toml)

## CI/CD & Deployment

**Hosting:**
- **Docker Compose** - Local development and single-node production
- **Kubernetes-ready** - Traefik ingress controller for routing
- **GitLab** - VCS and CI/CD platform

**CI Pipeline:**
- **GitLab CI** at `.gitlab-ci.yml`
- **Docker-in-Docker:** Build environment uses `docker:24.0.5-dind`
- **Build Stages:** Separate jobs for webapp, warehouse, API, and workflow services
- **Registry:** `registry.gitlab.com/progresslab/progress-platform/`
- **Versioning:** Semantic versioning from git tags (e.g., `v0.9.8` -> `0.9-latest` and `0.9.8` tags)
- **Artifacts:** Docker images pushed on tag matching `v[0-9]+.[0-9]+.(a|b|rc)?[0-9]+` pattern

**Deployment:**
- **Traefik v2.11** - Reverse proxy and load balancer
  - Routing rules via Docker labels
  - SSL/TLS termination at port 443
  - HTTP at port 80
  - Web UI at port 8080 (development only)
- **Compose files:**
  - `deploy/compose/base.yaml` - Core services (Traefik, API, Database, Kafka)
  - `deploy/compose/dev.yaml` - Development overrides
  - `deploy/compose/dev.debug.yaml` - Debug mode with remote debugging
  - `deploy/compose/stack.yaml` - Production stack
  - `deploy/compose/workflow.yaml` - Workflow services
  - `deploy/compose/warehouse.yaml` - Warehouse app
  - `deploy/compose/reporting.yaml` - Reporting services
  - `deploy/compose/notebooks.yaml` - Jupyter notebook environment

## Environment Configuration

**Required environment variables:**
- `PROGRESS_ARANGO_URL` - ArangoDB connection string
- `PROGRESS_MEDIA_PATH` - Path to media files volume
- `PROGRESS_API_ROOT_PATH` - API prefix path (default: `/api`)
- `PROGRESS_DB_NAME` - ArangoDB database name
- `PROGRESS_WEBAPP_URL` - Frontend URL for CORS
- `PROGRESS_API_DB_USERNAME` - Database user
- `PROGRESS_API_DB_PWD` - Database password (Docker secret)
- `PROGRESS_ADMIN_PWD` - Admin user password (Docker secret)
- `PROGRESS_JWT_SECRET` - JWT signing secret (Docker secret)
- `PREFECT_API_URL` - Prefect server endpoint
- `KAFKA_BOOTSTRAP_SERVER` - Kafka broker connection
- `KAFKA_GROUP_ID` - Consumer group (default: `backend`)

**Optional configurations:**
- `PROGRESS_CORS_ALLOWED_ORIGINS` - CORS origin whitelist
- `PROGRESS_KAFKA_SESSION_TO_MS` - Consumer session timeout
- `PREFECT_UI_SERVE_BASE` - Workflow UI base path
- Traefik environment: `SUBDOMAIN`, `DOMAIN` for URL construction

**Secrets location:**
- Docker secrets directory: `/run/secrets/`
- Environment file support: `.env` file parsing via pydantic-settings
- Configuration class: `backend/api/utils/config.py` with BaseSettings

## Webhooks & Callbacks

**Incoming:**
- Admin endpoints: `backend/api/endpoints/admin.py` - Kafka topic management
- Notification webhooks: Implicit via Kafka topic subscriptions

**Outgoing:**
- Prefect API calls: Frontend composable triggers workflow runs via Prefect API
- WebSocket broadcasts: Backend sends real-time updates to connected clients
- Kafka producer: Backend publishes events to Kafka topics for consumer subscriptions

**Event Flow:**
1. Backend processes request or event
2. If notification needed, produces to Kafka `notifications` topic
3. NotificationsKafkaConsumer receives message
4. WebsocketManager broadcasts to connected clients via WebSocket
5. Frontend receives update and refreshes UI state

## File Management

**File Upload/Download:**
- Media endpoint: `backend/api/endpoints/media.py`
- Storage: Bind-mounted `/media` volume
- MIME type support: Video, image, document formats
- Attachment management: `backend/api/endpoints/file.py` for file operations

**PDF Generation:**
- Server-side: WeasyPrint/ReportLab in `backend/api/utils/dhr.py`
- Client-side: PDFme templates in both web applications
- Stream response: PDF content streamed to client via HTTP

---

*Integration audit: 2026-03-12*
