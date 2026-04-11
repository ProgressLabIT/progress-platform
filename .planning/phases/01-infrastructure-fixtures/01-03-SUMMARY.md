---
phase: 01-infrastructure-fixtures
plan: 03
subsystem: testing
tags: [pytest, fixtures, factories, arangodb, domain-model]

# Dependency graph
requires:
  - 01-01 (db fixture, ArangoDB schema, conftest infrastructure)
provides:
  - 9 function-scoped factory fixtures in testing/pytest/tests/factories/conftest.py
  - create_user (FACT-01), create_product (FACT-02), create_bom (FACT-03)
  - create_work_order (FACT-04), create_job (FACT-05), create_batch (FACT-06)
  - create_work_session (FACT-07), create_step_execution (FACT-08), seed_config (FACT-09)
affects:
  - 01-02 (wave-2 parallel: StepCompleted test plan)
  - 01-04 (BatchCompleted test plan — builds on these factories)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Function-scoped pytest fixtures returning factory callables (not instances)
    - raw db.collection("X").insert() — never create_as_child()
    - Batch uses work_order_key (not wo_key) — matches ArangoDB document field
    - Job parameters stored as plain dict (PhaseParameters structure)
    - canceled and modified fields on Batch/WorkSession/StepExecutionData are strings (event ids), not booleans
    - seed_config uses upsert pattern: get → update if exists, insert if not

key-files:
  created:
    - testing/pytest/tests/factories/conftest.py
  modified: []

key-decisions:
  - "Batch uses work_order_key not wo_key — verified from traceability.py Batch model"
  - "Job parameters stored as dict (not PhaseParameters object) for direct ArangoDB insert"
  - "WorkSession requires phase_key and product_key (not just batch_key/job_key) — verified from model"
  - "canceled field is string (event id) not bool — allows audit trail of cancellation event"
  - "form_data on StepExecutionData is list not dict — matches FormFieldValue list type in model"
  - "std_processing_time in create_job is stored in parameters dict, not at Job root level"

# Metrics
duration: 15min
completed: 2026-04-09
---

# Phase 01 Plan 03: Core Domain Factory Fixtures Summary

**9 function-scoped factory fixtures using raw ArangoDB inserts — field names verified against production Pydantic models and event apply() methods**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-04-09T13:15:00Z
- **Completed:** 2026-04-09T13:28:35Z
- **Tasks:** 1 of 1
- **Files modified:** 1 created

## Accomplishments

- All 9 factory fixtures (FACT-01 through FACT-09) implemented in `testing/pytest/tests/factories/conftest.py`
- Field names verified against actual Pydantic models (`backend/api/models/production.py`, `backend/api/models/traceability.py`) and event source code (`step_completed.py`, `batch_completed.py`, `work_session_created.py`)
- Key field name corrections applied vs. plan template (see Deviations section)
- `seed_config` implements upsert pattern for controlling event branches like `enable_inventory_management`

## Task Commits

1. **Task 1: Create core domain factory fixtures** - `a3440b69` (feat)

## Files Created/Modified

- `testing/pytest/tests/factories/conftest.py` — 9 factory fixtures (515 lines), fully documented with field name source references

## Decisions Made

- **`Batch.work_order_key` not `wo_key`**: The Batch Pydantic model in `traceability.py` uses `work_order_key` — the plan template incorrectly used `wo_key`. Fixed to match the actual model.
- **Job parameters as dict**: `PhaseParameters` fields (step_check, auto_new_batch, production_batch_qt) are stored nested in a `parameters` dict on the Job document — this is how `batch_completed.py` reads `self.job.parameters.step_check`.
- **WorkSession requires `phase_key` and `product_key`**: The model requires these fields beyond just `batch_key` and `job_key`. Added defaults of `"unknown"` to remain test-friendly.
- **`canceled` as string not bool**: On Batch, WorkSession, and StepExecutionData, the `canceled` field is a string (event id of the canceling event) not a boolean. Default is `None` (not canceled).
- **`form_data` as list**: `StepExecutionData.form_data` is `list[FormFieldValue]` not a dict. Factory initializes it as an empty list.
- **`WorkOrder.wo_code` not `code`**: The plan template used `code` as the WorkOrder code field but the model uses `wo_code`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected Batch field from `wo_key` to `work_order_key`**
- **Found during:** Task 1 (model verification)
- **Issue:** Plan template used `work_order_key: wo_key` for Batch but the actual Batch model in `traceability.py` uses `work_order_key` as the field name. Events like `batch_completed.py` do `self.batch.work_order_key` to resolve the work order.
- **Fix:** Used `work_order_key` in `create_batch`; also added `phase_key` as required parameter since it's a required field on Batch.
- **Files modified:** testing/pytest/tests/factories/conftest.py
- **Commit:** a3440b69

**2. [Rule 1 - Bug] Corrected WorkOrder code field from `code` to `wo_code`**
- **Found during:** Task 1 (model verification)
- **Issue:** Plan template used `"code": f"WO-TEST-{key}"` but WorkOrderFull model uses `wo_code`. Events reference `self.job.wo_key` to get the WO key but the WO document itself uses `wo_code` for display.
- **Fix:** Used `wo_code` in `create_work_order`.
- **Files modified:** testing/pytest/tests/factories/conftest.py
- **Commit:** a3440b69

**3. [Rule 2 - Missing Critical] Added `phase_key`, `product_key` required fields to `create_batch`**
- **Found during:** Task 1 (model verification)
- **Issue:** Plan template only had `wo_key`, `phase_key` as optional. The Batch model requires `phase_key` and the events read `self.batch.phase_key` to determine phase-level WIP movements.
- **Fix:** Added `phase_key` and `product_key` as parameters (with "unknown" defaults) on `create_batch`.
- **Files modified:** testing/pytest/tests/factories/conftest.py
- **Commit:** a3440b69

**4. [Rule 2 - Missing Critical] Added `phase_key` and `product_key` required fields to `create_work_session`**
- **Found during:** Task 1 (model verification)
- **Issue:** The WorkSession model requires `phase_key`, `work_order_key`, and `product_key` — not just `batch_key` and `job_key`. WorkSessionCreatedEvent reads all these from the job, so tests wiring a real workflow need all fields populated.
- **Fix:** Added `work_order_key`, `phase_key`, `product_key` as keyword arguments with "unknown" defaults.
- **Files modified:** testing/pytest/tests/factories/conftest.py
- **Commit:** a3440b69

**5. [Rule 1 - Bug] Fixed Job's required fields to include `wo_code`, `phase_alias`, `product_code`, `product_description`, `operation_key`**
- **Found during:** Task 1 (model verification)
- **Issue:** The Job model has required fields beyond `wo_key` and `phase_key`. Events instantiate `Job(**self.tx.collection('Job').get(...))` so missing required fields cause Pydantic validation errors.
- **Fix:** Added all required Job fields with sensible defaults derived from the provided keys.
- **Files modified:** testing/pytest/tests/factories/conftest.py
- **Commit:** a3440b69

---

**Total deviations:** 5 auto-fixed (2 bug fixes, 3 missing critical fields)
**Impact on plan:** All corrections required for events to read factory-created documents without Pydantic validation errors. No scope creep.

## Known Stubs

None — all factory fixtures produce complete documents with real field values. The "unknown" defaults on optional cross-reference fields (e.g., `work_order_key="unknown"` on WorkSession) are intentional: tests that need accurate cross-references must provide the real keys, while tests only needing the document to exist can use the defaults.

## Issues Encountered

None — all corrections were deterministic fixes based on model inspection.

## User Setup Required

None.

## Next Phase Readiness

- All 9 factory fixtures available for tests in Plans 01-02 (StepCompleted) and 01-04 (BatchCompleted)
- Factories compose: `create_work_order` → `create_job` → `create_batch` → `create_work_session` → `create_step_execution`
- `seed_config("enable_inventory_management", value=True/False)` controls inventory movement code paths in BatchCompleted

---
*Phase: 01-infrastructure-fixtures*
*Completed: 2026-04-09*
