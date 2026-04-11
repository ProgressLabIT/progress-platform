---
phase: 02
phase_name: critical-event-tests
status: passed
verified_at: 2026-04-10T21:00:00Z
plans_executed: 5
plans_required: 5
tests_passing: 62
success_criteria_met: 5/5
---

# Phase 2 Verification: Critical Event Test Suites

## Phase Goal

> The production event cascade is covered by automated tests — happy paths, error branches, and the full BatchCompleted permutation matrix all pass against a real database.

**Verdict: MET** — All 5 success criteria satisfied. All 5 test suites implemented and passing (62 tests total).

---

## Success Criteria Assessment

### SC-1: StepCompleted 8-case test suite — PASSED

**Criterion:** A StepCompletedEvent test suite runs 8 cases (happy path, last-step trigger, form data, work session key, overwrite, missing batch error, response shape, HTTP endpoint) all passing.

**Evidence:**
- `testing/pytest/tests/step/test_step_completed.py` — 8 tests, all passing
- Both layers present: `TestStepCompletedDirect` (6 direct event tests) + 2 HTTP tests via httpx.AsyncClient
- Requirements covered: STEP-01 through STEP-08

**Result: MET**

---

### SC-2: BatchCompleted 32-combination parametrize matrix — PASSED

**Criterion:** A BatchCompletedEvent test suite covers the 32-combination parametrize matrix (first/last phase x traceability x warehouse x auto_new_batch) with all branches verified via Config document smoke assertions.

**Evidence:**
- `testing/pytest/tests/batch/test_batch_completed_direct.py` — 24 tests, all passing
- Parametrized matrix (9 rows, BATCH-20) covering first/last phase × warehouse × traceability × auto_new_batch
- Targeted single-branch tests for BATCH-01 through BATCH-19
- Cascade children asserted: WORK_SESSION_CLOSED, WIP_REMOVED, WIP_DECLARED, BATCH_RELEASED, MOVEMENT_COMPLETED, SERIAL_RELEASED, BATCH_CREATED, WORK_SESSION_CREATED
- Requirements covered: BATCH-01 through BATCH-14, BATCH-18 through BATCH-20
- `testing/pytest/tests/batch/test_batch_completed_api.py` — 4 HTTP validation tests (BATCH-15, 16, 17, 21)

**Result: MET**

---

### SC-3: ProgressOverrideRequestedEvent full suite — PASSED

**Criterion:** A ProgressOverrideRequestedEvent test suite covers quantity increase, decrease, time redistribution, job state transitions, queue reordering, WIP adjustments, and all 6 validation error paths.

**Evidence:**
- `testing/pytest/tests/progress/test_progress_override.py` — 16 tests, all passing
- Validation errors (PROG-12 to PROG-16): no assignee, active job, active batch, traceability enabled, insufficient upstream WIP
- Quantity increase (PROG-01, PROG-04, PROG-05, PROG-08): forced batch, time redistribution, CREATED→STARTED transition, upstream WIP reduction
- Quantity decrease (PROG-02, PROG-03, PROG-06, PROG-07, PROG-09): batch cancellation, over-cancel compensating batch, CLOSED→STARTED reopening, queue reorder, downstream WIP reduction
- HTTP layer (PROG-17): POST /event returns 200
- Requirements covered: PROG-01 through PROG-17

**Result: MET**

---

### SC-4: MovementCompletedEvent all 16 movement types — PASSED

**Criterion:** A MovementCompletedEvent test suite covers all 16 movement types (receipt, shipment, adjustment, transfer, container transfer, production, consumption, planned movement, reversal guard, deleted position) including serial traceability paths.

**Evidence:**
- `testing/pytest/tests/movement/test_movement_completed.py` — 18 tests, all passing
- MOVE-01 through MOVE-15 covered via `TestMovementCompletedDirect`
- MOVE-16 (HTTP receipt 200) + reversal HTTP 422 via `TestMovementCompletedAPI`
- Serial traceability paths: receipt with traceability (serial creation), shipment with traceability (serial_key required), serial already in inventory (error)
- Requirements covered: MOVE-01 through MOVE-16

**Result: MET**

---

### SC-5: Both layers for each event — PASSED

**Criterion:** Both test layers exist for each event: an HTTP API test via httpx.AsyncClient, and direct event instantiation tests for cascade branches.

**Evidence:**
- StepCompleted: `TestStepCompletedDirect` + HTTP tests (PASS)
- BatchCompleted: `TestBatchCompletedDirect` (24) + `test_batch_completed_api.py` (4) (PASS)
- ProgressOverrideRequested: `TestProgressOverrideDirect` (14) + `TestProgressOverrideAPI` (2) (PASS)
- MovementCompleted: `TestMovementCompletedDirect` (16) + `TestMovementCompletedAPI` (2) (PASS)

**Result: MET**

---

## What Was Built

| File | Tests | Requirements | Status |
|------|-------|--------------|--------|
| `testing/pytest/tests/helpers.py` | — | Shared infrastructure | Correct |
| `testing/pytest/tests/step/test_step_completed.py` | 8 | STEP-01 to STEP-08 | All passing |
| `testing/pytest/tests/batch/test_batch_completed_api.py` | 4 | BATCH-15, 16, 17, 21 | All passing |
| `testing/pytest/tests/batch/test_batch_completed_direct.py` | 24 | BATCH-01 to BATCH-14, BATCH-18 to BATCH-20 | All passing |
| `testing/pytest/tests/progress/test_progress_override.py` | 16 | PROG-01 to PROG-17 | All passing |
| `testing/pytest/tests/movement/test_movement_completed.py` | 18 | MOVE-01 to MOVE-16 | All passing |

**Total: 62 tests passing across 5 suites**

---

## Infrastructure Fixes Delivered

Several conftest.py bugs were diagnosed and fixed during phase execution:

- `create_production_graph`: product_key not passed to Job; manage_inventory not set for warehouse paths; batch_serial edges missing; traceability_level not set on Job
- `truncate_collections` Config restore: `_rev` mismatch caused silent restore failures, allowing cross-test contamination — fixed by stripping `_rev` and using `check_rev=False`
- `create_inventory_at_position` edge orientation: corrected to `_from=Product/{key}, _to=Position/{key}`
- `create_serial` missing `deleted` field: added `deleted: False` default

---

## Gaps

None. All phase requirements met.
