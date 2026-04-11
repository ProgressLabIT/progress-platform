---
phase: 02
phase_name: critical-event-tests
status: clean
depth: standard
files_reviewed: 7
reviewed_at: 2026-04-10T16:35:29Z
findings:
  critical: 0
  warning: 0
  info: 4
  total: 4
---

# Code Review: Phase 02 — critical-event-tests

## Scope

Files reviewed from phase 02 commits:

- `testing/pytest/tests/helpers.py`
- `testing/pytest/tests/conftest.py`
- `testing/pytest/tests/factories/conftest.py` (modified — wo_bom fix)
- `testing/pytest/tests/step/__init__.py`
- `testing/pytest/tests/step/test_step_completed.py`
- `testing/pytest/tests/batch/__init__.py`
- `testing/pytest/tests/batch/test_batch_completed_api.py`

## Findings

### INFO-01: Inconsistent form_data in HTTP error test

**File:** `tests/step/test_step_completed.py:312`
**Finding:** `test_http_missing_batch_returns_422` omits `form_data` from the HTTP payload. The success path (`test_http_endpoint_success`) includes `form_data: []`. The error fires before form_data validation so this doesn't affect correctness, but it creates a minor inconsistency.
**Recommendation:** Add `"form_data": []` to the 422 test payload for parity. Not blocking.

### INFO-02: CustomField hardcoded _key with unnecessary has() guard

**File:** `tests/step/test_step_completed.py:122-130`
**Finding:** `cf-weight-test` is a hardcoded `_key` with an `if not has()` guard. `CustomField` is not in `SKIP_TRUNCATE` so it is truncated after each test — the guard is always true at test start. Harmless but could mislead future readers.
**Recommendation:** Remove the `if not has()` guard and always insert. Or add a comment explaining the guard is defensive.

### INFO-03: Typo in step_check message assertion

**File:** `tests/batch/test_batch_completed_api.py:68`
**Finding:** `"stepcompletedEvent"` is wrong camelCase and would never match the actual error message from `batch_completed.py` ("Step check is active for the job. Use `StepCompletedEvent` to store step data."). The assertion succeeds because `"step" in message.lower()` catches it first.
**Recommendation:** Remove the dead `"stepcompletedEvent"` branch, or fix to `"StepCompletedEvent"`.

### INFO-04: Factory wo_bom fix is correct but not documented in factory docstring

**File:** `tests/factories/conftest.py`
**Finding:** `wo_bom: []` was added silently without updating the FACT-04 docstring. Future readers won't know why it's there.
**Recommendation:** Add a comment: `"wo_bom": [],  # required by GET_WORKING_JOB_DATA AQL: FOR bom_line IN DOCUMENT(WorkOrder, j.wo_key).wo_bom — null crashes with ERR 1563`

## Summary

No critical or warning issues. All 4 findings are informational. The test suite is well-structured, follows the design principles (D-01 through D-16), and the factory fix is correct and necessary. Tests are readable and the deviation decisions (form_field_key, temp SXD cleanup) are well-documented in test comments.
