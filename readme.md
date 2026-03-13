# Progress Platform

An open-source Manufacturing Operating System (MOS/MES) built for small and mid-size production companies. Tracks work orders, production jobs, inventory movements, serial numbers, and warehouse operations — all wired together through an immutable event log.

> **Status:** Built and deployed in real manufacturing environments. Actively developed but not yet production-polished (sparse test coverage, some debug artifacts). Contributions welcome.

---

## What It Does

Progress Platform gives factory operators and managers a single interface to run production:

- **Work orders & job queues** — Create work orders from your product catalog, assign them to production queues, track jobs through each operation step
- **Operator panel** — Operators claim jobs, log start/stop times, declare output quantities, and handle batch/serial production
- **Serial number & traceability** — Full genealogy tracking from raw material to finished product, including rework and scrap
- **Inventory management** — Warehouse positions, stock movements, mission-based picking, inventory counting with import/export
- **Print templates** — PDF label generation via a pdfme v5 designer embedded in the app; direct ZPL printing to LAN printers (in progress)
- **Collaboration** — Issues, tasks, and a real-time chat linked to production entities
- **Workflow automation** — Prefect-based scheduled flows for ERP integrations and background jobs
- **Warehouse mobile app** — A Capacitor-wrapped Quasar app for tablet/mobile warehouse operators, with barcode scanning

---

## Architecture

The most deliberate design choice in this codebase is **Event Sourcing with Domain-Driven Design**. Every state mutation goes through a typed `Event` object — never a direct document update. This gives you a complete audit trail, replay capability, and a clean separation between "what happened" and "what it looks like now."

```
HTTP Request
    │
    ▼
FastAPI Endpoint          ← validates input, checks preconditions
    │
    ▼
Event(info=...)           ← immutable business operation
    │
    ├── pre_processing()  ← pre-checks inside transaction scope
    ├── apply()           ← all DB mutations, transactional
    ├── store_event()     ← write to Event collection
    └── post_processing() ← Kafka publish, side effects (non-blocking)
    │
    ▼
NotificationMiddleware    ← WebSocket broadcast to connected clients
```

Key architectural choices:

| Decision | Rationale |
|---|---|
| **ArangoDB** (graph + document) | Domain entities have natural graph relationships (product → phases → operations, serial → movements → positions). Graph traversals beat JOIN chains for genealogy queries. |
| **Kafka** for domain events | Decouples the core API from integrations (ERP sync, notifications). Kafka consumers subscribe per topic; failures don't roll back the event. |
| **Prefect** for automation | Scheduled flows (ERP imports, inventory syncs) need retries, observability, and deployment management — not just cron. |
| **Dual webapp** (desktop + mobile) | Operators on the floor use tablets with barcode scanners. The warehouse app is a separate Quasar + Capacitor build sharing the same API. |
| **pdfme v5** for labels | Client-side PDF template designer with a pluggable schema system. Avoids server-side PDF generation for label use cases. |

---

## Tech Stack

**Backend**
- Python 3.11 · FastAPI · Pydantic v2
- ArangoDB 3.11 (via `python-arango`)
- Apache Kafka (KRaft mode)
- Prefect 3.x (workflow engine)
- WeasyPrint / ReportLab (server-side PDF)
- JWT auth (PyJWT + bcrypt)

**Frontend**
- Vue 3 · Quasar Framework 2 · Pinia · Vue Router
- pdfme v5 (PDF template designer + generator)
- Socket.IO (real-time updates via WebSocket)
- ZXing (barcode/QR scanning in warehouse app)
- Capacitor 6 (native mobile wrapper)

**Infrastructure**
- Docker Swarm (production) · Docker Compose (development)
- Traefik v2 (reverse proxy, TLS)
- Ansible (automated server provisioning)
- Prometheus + Grafana (metrics)
- Vector (log aggregation)

---

## Project Structure

```
progress-platform/
├── backend/
│   ├── api/                  # Main FastAPI application
│   │   ├── endpoints/        # Route handlers (one file per domain)
│   │   ├── events/           # 50+ typed event classes (core business logic)
│   │   ├── managers/         # WebSocket, Kafka, notifications
│   │   ├── models/           # Pydantic schemas
│   │   └── utils/            # DB, auth, config, Kafka clients
│   ├── workflow/             # Prefect flows (scheduled automation)
│   ├── reports/              # Streamlit reporting service
│   └── scripts/              # DB migrations, dev utilities
├── webapps/
│   ├── main/                 # Desktop MES app (Vue3 + Quasar)
│   └── warehouse/            # Mobile warehouse app (Vue3 + Quasar + Capacitor)
├── deploy/
│   ├── compose/              # Docker Compose files (base, dev, prod, services)
│   ├── config/               # Per-service config (Traefik, Kafka, ArangoDB)
│   └── scripts/              # DB initialization, provisioning scripts
├── testing/                  # E2E (Cypress), integration (Robot Framework), BDD
├── km/                       # Knowledge base: architecture docs, domain rules
└── cli/                      # CLI tools for local development
```

---

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ and Yarn
- Python 3.11+

### Local Development

**1. Start infrastructure services**

```bash
cd deploy
docker compose -f compose/base.yaml -f compose/dev.yaml up -d
```

This starts ArangoDB, Kafka, and Traefik.

**2. Initialize the database**

```bash
# Create collections, indexes, and a default admin user (cadmin / resetme)
python deploy/scripts/db_init.py
```

**3. Start the API**

```bash
cd backend/api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**4. Start the web app**

```bash
cd webapps/main
yarn install
yarn dev
```

The app will be available at `http://localhost:9000`. Log in with `cadmin` / `resetme` and change the password on first login.

### Environment Variables

The API reads configuration from `PROGRESS_*` environment variables or a `.env` file:

```bash
# backend/api/.env (example)
PROGRESS_ARANGO_URL=http://localhost:8529
PROGRESS_DB_NAME=PROGRESS_DEV
PROGRESS_JWT_SECRET=your-secret-here   # required — generate with: openssl rand -hex 32
PROGRESS_API_DB_USERNAME=root
PROGRESS_API_DB_PWD=
```

### Production Deployment (Docker Swarm)

The `deploy/` folder contains a full single-node Ansible playbook and Docker Swarm stack. Secrets are managed via `docker secret create` — no credentials in config files.

```bash
# Provision a fresh Ubuntu server and deploy the full stack
ansible-playbook deploy/single_node_setup.yaml -i your-server-ip,
```

---

## Domain Model

The core entities and their relationships:

```
Product ──has──> Phase ──has──> Operation
    │
WorkOrder ──produces──> Job ──runs──> Batch ──tracks──> Serial
    │
    └── assigned to ──> Queue (per site / department)

Serial ──is_in_position──> Position (inventory location)
Serial ──moved_by──> Movement ──part_of──> MovementList (warehouse mission)
```

ArangoDB's graph model maps naturally to this — genealogy queries ("show me everything that went into this serial number") are single graph traversals.

---

## Event System

Every business operation is a named event. To understand what the system can do, read the `backend/api/events/` directory:

```
events/
├── production/
│   ├── job_started.py
│   ├── job_paused.py
│   ├── job_completed.py
│   ├── batch_declared.py
│   └── ...
├── inventory/
│   ├── movement_planned.py
│   ├── movement_completed.py
│   ├── count_session_applied.py
│   └── ...
└── serial/
    ├── serial_created.py
    ├── serial_released.py
    └── ...
```

Each event class defines:
- `event_type` — unique identifier (enum)
- `tx_collections` — ArangoDB collections included in the transaction
- `apply()` — all DB mutations (transactional, idempotent)
- `post_processing()` — optional Kafka publish or side effects

---

## Honest Assessment

This codebase was built under real startup constraints. Things to be aware of:

- **Test coverage is sparse.** There are Cypress E2E tests and a Robot Framework test suite, but unit test coverage is low. The event system is well-suited for unit testing; it just hasn't been prioritized.
- **Some debug `print()` statements** remain in the API layer. A structured logging pass is overdue.
- **Mixed patterns in the frontend.** The main webapp has both Vuex (legacy) and Pinia stores, and both Options API and Composition API components from different development phases.
- **No CI on GitHub yet.** The original CI/CD ran on GitLab. GitHub Actions equivalents need to be set up.

If you're evaluating this as a portfolio project: the architecture decisions — event sourcing, graph database, Kafka, dual webapp — were made deliberately and under production constraints, not as a demo.

---

## Contributing

Issues and PRs are welcome. If you're interested in contributing, check `km/` for architecture context before diving into the code — it explains the "why" behind most non-obvious decisions.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
