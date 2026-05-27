# Progress Platform Knowledge Base

Welcome to the **Progress Platform Knowledge Base**. This documentation serves as the single source of truth for the system's architecture, business domains, and development guides. It is designed for both **Human Engineers** and **AI Agents**.

> **Note to AI Agents:** When answering user queries, always search this directory first to understand the architectural context and business rules before suggesting code changes.

## 📚 Table of Contents

### 🏗️ Architecture
High-level technical decisions and system design.
- [Overview](architecture/overview.md) - System context, stack, and deployment topology.
- [Event Sourcing](architecture/event-sourcing.md) - **CRITICAL**: How business logic is implemented via immutable events.
- [Database Schema](architecture/database-schema.md) - ArangoDB graph model explanation.
- [Mobile & Offline](architecture/mobile-offline.md) - Warehouse app offline capability strategies.

### 🏭 Business Domains
Detailed documentation of the application's core capabilities, mapping to `backend/api/endpoints/`.

#### Production (`/domains/production`)
- [Queue Management](domains/production/queue-management.md)
- [Serial Management](domains/production/serial-management.md)

#### Inventory (`/domains/inventory`)
- [Counting](domains/inventory/counting/async-count-session-application.md)
- [Stock Movements](domains/inventory/stock-movements.md)
- [Warehouse Structure](domains/inventory/warehouse-structure.md)

#### Traceability (`/domains/traceability`)
- Genealogy, Batch Tracking, and Compliance.

#### Quality (`/domains/quality`)
- Issue Tracking and Quality Checks.

#### Master Data (`/domains/master-data`)
- Products, BOMs, and Process Definitions.

#### Print
- [Print Templates (pdfme v5)](print-templates.md) — Template designer, field linking (preset/custom/extra), and v5 field properties (`readOnly`, `required`, `extraPath`).

### 🧪 Testing
- [Testing Strategy](testing/strategy.md) - Test layers, spec-first workflow, tooling, and project structure.

### 📘 Guides & Standards
- [Development Setup](guides/setup-dev.md) - Getting started with Docker and local env.
- [Deployment](guides/deployment.md) - CI/CD pipelines and release process.
- [AI Agent Rules](guides/agent-rules.md) - Instructions for AI assistants working in this repo.

### 🔐 Security
Security model, identity, and transport hardening.
- [IIoT Security Model](security/iiot-security.md) - Control plane, signed updates, edge identity/PKI, audit & compliance evidence.
- [Tokens (Authentication)](security/tokens.md) - JWT access/session/API tokens, SSE tickets, revocation.
- [HTTPS / TLS](security/https.md) - Traefik termination, Let's Encrypt, custom certificates.

### 🛠️ Operations
Runbooks and operational procedures for production / customer deployments.
- [Workflow DB Recovery](operations/workflow-db-recovery.md) — `progress_workflow-db` crash-loop diagnosis and `pg_resetwal` recovery.
- [Workflow DB Backup](operations/workflow-db-backup.md) — `pg_dump` backup strategy and restore procedure.

---

*This documentation is automatically mirrored to the GitLab Wiki.*
