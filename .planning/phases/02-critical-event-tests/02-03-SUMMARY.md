---
plan: 02-03
phase: 02-critical-event-tests
status: complete
completed: 2026-04-10
requirements_covered: [BATCH-01, BATCH-02, BATCH-03, BATCH-04, BATCH-05, BATCH-06, BATCH-07, BATCH-08, BATCH-09, BATCH-10, BATCH-11, BATCH-12, BATCH-14, BATCH-18, BATCH-19, BATCH-20]
tests_written: 24
tests_passed: 24
---

# Plan 02-03 Summary: BatchCompletedEvent Direct Event Test Suite

## What Was Built

`testing/pytest/tests/batch/test_batch_completed_direct.py` — 24 tests in `TestBatchCompletedDirect` covering the full cascade permutation matrix and targeted single-branch tests for BatchCompletedEvent via direct `event.save()` calls against a real ArangoDB testcontainer.

## Test Structure

**Parametrized matrix (9 rows, BATCH-20):** Covers first/last phase × warehouse × traceability × auto_new_batch combinations, asserting cascade children (WORK_SESSION_CLOSED, WIP_REMOVED, WIP_DECLARED, BATCH_RELEASED, MOVEMENT_COMPLETED, SERIAL_RELEASED, BATCH_CREATED, WORK_SESSION_CREATED).

**Targeted single-branch tests (15 methods):** BATCH-01 through BATCH-19 individually.

## Infrastructure Fixes to conftest.py

Four bugs discovered and fixed in `create_production_graph`:

1. **product_key not passed to Job** — `job.product_key` was `"unknown"`, breaking `PRODUCTS_INVENTORY_CONFIG` AQL query. Fixed by passing `product_key=product_data["product_key"]` to `create_job`.
2. **manage_inventory not set** — Warehouse movement path requires `Product.manage_inventory=True`. Fixed by updating the product document when `warehouse_management=True`.
3. **batch_serial edges not created** — `GET_BATCH_SERIALS` traversal requires `batch_serial` edges. Fixed by inserting edges when traceability is enabled.
4. **traceability_level not set on Job** — `_handle_batch_serials` checks `job.traceability_level`. Fixed by passing it from the graph builder.

## Key Findings

- `SerialUpdatedEvent` only fires when `serial_data > 0 OR serial_code is not None` — requires step form data or counter-based code generation. Tests for BATCH-11 use counter approach.
- `WIPRemovedEvent` requires booked WIP (`_to=Job/{job_key}`). Helper `_book_wip_to_job` simulates the WIPBookedEvent side-effect.
- `next_batch_available=True` must be set on Job for auto-batch creation to fire.

## Verification

```
24 passed in ~9s
```
