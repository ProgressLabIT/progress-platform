# Phase 2: Critical Event Test Suites - Context

**Gathered:** 2026-04-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver deep dual-layer test suites (HTTP API via httpx.AsyncClient + direct event instantiation via event.save(db)) for the 4 critical production events: StepCompletedEvent, BatchCompletedEvent, ProgressOverrideRequestedEvent, and MovementCompletedEvent. Tests run against a real ArangoDB via testcontainers. No frontend tests, no new infrastructure — this phase consumes Phase 1 fixtures.

</domain>

<decisions>
## Implementation Decisions

### Event Instantiation Strategy
- **D-01:** Direct event tests call `event.save(db)` against the real ArangoDB testcontainer — no mocking of the transaction layer
- **D-02:** Pattern: seed preconditions via Phase 1 factory fixtures → instantiate event with info dict → call `event.save(db)` → assert on collection documents via `db.collection().find()`/`db.collection().get()`
- **D-03:** HTTP API tests use `httpx.AsyncClient` (session-scoped from Phase 1) with auth_headers fixture — these test the endpoint → event dispatch chain
- **D-04:** The two layers are cleanly separated by assertion surface: API tests assert on HTTP response shape, direct tests assert on DB state

### Cascade Assertion Strategy
- **D-05:** For cascading events (BatchCompleted → child events), assert the parent event's own DB state changes (batch status, work session closed, job progress) + verify child events were recorded in the Event collection
- **D-06:** Do NOT duplicate child event DB side effect assertions in parent tests — child events have their own test suites (MovementCompleted is in this phase, others will follow)
- **D-07:** Query the Event collection to verify each expected child event type was dispatched with correct info — this catches missing `create_as_child()` calls without coupling to child apply() logic

### BatchCompleted Parametrize Matrix
- **D-08:** Use a curated ~16-test pairwise matrix instead of full 32 cartesian product
- **D-09:** Eliminate impossible combinations: `auto_new_batch=True` + last batch (no remaining quantity) is a no-op
- **D-10:** Treat `step_check` as orthogonal — 2 isolated tests (with/without step_data) rather than crossing it with all cascade flags
- **D-11:** Cover all real flag interactions: first/last phase × traceability × warehouse_management × auto_new_batch (non-last-batch scenarios only)
- **D-12:** Include comment block in parametrize decorator documenting excluded combinations and why
- **D-13:** Update BATCH-20 success criterion wording from "32-combination" to reflect actual curated count

### Plan Splitting (6 plans)
- **D-14:** Plan 02-01: StepCompletedEvent (8 requirements: STEP-01 through STEP-08, both layers)
- **D-15:** Plan 02-02: BatchCompletedEvent HTTP API tests (~10 requirements: happy paths, validation errors, HTTP integration via endpoint)
- **D-16:** Plan 02-03: BatchCompletedEvent direct event tests (~11 requirements: cascade branches, parametrized matrix, edge cases via event.save(db))
- **D-17:** Plan 02-04: ProgressOverrideRequestedEvent (17 requirements: PROG-01 through PROG-17, both layers)
- **D-18:** Plan 02-05: MovementCompletedEvent type coverage (~10 requirements: receipt, shipment, adjustment, transfer, container transfer, production, consumption, planned movement, reversal guard, deleted position)
- **D-19:** Plan 02-06: MovementCompletedEvent API + serial traceability (~6 requirements: serial paths, HTTP integration, remaining edge cases)

### Claude's Discretion
- Test helper organization — whether to create shared assertion helpers (e.g., `assert_event_dispatched()`) or keep assertions inline per test
- Exact requirement-to-plan mapping for BATCH split — Claude to assign requirements to 02-02 vs 02-03 during planning based on which layer each requirement belongs to
- Fixture composition for complex preconditions — whether to create higher-level "scenario" fixtures or compose Phase 1 factories inline

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Event Source Code (test targets)
- `backend/api/events/production/step_completed.py` — 93 lines, StepCompletedEvent with apply() logic and BatchCompleted child dispatch
- `backend/api/events/production/batch_completed.py` — 489 lines, BatchCompletedEvent with full cascade: WIP, serials, movements, job close, auto_new_batch
- `backend/api/events/admin/progress_override_requested.py` — 292 lines (note: lives in admin/, not production/), ProgressOverrideRequestedEvent with WIP management, inventory movements, job state transitions
- `backend/api/events/inventory/movement_completed.py` — 292 lines, MovementCompletedEvent handling 16 movement types

### Event Base Classes
- `backend/api/events/base_event.py` — BaseEvent with save() → pre_processing() → apply() → store_event() → commit_transaction() flow
- `backend/api/events/production/base_production.py` — BaseProductionEvent with shared helpers (_get_job_data, get_current_work_session, get_batch_execution_data, update_job_step_progress)
- `backend/api/events/admin/base_admin.py` — BaseAdmin with _reduce_wip, update_work_order, NON_CANCELED_BATCHES_BY_JOB query
- `backend/api/events/inventory/base_inventory.py` — BaseInventory event base

### Domain Models
- `backend/api/models/traceability.py` — Batch, WorkSession, StepExecutionData, StepStatus, WIP, ExecutionDataUpdate
- `backend/api/models/production.py` — Job, WorkOrderFull, WorkStatus
- `backend/api/models/inventory.py` — InventoryMovementType, InventoryMovementReferences
- `backend/api/models/event.py` — EventType enum, EventInfoModel base
- `backend/api/models/form.py` — FormFieldValue, SerialFormFieldValue

### Endpoints (for HTTP API tests)
- `backend/api/endpoints/production.py` — StepCompleted and BatchCompleted dispatch endpoints
- `backend/api/endpoints/admin.py` — ProgressOverrideRequested dispatch endpoint
- `backend/api/endpoints/inventory.py` — MovementCompleted dispatch endpoint

### Query Utilities
- `backend/api/utils/production.py` — ProductionQueries (GET_WORKING_JOB_DATA, REORDER_JOB_QUEUES, ADD_JOB_TO_QUEUE)
- `backend/api/utils/traceability.py` — TraceabilityQueries (COMPLETE_BATCH, GET_BATCH_EXECUTION_DATA, GET_AVAILABLE_WIP_UPSTREAM_AND_DOWNSTREAM_OF_JOB)
- `backend/api/utils/inventory.py` — InventoryQueries (PRODUCTS_INVENTORY_CONFIG)
- `backend/api/utils/serial.py` — SerialQueries (GET_BATCH_SERIALS)
- `backend/api/utils/counter.py` — _generate_counter for serial code generation

### Test Infrastructure (from Phase 1)
- `testing/pytest/conftest.py` — Root conftest with db, mock_nats, client, auth_headers, truncate_collections fixtures
- `testing/pytest/tests/factories/conftest.py` — All factory fixtures (create_user, create_product, create_work_order, create_job, create_batch, create_work_session, create_step_execution, seed_config, create_serial, create_wip, create_position, create_queue, create_production_graph)
- `testing/pytest/conftest_helpers/schema.py` — Schema initialization with all 48 collections

### Testing Strategy
- `km/testing/strategy.md` — Spec-first development loop, real database requirement, test layers

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Phase 1 factory fixtures: `create_production_graph` composes full WorkOrder→Job→Batch→WorkSession→StepExecution graphs with parametrized flags (first_phase, last_phase, traceability, warehouse, auto_new_batch, step_check)
- `seed_config` fixture: upserts Config records (enable_inventory_management, default_operation_parameters) needed for BatchCompleted branches
- `auth_headers` fixture: generates JWT tokens with configurable scopes for API tests

### Established Patterns
- Events use `create_as_child()` to spawn child events within the same transaction — child events share parent's tx object
- Events store themselves in the Event collection via `store_event()` — queryable for cascade assertion verification
- `BaseProductionEvent._get_job_data()` fetches job, product, and phase info — must be seeded correctly in fixtures
- `BatchCompletedEvent.warehouse_management_enabled` is a `@cached_property` that reads Config collection
- `ProgressOverrideRequestedEvent` lives in `events/admin/` not `events/production/` — inherits from BaseAdmin not BaseProductionEvent

### Integration Points
- Test files go in `testing/pytest/tests/step/`, `tests/batch/`, `tests/progress/`, `tests/movement/` per D-02 from Phase 1
- Factory fixtures imported via pytest's conftest chain (tests/factories/conftest.py)
- httpx.AsyncClient fixture from root conftest for API layer

</code_context>

<specifics>
## Specific Ideas

- BatchCompleted parametrize matrix should use explicit test IDs (e.g., `first-phase-no-trace-no-wh`) not auto-generated ones, for readable test output
- ProgressOverrideRequested has 6 distinct validation error paths (PROG-12 through PROG-16 + ValueError) — these are quick tests that should use `pytest.raises()`
- MovementCompleted's 16 types are mostly parallel (same setup pattern, different movement_type enum) — good candidate for parametrize with a fixture factory
- The Event collection can be queried with `db.collection('Event').find({'event_type': 'BATCH_COMPLETED'})` to verify cascade dispatch

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-critical-event-tests*
*Context gathered: 2026-04-10*
