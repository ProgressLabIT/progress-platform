# Architecture

A high-level overview of the Progress Platform architecture for visitors browsing the repository. For deeper layer/module reference, see the docs site at <https://progresslabit.github.io/progress-platform/>.

## System diagram

```
                  ┌──────────────┐     ┌───────────────┐
                  │  Main Webapp │     │ Warehouse App │
                  │  Vue 3 / SPA │     │ Vue 3 / Mobile│
                  └──────┬───────┘     └──────┬────────┘
                         │  SSE (live updates) │
                         └────────┬───────────┘
                                  │
                         ┌────────▼────────┐
                         │     Traefik     │
                         │  Reverse Proxy  │
                         └────────┬────────┘
                                  │
                         ┌────────▼────────┐
                         │  FastAPI (API)  │
                         │  Event-Sourced  │
                         └───┬─────┬────┬──┘
                             │     │    │
                   ┌─────────┘     │    └─────────┐
                   │               │              │
            ┌──────▼──────┐ ┌──────▼──────┐ ┌────▼─────┐
            │  ArangoDB   │ │    NATS     │ │  Prefect │
            │  Multi-Model│ │  JetStream  │ │ Workflows│
            └─────────────┘ └─────────────┘ └──────────┘
```

## Key design decisions

- **Event-sourced backend** — Factory activities are modeled as immutable `Event` objects with a transactional `apply()` method. State is derived from the event log, enabling full auditability and traceability (critical for manufacturing compliance). Every mutation is captured; nothing is overwritten in place.
- **Multi-model database** — ArangoDB provides document storage and graph traversal in a single engine, used for everything from inventory hierarchies to production genealogy and serial-number BOM linkage.
- **Async workflows** — Long-running operations (e.g. bulk inventory adjustments across 500+ records) are offloaded to Prefect 3, keeping the API responsive. The workflow engine also hosts custom plugins that integrate the platform with ERPs and other business systems.
- **Real-time messaging** — NATS with JetStream handles inter-service pub/sub messaging; Server-Sent Events (SSE) push live updates to the browser. (Some legacy references to Kafka exist in older documentation — the platform is NATS-only.)
- **Single-tenant, on-premise** — Every customer runs their own Compose stack. No multi-tenant SaaS layer; no shared database. Simplifies the data model and the compliance story.

## Layered backend

| Layer | Location | Responsibility |
|-------|----------|----------------|
| **HTTP / middleware** | `backend/api/main.py` + `backend/api/middlewares/` | FastAPI app, CORS / GZip / notification middleware, startup/shutdown hooks |
| **Endpoints** | `backend/api/endpoints/*.py` (~20 files) | Route handlers; validate input, instantiate domain events, return responses |
| **Events (business logic)** | `backend/api/events/` | `BaseEvent` abstract class + 50+ concrete events organized by domain (production, inventory, counting, etc.). Each event runs `pre_processing → apply → store_event` inside a single ArangoDB transaction. |
| **Managers (side effects)** | `backend/api/managers/*.py` | Singletons for cross-cutting concerns: `NotificationManager`, `KafkaConsumerManager`, websocket fan-out, etc. (Naming is historical — managers wire NATS, not Kafka.) |
| **Models (validation)** | `backend/api/models/*.py` | Pydantic v2 models for request/response validation and ArangoDB document structure |
| **Utilities** | `backend/api/utils/` | Auth, queries, config, helpers |

## Data flow (typical request)

1. **HTTP request** hits Traefik → FastAPI middleware chain → endpoint handler.
2. Endpoint **validates** input via Pydantic, **fetches** current state via `utils.*.Queries.*`, checks **preconditions** (e.g. "job must be RUNNING").
3. Endpoint **instantiates an Event** and calls `Event.save()`.
4. `Event.save()` opens an ArangoDB **transaction**, runs `pre_processing` → `apply` (state mutations) → `store_event` (event log append), then **commits** atomically. Any exception aborts the transaction.
5. Post-commit, `post_processing` publishes to **NATS** for downstream subscribers (notifications, fan-out children, integrations); failures here do not fail the original event.
6. Browser clients receive the change via **SSE** broadcast from `NotificationManager`.

## Frontends

- **Main webapp** (`webapps/main/`) — Vue 3 + Quasar 2 desktop SPA. Production / inventory / counting / user-hub / printing.
- **Warehouse app** (`webapps/warehouse/`) — Vue 3 + Quasar 2 + Capacitor mobile app. Scanning, missions, movement-lists, counting sessions.
- Both use Pinia (newer) + a legacy Vuex store (being phased out). Real-time updates via SSE; some integrations use `socket.io-client` / `vue-sse`.

## Repository layout

```
├── backend/
│   ├── api/            FastAPI application (endpoints, models, events, managers)
│   ├── workflow/       Prefect flows (inventory, production, cleanup)
│   ├── commons/        Shared logic across backend services
│   └── reports/        Reporting service
├── webapps/
│   ├── main/           Primary SPA (Vue 3 + Quasar + Vite)
│   └── warehouse/      Mobile-first warehouse app (Vue 3 + Quasar + Vite + Capacitor)
├── deploy/
│   ├── compose/        Docker Compose files (dev / prod / TLS / etc.)
│   └── config/         Environment configs, Traefik, Prometheus
├── db/                 Migrations, queries, backup scripts
├── testing/            Test suites (pytest + Robot Framework)
├── km/                 Living documentation (architecture, domain logic)
├── cli/                CLI tools (data generation, utilities)
└── docs/               Public documentation site (VitePress) — published to GitHub Pages
```

## Tech stack

| Layer | Technologies |
|-------|--------------|
| Backend API | Python 3.11, FastAPI, Pydantic v2, Gunicorn/Uvicorn |
| Database | ArangoDB 3.11 (documents + graphs) |
| Messaging | NATS with JetStream |
| Workflows | Prefect 3 |
| Frontend | Vue 3, Quasar 2, Pinia, Vite, vue-i18n |
| Infrastructure | Docker, Docker Swarm, Traefik v2 |
| CI/CD | GitLab CI (tag-triggered builds) |
| Deployment | Ansible (single-node provisioning) |
| Other | WeasyPrint / ReportLab (PDF), openpyxl (Excel), httpx, CodeMirror 6 |
