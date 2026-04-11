---
plan: 02-04
phase: 02-critical-event-tests
status: complete
completed: 2026-04-10
requirements_covered: [PROG-01, PROG-02, PROG-03, PROG-04, PROG-05, PROG-06, PROG-07, PROG-08, PROG-09, PROG-12, PROG-13, PROG-14, PROG-15, PROG-16, PROG-17]
tests_written: 16
tests_passed: 16
---

# Plan 02-04 Summary: ProgressOverrideRequestedEvent Dual-Layer Test Suite

## What Was Built

`testing/pytest/tests/progress/test_progress_override.py` — 16 tests in two classes covering validation errors, quantity increase/decrease business logic, and HTTP API layer for ProgressOverrideRequestedEvent.

## Test Structure

**TestProgressOverrideDirect (14 methods):**
- Validation errors (PROG-12 to PROG-16): no assignee, active job, active batch, traceability enabled, insufficient upstream WIP
- Quantity increase (PROG-01, PROG-04, PROG-05, PROG-08): forced batch created, time redistribution, CREATED→STARTED transition, upstream WIP reduction
- Quantity decrease (PROG-02, PROG-03, PROG-06, PROG-07, PROG-09): batch cancellation, over-cancel compensating batch, CLOSED→STARTED reopening, queue reorder, downstream WIP reduction

**TestProgressOverrideAPI (2 methods):**
- PROG-17: HTTP POST /event returns 200
- PROG-13 HTTP layer: active job returns 422

## Infrastructure Fixes

**conftest.py — Config restore bug (critical cross-test contamination fix):**

The `truncate_collections` fixture used `config_col.update(doc)` with the original snapshot (which included `_rev`). ArangoDB rejected updates when `_rev` mismatched (HTTP 412). As a result, `enable_inventory_management` was never restored to `False` after batch tests seeded it to `True`. Fix: strip `_rev` from restore doc and pass `check_rev=False`.

Also added deletion of Config keys not present in the original snapshot (e.g., keys inserted by `seed_config()` that didn't exist in schema init).

**conftest.py — `create_serial` `deleted` field:**
Added `deleted: False` default to `create_serial` fixture so serial documents match the `Serial.find({"deleted": False})` query used in receipt-with-traceability handlers.

## Key Findings

- `WorkOrder.phase_sequence` must be seeded for all tests — required by `GET_AVAILABLE_WIP_UPSTREAM_AND_DOWNSTREAM_OF_JOB` AQL
- `batch.qt_pass` must be set on completed batches — `_cancel_batches_for_quantity_decrease` uses it to sum cancellable quantity (default is 0.0)
- `ProgressOverrideRequestedEvent` response body: `{"status": 200, "detail": None, "message": None}` — assert on `status`, not `detail`

## Verification

```
16 passed
```
