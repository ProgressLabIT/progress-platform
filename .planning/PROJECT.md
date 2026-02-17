# Progress Platform - Float Precision Fix

## What This Is

A Manufacturing Operations Management (MOM) system that manages work orders, production tracking, inventory, traceability, quality control, and collaboration across manufacturing operations. Built with FastAPI backend, Vue 3 frontend, event-driven architecture using ArangoDB and Kafka, serving production operators and warehouse staff.

## Core Value

**Accurate, clean numeric data throughout the system** — quantities, progress, and measurements display correctly to users without floating-point noise, and comparisons work reliably without epsilon drift errors.

## Requirements

### Validated

<!-- Existing capabilities confirmed in the codebase -->

- ✓ **Event-driven architecture** — Immutable event log with CQRS pattern (`backend/api/events/`) — existing
- ✓ **Production management** — Work orders, jobs, batches, phases, processes, WIP tracking — existing
- ✓ **Inventory management** — Movements, counting, stock levels, warehouse operations — existing
- ✓ **Traceability** — Serial number tracking, batch tracking, genealogy — existing
- ✓ **Collaboration** — Tasks, issues, data collection forms — existing
- ✓ **Real-time updates** — WebSocket + Kafka for live state changes — existing
- ✓ **Multi-tenant architecture** — Organizations, departments, users, permissions — existing
- ✓ **Database transactions** — ArangoDB multi-collection ACID transactions in events — existing
- ✓ **Dual frontends** — Main Quasar app + mobile warehouse app with Capacitor — existing
- ✓ **i18n support** — English and Italian translations — existing

### Active

<!-- Float precision fix scope -->

- [ ] **FLOAT-01**: All float values round to 6 decimal places when written to ArangoDB via serializer
- [ ] **FLOAT-02**: All float comparisons in business logic use tolerance-based equality (epsilon 1e-6)
- [ ] **FLOAT-03**: Vue components display quantities with clean decimal formatting (no trailing noise)
- [ ] **FLOAT-04**: Movement and inventory quantity displays show round numbers (e.g., 100.0 not 100.000001)
- [ ] **FLOAT-05**: Progress percentages display cleanly without floating-point artifacts
- [ ] **FLOAT-06**: Duration/time calculations in work sessions round consistently
- [ ] **FLOAT-07**: Batch completion and consumption quantities display cleanly
- [ ] **FLOAT-08**: Helper utility functions for tolerance-based comparison available system-wide

### Out of Scope

- **Migrate to Decimal type** — Too complex across Pydantic models, DB, frontend; float + rounding sufficient for domain needs
- **Migrate existing database values** — Leave historical data as-is, fix going forward only
- **Change number precision standard** — 6 decimals is the fixed standard, not configurable
- **Currency/monetary fields** — Not currently in scope; may revisit Decimal for true financial reconciliation in future
- **Test suite creation** — No active test suite to update; focus on implementation only

## Context

**Trigger**: UI displays excessive decimal places in movement/inventory quantities (e.g., `100.000001` instead of `100.0`), causing user confusion and visual noise. Root cause is floating-point arithmetic in division operations (progress calculations, unit processing time, proportional distributions).

**Analysis completed**: Reviewed warehouse movements, inventory events, and related calculations. Determined that:
- Most operations are additions/subtractions/multiplications (low drift risk)
- Critical divisions: progress %, unit processing time, quantity ratios, proportional splits
- Domain requires fixed precision (6 decimals), not algebraic exactness
- Float + disciplined rounding is superior to Decimal migration (complexity/performance trade-off)

**Existing serializer**: `backend/api/utils/db.py` has `model_to_db_dict()` and custom `encoder()` — ideal place to inject rounding logic for all DB writes.

**Tech stack**:
- Backend: FastAPI + Pydantic v2 + ArangoDB (python-arango 8.x)
- Frontend: Vue 3 + Quasar 2.16 + Pinia
- Event system: 82 event classes across 7 domains (production, inventory, collaboration, serial, work_session, wip, admin)

**Affected areas**:
- Quantities: `quantity`, `consumed_quantity`, `available_quantity`, etc.
- Progress: `progress` percentages, completion ratios
- Durations: Work session durations, processing times
- Any float field system-wide

## Constraints

- **Tech stack**: Must work with existing FastAPI + Pydantic v2 + ArangoDB + Vue 3 stack
- **Backwards compatibility**: Existing data in ArangoDB untouched; new writes only
- **No test suite**: No automated tests to update or maintain
- **Performance**: Rounding overhead must be negligible (single rounding op per float per write)
- **Brownfield**: Cannot break existing event application logic or API contracts

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Round at boundaries (not just divisions) | Prevents drift accumulation, ensures consistency, solves UI problem comprehensively, future-proof | — Pending |
| Use float (not Decimal) | Domain needs fixed precision (6 decimals), not algebraic equality; Decimal adds complexity across layers + performance cost | — Pending |
| 6 decimal precision standard | Sufficient for manufacturing quantities, progress, durations; common industry standard | — Pending |
| Tolerance 1e-6 for comparisons | Matches 6 decimal precision; prevents off-by-epsilon bugs in business logic | — Pending |
| Leave existing DB data as-is | Historical data doesn't cause issues; fix going forward only; avoids risky migration | — Pending |
| Inject rounding in db.py serializer | Single chokepoint for all DB writes; ensures consistency without hunting for write sites | — Pending |

---
*Last updated: 2026-02-17 after initialization*
