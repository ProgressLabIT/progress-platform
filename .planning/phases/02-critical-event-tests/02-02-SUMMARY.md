---
plan: 02-02
phase: 02-critical-event-tests
status: completed
started: 2026-04-10T16:29:47Z
completed: 2026-04-10T16:35:29Z
requirements: [BATCH-15, BATCH-16, BATCH-17, BATCH-21]
---

# Plan 02-02 Summary: BatchCompletedEvent HTTP API Test Suite

## What Was Built

4 passing HTTP API tests covering BatchCompletedEvent validation errors (422) and the happy path (200). All tests use the `/event` endpoint with `httpx.AsyncClient`.

## Key Files Created

- `testing/pytest/tests/batch/__init__.py` — package marker
- `testing/pytest/tests/batch/test_batch_completed_api.py` — 4-test HTTP API suite

## Test Results

```
4 passed, 18 warnings
```

| Test | Requirement | Status |
|------|-------------|--------|
| test_step_check_active_returns_422 | BATCH-15 | PASS |
| test_quantity_mismatch_returns_422 | BATCH-16 | PASS |
| test_closed_job_returns_422 | BATCH-17 | PASS |
| test_happy_path_returns_200 | BATCH-21 | PASS |

## Design Notes

- BATCH-15 (step_check): sends `step_data` in payload alongside `step_check=True` job — this is the only branch that raises ValueError for step_check active (without step_data, no error fires)
- All tests use `_set_job_active(db, job_key, ws_key)` helper to set `active=True` and `last_work_session_started` — required for WorkSessionClosedEvent child dispatch
- Per D-04: only HTTP response shape asserted, no DB state queries

## Self-Check: PASSED

All 4 tests pass. API response shape contracts are verified.
