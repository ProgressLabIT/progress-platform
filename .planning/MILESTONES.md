# Milestones

## v2.0 Test Suite (Shipped: 2026-04-11)

**Phases completed:** 4 phases, 15 plans
**Timeline:** 2026-04-09 → 2026-04-11 (3 days)
**Tests written:** 75+ backend tests, 19 component tests, 10 E2E scripts

**Key accomplishments:**

- pytest + testcontainers harness: ArangoDB 3.11 ephemeral container, db singleton override before backend import, NATS mock, httpx ASGI client — full isolation via per-class collection truncation
- 14 domain factory fixtures (WorkOrder, Job, Batch, WorkSession, StepExecution, User, Product, BOM, Config, Serial, WIP, Position, Queue) built on raw ArangoDB inserts verified against production Pydantic models
- Dual-layer test suites for 4 critical events: StepCompleted (8 tests), BatchCompleted (24 tests, 9-row parametrize matrix), ProgressOverrideRequested (16 tests), MovementCompleted (18 tests, 16 movement types)
- OpenAPI coverage audit (75+ routes via app.routes introspection, warn-only) + Schemathesis fuzzing (zero 5xx on valid inputs) + Locust load scenarios for 3 critical endpoints
- Vitest component tests for ProgressBtn.vue (8 tests) and WorkSessionSteps.vue (11 tests) + Playwright E2E scripts for 3 critical user journeys

**Known gaps (tech debt):** BATCH-13, PROG-10, PROG-11 — complex warehouse-interaction paths deferred
**Archive:** `.planning/milestones/v2.0-ROADMAP.md`

---

## v1.0 Printing v2 (Shipped: 2026-03-20)

**Phases completed:** 4 phases, 14 plans
**Timeline:** 2026-03-12 → 2026-03-20 (9 days)
**Files changed:** 117 files, 15,634 insertions

**Key accomplishments:**

- Template string `{{variable}}` composite text fields in pdfme designer with full encode/decode/resolve pipeline
- Pure-JS `generateZpl()` transpiler covering text, all 5 barcode types (QR/128/39/EAN-13/GS1), and image skipping at configurable DPI
- On-prem SSE-subscriber print service + raw TCP relay with Docker Compose deployment and health endpoint
- PrintDialog "Send to Printer" action with ZPL/PDF routing and real-time SSE feedback (no false positives)
- Warehouse app migrated from hardcoded Zebra `/pstprint` to unified print service + configurable pdfme templates
- Full documentation in `km/domains/printing/print-templates.md` covering all new capabilities

**Archive:** `.planning/milestones/v1.0-ROADMAP.md`

---
