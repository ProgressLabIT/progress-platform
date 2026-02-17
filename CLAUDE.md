# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Progress Platform is a Manufacturing Operations Management System (MOM) built with a microservices architecture. It manages work orders, production tracking, traceability, quality management, inventory, and collaboration.

**Tech Stack:**
- **Backend**: FastAPI (Python 3.11) + ArangoDB (graph database) + Kafka
- **Workflow**: Prefect 2.x orchestration
- **Frontend Main**: Quasar Vue 3 + Pinia + i18n
- **Frontend Warehouse**: Quasar with Capacitor (mobile)
- **Infrastructure**: Docker Compose + Traefik reverse proxy

## Development Environment

The project runs entirely in Docker. Database runs without authentication in dev mode.

**Start development environment:**
```bash
# From project root
docker compose -f deploy/compose/base.yaml -f deploy/compose/dev.yaml \
  --project-directory . --project-name progress_lab_dev up -d

# With remote debugging enabled
docker compose -f deploy/compose/base.yaml -f deploy/compose/dev.debug.yaml \
  --project-directory . --project-name progress_lab up -d
docker compose -f deploy/compose/kafka.dev.yaml \
  --project-directory . --project-name kafka up -d

# Restore database
docker exec progress_lab-db-1 arangorestore \
  --input-directory "/db_backup" --all-databases true --create-database
```

**First-time setup requires creating Docker volumes** (see readme.md for details).


## Architecture Patterns

### Event-Driven System
The codebase uses an immutable event-sourcing pattern for business logic:

- **Event Base**: All events inherit from base classes in `/backend/api/events/base_event.py`
- **Event Types**: production, collaboration, work_session, wip, inventory, serial, traceability
- **Event Structure**: Each event implements:
  - `get_event_type()` - Returns event type (string)
  - `get_tx_collections()` - Returns collections involved in transaction
  - `apply()` - Executes business logic within an ArangoDB transaction
- **Event Classes**: TaskCreated, TaskCompleted, IssueCreated, IssueUpdated, JobStarted, BatchCompleted, ProgressOverrideRequested etc.
- **Storage**: Events stored in immutable `Event` collection, streamed to Kafka

### Database Design (ArangoDB)
- **Graph Database**: Uses ArangoDB with document collections and edge relationships
- **Transactions**: Multi-collection transactions ensure consistency
- **Core Collections**: WorkOrder, Job, Queue, Product, Phase, Process, Batch, WIP, Event, StepExecutionData, WorkSession, CustomField, Config, Inventory, Movement, Counting
- **Migrations**: AQL scripts in `/db/migrations/` (e.g., `226-process-steps-to-custom-fields.aql`)

### API Structure (`/backend/api`)
Main FastAPI app in `main.py` registers routers from `/endpoints/`:
- `admin.py` - Administration
- `auth.py` - Security/Authentication
- `production.py` - Work orders and jobs
- `process.py` - Process definitions
- `product.py` - Product management
- `inventory.py` - Inventory/warehouse
- `traceability.py` - Traceability tracking
- `collaboration.py` - Tasks and issues
- `serial.py`, `print.py`, `form.py`, `org.py`, `file.py`, `media.py`, etc.

**Utilities** organized in `/backend/api/utils/`:
- `db.py` - ArangoDB connection
- `auth.py` - JWT validation
- `kafka/` - Kafka producer/consumer
- `float_precision.py` - Float rounding and comparison utilities (6-decimal standard)
- Domain helpers: `production.py`, `inventory.py`, `process.py`, `collaboration.py`

**Managers** in `/backend/api/managers/`:
- WebSocket, Kafka, Executor, Notification, ServerEvent managers

### Frontend Architecture (`/webapps/main/src`)
- **State**: Pinia stores (`/stores/config.js`, `/stores/task.js`, etc.)
- **Routing**: Route-based code splitting (adminRoutes, productionRoutes, warehouseRoutes)
- **i18n**: Translations in `/src/i18n/en.js` and `/src/i18n/it.js`
- **Components**: Feature-organized Vue 3 components with Composition API
- **Plugins**: Registered in `/boot/` (pinia, i18n, axios, filters, form, theme)

### Models (`/backend/api/models`)
- `base_models.py` - FlexModel, ArangoDocument, ArangoEdge base classes
- Domain models: `production.py` (WorkOrder, Job, Batch), `product.py`, `inventory/`, `collaboration.py`
- Uses Pydantic v2 for validation and serialization

## Important Development Guidelines

### Float Precision Standards
**CRITICAL**: The codebase uses a **hybrid approach** to prevent floating-point precision noise in numeric data:

#### 1. Pydantic Model Validators (Automatic)
Float fields on key models automatically round to 6 decimals via `@field_validator`:
- **Production models**: WorkOrderFull, Job, Batch, WorkSession, WIP
- **Inventory models**: Inventory, InventoryMovement, MovementSplitData
- **Pattern**: Fields like `quantity`, `value`, `qt_planned`, `qt_completed`, `progress`, `cost`

Models with validators will round float values when data flows through Pydantic validation.

#### 2. Manual Rounding at Calculation Sites (Required)
**When to use `round_float()`**:
- Any division operation: `progress = completed / total` → `progress = round_float(completed / total)`
- Progress calculations: `100 * completed / planned` → `int(round_float(100 * completed / planned))`
- Ratio/percentage calculations: `quantity / total_quantity`
- Unit cost/value calculations: `total_cost / quantity`
- **Especially** when the result will be stored in a raw dictionary for database update

**Import**: `from utils.float_precision import round_float`

**Why**: Many database writes use raw dictionaries (not Pydantic models), bypassing automatic validation. Manual rounding at calculation sites ensures these values are clean before entering the database.

See `backend/FLOAT_PRECISION_CHECKLIST.md` for specific locations requiring manual rounding.

#### 3. Comparison Utilities (For Business Logic)
For float comparisons in business logic, use tolerance-based utilities:
```python
from utils.float_precision import float_equals, float_less_than, float_greater_than

if float_equals(available_qty, required_qty):  # Instead of: available_qty == required_qty
    ...

if float_less_than(stock, threshold, epsilon=1e-6):  # Configurable epsilon
    ...
```

**Standard**: 6 decimal precision, 1e-6 absolute epsilon tolerance (configurable via `PROGRESS_FLOAT_PRECISION_DECIMALS` env var).

### Translations (from AGENTS.md)
**CRITICAL**: When adding any new text to webapps, **always add translations** in the related language files in `src/i18n/` folder (both `en.js` and `it.js`). The platform supports Italian and English.

### Code Changes
- Ask clarifying questions if uncertain about intentions
- Evaluate inputs for missing information before proceeding
- For changes affecting more than a few lines, explain your approach first and get explicit approval before implementing

### Security Considerations
- Backend uses JWT authentication with custom middleware
- Dev environment runs DB without authentication (never use in production)
- CORS middleware allows all origins/methods/headers in current config

## CI/CD

GitLab CI pipeline (`.gitlab-ci.yml`) triggers on version tags matching `v[0-9]+.[0-9]+.(a|b|rc)?[0-9]+`:
- Builds Docker images for: webapp (main app), warehouse, api, workflow
- Pushes to GitLab Container Registry with tags: `$BRANCH_VERSION-latest` and `$VERSION`

## Docker Compose Files

Multiple compose files in `/deploy/compose/`:
- `base.yaml` - Core services (Traefik, API, DB, Kafka, media volumes)
- `dev.yaml` - Development overrides with hot-reload and source mounts
- `dev.debug.yaml` - Remote debugging configuration
- `workflow.yaml` - Prefect server + PostgreSQL
- `stack.yaml` - Production swarm deployment
- `kafka.dev.yaml` - Kafka in KRaft mode (no ZooKeeper)

## Key Technology Versions

- Python: 3.11 (backend/workflow), 3.8 (legacy/symlinked code)
- Node: 20/18/16/14.19 (webapps)
- FastAPI: 0.x with Pydantic v2
- Quasar: 2.14+ (main), 2.16+ (warehouse)
- Vue: 3.x with Composition API
- ArangoDB client: python-arango 8.x
- Prefect: 2.x
- Traefik: 2.3

## Useful Patterns

- **Model Base Classes**: Extend `FlexModel`, `ArangoDocument`, or `ArangoEdge` for consistency
- **Event Handlers**: Implement event classes for business logic rather than direct DB operations
- **Transactions**: Use event `apply()` methods to ensure transactional consistency
- **API Response**: Endpoints use standard response wrappers
- **Middleware Stack**: CORS → GZip (filters /notification) → NotificationMiddleware → Auth
- **Float Precision**: Use `round_float()` for calculations, Pydantic validators for models, tolerance utilities for comparisons (see Float Precision Standards above)


## 3. High-Level Feature Description

The Progress Platform is a Manufacturing Operating System with a focus on traceability, planning, and quality control.

Key features include:

*   **Master Data Management**:
    *   **Products**: Managing product definitions, bills of materials (BOMs), and production processes (`MasterData.yaml`, `backend/api/endpoints/product.py`).
    *   **Organizational Structure**: Defining departments, equipment, users, and groups (`MasterData.yaml`, `backend/api/endpoints/org.py`).
*   **Production Planning & Execution**:
    *   **Work Orders & Jobs**: Creating and managing work orders and the associated jobs for different production phases (`Planning.yaml`, `backend/api/endpoints/production.py`).
    *   **Real-time Traceability**: Tracking serial numbers, batches, and work-in-progress (WIP) throughout the production process (`Traceability.yaml`, `backend/api/endpoints/traceability.py`).
*   **Inventory Management**:
    *   Managing stock levels of products, materials, and other items (`Inventory.yaml`, `backend/api/endpoints/inventory.py`).
    *   The `warehouse` application provides a mobile interface for these operations.
*   **Issue, Tasks, Data Collection**:
    *   **Issue Tracking**: Reporting and managing quality issues that arise during production (`backend/api/endpoints/collaboration.py`).
    *   **Task Management**: Assigning, monitoring and executing tasks (`backend/api/endpoints/collaboration.py`).
    *   **Data Collection**: Using forms and steps to collect data during the production process (`backend/api/endpoints/form.py`).
*   **User Management & Security**:
    *   Authentication and authorization are handled by the backend, using JWT for session management (`backend/api/endpoints/auth.py`).


# KM
Check out .cursor/rules/km.mdc for knowledge management policies.
