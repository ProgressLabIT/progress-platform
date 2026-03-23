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
- **Real-time Communication** — Kafka for inter-service event streaming, WebSockets and SSE for live UI updates.

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
- PDF generation and download
- ZPL integration (industrial label printing language)

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

## What I Built & Learned

This platform was designed and developed largely by me, from database schema to deployment automation. Some highlights:

- **Implemented event sourcing from scratch** on top of ArangoDB — no ORM, no framework magic. Every domain event is an explicit, auditable state transition with transactional `apply()` semantics. Events can generate child events for modularity, but all are handled within the same database transaction for data consistency.
- **Designed a multi-app frontend architecture** with a shared design system across a desktop SPA and a mobile warehouse app (Capacitor/Android with barcode scanning), both built with Vue 3 and Quasar.
- **Built real-time collaboration features** using Kafka, WebSockets, and SSE to keep operators' screens in sync on the factory floor.
- **Security-conscious design** — JWT authentication with server-side token records for revocation, single active session enforcement, bcrypt password hashing, ACL-based permission scopes, and Docker Swarm secrets for credential management. TLS termination via Traefik with support for both Let's Encrypt and custom certificates for private networks.
- **Infrastructure as Code** — Ansible playbooks automate full single-node provisioning: system packages, Docker Swarm init, network/secret creation, compose deployment, and database initialization. GitLab CI handles tag-triggered image builds.
- **Maintained living documentation** (`km/`) — architecture decisions, domain logic, and test case specifications co-evolve with the codebase, following a "read first, write back" protocol.

---

## What's missing / Next steps
- Robust testing framework
- User oriented/UI documentation 
- Cloud readiness

## License

This project is proprietary. Source code is shared for portfolio purposes only.
