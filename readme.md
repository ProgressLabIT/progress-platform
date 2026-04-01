# Progress Platform

A full-stack **Manufacturing Operations Management** system (MOM) built to manage product data, production planning and execution, inventory, traceability, and quality for discrete manufacturing environments. Designed and developed as a single-tenant, event-sourced platform deployed on-premise via Docker.

> **Note:** This is a production system actively used by manufacturing companies in high compliance sectors such as electronics, medical devices, defence and aerospace. Some configuration files and credentials have been excluded from this repository.

---

## Architecture

```
                  ┌──────────────┐     ┌───────────────┐
                  │  Main Webapp │     │ Warehouse App │
                  │  Vue 3 / SPA │     │ Vue 3 / Mobile│
                  └──────┬───────┘     └──────┬────────┘
                         │                    │
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
            │  ArangoDB   │ │    Kafka    │ │  Prefect │
            │  Multi-Model│ │  Streaming  │ │ Workflows│
            └─────────────┘ └─────────────┘ └──────────┘
```

### Key Design Decisions

- **Event Sourcing** — Factory activities are modeled through immutable events, from which state is derived, enabling full auditability and traceability (critical for manufacturing compliance). Every mutation is modeled as an `Event` with a transactional `apply()` method.
- **Multi-Model Database** — ArangoDB provides document storage and graph traversal in a single engine, used for everything from inventory hierarchies to production genealogy.
- **Async Workflows** — Long-running operations (e.g. bulk inventory adjustments across 500+ records) are offloaded to Prefect, keeping the API responsive. The workflow engine is also used to add custom plugins to integrate the platform with ERPs and other business systems.
- **Real-time Communication** — NATS for inter-service event streaming, SSE for live UI updates.

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Backend API** | Python 3.11, FastAPI, Pydantic v2, Gunicorn/Uvicorn |
| **Database** | ArangoDB 3.11 (documents + graphs) |
| **Messaging** | Apache Kafka (KRaft mode) |
| **Workflows** | Prefect 3 |
| **Frontend** | Vue 3, Quasar 2, Pinia, Vite, vue-i18n |
| **Infrastructure** | Docker, Docker Swarm, Traefik v2 |
| **CI/CD** | GitLab CI (tag-triggered builds) |
| **Deployment** | Ansible (single-node provisioning) |
| **Other** | WeasyPrint/ReportLab (PDF), openpyxl (Excel), httpx, CodeMirror 6 |

---

## Domain Features

### Production
- Work order lifecycle management with status-driven queue ordering
- Operator job assignment and phase tracking
- Serial number management with BOM-linked genealogy
- Batch and step execution tracking
- Interactive work instructions backed by rich media (images, video, documents)

### Inventory
- Warehouse position hierarchy with product-based and position-based counting
- Count session lifecycle (planned → started → completed → async application)
- Bulk import/export (XLSX/CSV) with conflict detection and resolution
- Async count application via Prefect for large-scale adjustments

### Traceability, Quality and Collaboration
- Component linking and serial genealogy
- Production event audit trail (powered by event sourcing)
- No code development of data gathering forms
- Task and Issue tracking with custom types, assignments, entity linking
- Dedicated messaging threads for work orders, issues, serials, tasks

### Printing
- Drag and Drop Report/Label template design
- Auto filling of forms from UI context
- PDF and ZPL (industrial label printing language) generation and direct print

---

## Project Structure

```
├── backend/
│   ├── api/            # FastAPI application (endpoints, models, events, managers)
│   ├── workflow/        # Prefect flows (inventory, production, cleanup)
│   ├── commons/         # Shared logic across backend services
│   └── reports/         # Reporting service
├── webapps/
│   ├── main/            # Primary SPA (Vue 3 + Quasar + Vite)
│   └── warehouse/       # Mobile-first warehouse app (Vue 3 + Quasar + Vite)
├── deploy/
│   ├── compose/         # Service configuration / Docker Compose files (dev, prod, TLS config, etc.)
│   └── config/          # Environment configs, Traefik, Prometheus
├── db/                  # Migrations, queries, backup scripts
├── testing/             # Robot Framework suites
├── km/                  # Living documentation (architecture, domain logic)
└── cli/                 # CLI tools (data generation, utilities)
```

---

## Setup

> *Progress CLI coming soon! In the meantime, you can follow the procedures below.*


### Prerequisites

- **Docker** with Compose v2 (local stack uses Docker Compose; production uses Docker Swarm).
- **Node.js** — use the version in [`.nvmrc`](.nvmrc) for the Quasar webapps (`webapps/main`, `webapps/warehouse`).
- **Python 3.11+** — only if you run Prefect or workflow tooling on the host (see below).

---

### Run locally (Docker Compose)

The local API, Traefik, ArangoDB, and NATS are defined under [`deploy/compose/`](deploy/compose/): merge [`base.yaml`](deploy/compose/base.yaml) with [`dev.yaml`](deploy/compose/dev.yaml). The dev overlay mounts the API source for hot reload and enables the debugpy port.

**1. One-time: create external volumes** (required by `base.yaml` / `dev.yaml`):

```bash
docker volume create media
docker volume create db_data
docker volume create db_backup
```

**2. Hostname**

Traefik router rules default to the hostname **`progress.localhost`**. Either map that name or override the variable:

- Add to `/etc/hosts`: `127.0.0.1 progress.localhost`, or  
- Set `PROGRESS_ADDRESS` when starting Compose (e.g. `export PROGRESS_ADDRESS=localhost` and ensure labels match your setup).

**3. Start the stack**

From the repository root:

```bash
cd deploy/compose
docker compose -f base.yaml -f dev.yaml up -d --build
```

**4. URLs and ports (typical defaults)**

| Service | Access |
|--------|--------|
| Traefik dashboard | [http://localhost:8080](http://localhost:8080) |
| API (direct, bypass Traefik) | [http://localhost:8000](http://localhost:8000) (also debugpy on `5678` if you attach a debugger) |
| API via Traefik | `http://<PROGRESS_ADDRESS>/api/...` (default host: `progress.localhost`) |
| ArangoDB web UI via Traefik | `http://<PROGRESS_ADDRESS>/_db/` |
| ArangoDB (direct) | [http://localhost:8529](http://localhost:8529) (dev uses `ARANGO_NO_AUTH=1`) |
| NATS client / monitoring | `localhost:4222` / `localhost:8222` |

**5. API environment**

The API loads `PROGRESS_*` settings from environment and optional `backend/api/.env` (see [`backend/api/utils/config.py`](backend/api/utils/config.py)). Compose already sets `PROGRESS_ARANGO_URL`, `PROGRESS_MEDIA_PATH`, and `PROGRESS_WEBAPP_URL`. For **Prefect** triggered from the API container, set `PREFECT_API_URL` (defaults in dev to `http://host.docker.internal:4200/api`). Full host-side steps: [`deploy/compose/prefect-local-dev.md`](deploy/compose/prefect-local-dev.md). On Linux you may need `extra_hosts: host.docker.internal:host-gateway` on the `api` service.

**6. Webapps (main / warehouse)**

The compose dev stack does not build the SPAs. Run them on the host:

```bash
cd webapps/main   # or webapps/warehouse
corepack enable   # if you use Yarn via Corepack
yarn install
yarn dev
```

Point the app at your API origin (Quasar dev server and `PROGRESS_WEBAPP_URL` / CORS as needed). The dev compose file sets `PROGRESS_WEBAPP_URL=http://localhost:9000` for the API process.

---

### Run in production (Docker Swarm)

Production is deployed as a **Docker Swarm stack** on a single node using **Ansible**: [`deploy/single_node_setup.yaml`](deploy/single_node_setup.yaml). Images are pulled from `registry.gitlab.com/progresslab/progress-platform` (tag from `VERSION`).

**1. Configure deployment variables**

Edit [`deploy/config/progress.env.yaml`](deploy/config/progress.env.yaml) (or your copy on the deploy host):

| Variable | Purpose |
|----------|---------|
| `DOMAIN` | Base domain (e.g. `progresslab.it`) |
| `SUBDOMAIN` | Tenant host segment (`<SUBDOMAIN>.<DOMAIN>`) |
| `VERSION` | Image tag (e.g. GitLab registry tag from CI) |
| `ENABLE_TLS` | `true` to include Let’s Encrypt (`tls.yaml`); `false` for HTTP-only |
| `TLS_EMAIL` | ACME registration email when TLS is enabled |

**2. Registry authentication**

Provide GitLab registry credentials in [`deploy/registry_creds`](deploy/registry_creds) as expected by the playbook (`vars_files`).

**3. What the playbook does (high level)**

- Installs Docker, initializes Swarm, creates external volumes and **Docker secrets** (`progress_api_db_pwd`, `progress_admin_pwd`, `progress_jwt_secret`, `progress_db_root_pwd`).
- Copies [`deploy/compose/`](deploy/compose/) and config templates to `/opt/progress/config/` on the server.
- Renders `/opt/progress/config/progress.env` from `progress.env.yaml` via [`deploy/config/env_template.j2`](deploy/config/env_template.j2).
- Runs `docker stack deploy` from `/opt/progress/config` with compose files:
  - **With TLS:** `base.yaml`, `stack.yaml`, `tls.yaml`, `warehouse.yaml`, `workflow.yaml`, `integration.yaml`, `reporting.yaml`, `notebooks.yaml`
  - **Without TLS:** same list except `tls.yaml`
- Mounts API env file at **`/opt/progress/config/api.env`** into the API container (see [`deploy/config/api.env`](deploy/config/api.env) for optional overrides such as CORS).
- Runs database initialization via a one-off `init-db` service ([`deploy/scripts/db_init.py`](deploy/scripts/db_init.py)).

**4. Run Ansible**

From the machine that orchestrates the install (with Ansible and SSH access to the target):

```bash
cd deploy
ansible-playbook -i <inventory> single_node_setup.yaml
```

Air-gapped installs can use [`deploy/single_node_setup_local.yaml`](deploy/single_node_setup_local.yaml) with a local image tarball (see that file for scope and limitations).

**5. Optional stack pieces**

Additional compose files in the same directory cover **print** ([`print.yaml`](deploy/compose/print.yaml)), **TLS** overrides ([`tls.yaml`](deploy/compose/tls.yaml)), and other services—wire them into your deploy process if you use those features.

---

### CI-built images

GitLab CI builds and pushes images on tag pipelines; set `VERSION` in `progress.env.yaml` to the tag you deploy. The main application image is `app`; the API image is `api` (see [`deploy/compose/stack.yaml`](deploy/compose/stack.yaml)).


