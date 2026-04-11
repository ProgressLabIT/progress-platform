---
plan: 02-01
phase: 02-critical-event-tests
status: completed
started: 2026-04-10T16:29:47Z
completed: 2026-04-10T16:35:29Z
requirements: [STEP-01, STEP-02, STEP-03, STEP-04, STEP-05, STEP-06, STEP-07, STEP-08]
---

# Plan 02-01 Summary: StepCompletedEvent Dual-Layer Test Suite

## What Was Built

8 passing tests covering all STEP requirements across two layers: direct event instantiation (6 tests) and HTTP API (2 tests). Shared `assert_event_dispatched` helper for child event verification.

## Key Files Created

- `testing/pytest/tests/helpers.py` — shared `assert_event_dispatched(db, event_type, **filters)` helper
- `testing/pytest/tests/step/__init__.py` — package marker
- `testing/pytest/tests/step/test_step_completed.py` — 8-test suite
- `testing/pytest/tests/conftest.py` — pytest_plugins re-export for factory fixtures across subdirs

## Key Files Modified

- `testing/pytest/tests/factories/conftest.py` — added `wo_bom: []` to WorkOrder factory (required by GET_WORKING_JOB_DATA AQL query which does `FOR bom_line IN DOCUMENT(WorkOrder, wo_key).wo_bom` — null crashes with ERR 1563)

## Test Results

```
8 passed, 18 warnings
```

| Test | Requirement | Status |
|------|-------------|--------|
| test_happy_path_non_last_step | STEP-01 | PASS |
| test_last_step_triggers_batch_completed | STEP-02 | PASS |
| test_form_data_stored | STEP-03 | PASS |
| test_work_session_key_set | STEP-04 | PASS |
| test_temp_step_data_overwritten | STEP-05 | PASS |
| test_missing_batch_raises_value_error | STEP-06 | PASS |
| test_http_endpoint_success | STEP-07, STEP-08 | PASS |
| test_http_missing_batch_returns_422 | STEP-06 (HTTP) | PASS |

## Deviations

- `FormFieldValue.form_field_key` is the correct field name (plan spec said `field_key` — corrected)
- `_step_event_info` helper uses explicit `form_data` parameter (not `**extra`) to avoid keyword collision
- `test_temp_step_data_overwritten` clears factory-created SXD records before inserting the temp record (factory auto-creates SXDs for all steps; without clearing, there are 2 records and overwrite creates a 3rd)
- HTTP success test includes `form_data: []` in payload (StepExecutionData Pydantic model requires list, not None)

## Self-Check: PASSED

All 8 tests pass. Factory fix (wo_bom) is correct and necessary for production event compatibility.
