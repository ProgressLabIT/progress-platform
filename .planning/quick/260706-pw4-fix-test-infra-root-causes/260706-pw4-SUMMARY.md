---
phase: quick-260706-pw4
plan: 01
subsystem: testing
tags: [pytest, bcrypt, passlib, schemathesis, arangodb, test-infra]
requires: []
provides:
  - "Green-by-default pytest run: integration-marked tests deselected unless -m integration"
  - "bcrypt 4.3.0 + passlib 1.7.2 in test venv, matching backend/api/requirements.txt"
  - "ErrorLog collection in PROGRESS_TEST schema init"
  - "Production payload helpers aligned to create_production_graph contract"
  - "Schemathesis fuzz bounded at ~1,650 cases"
affects: [testing/pytest]
tech-stack:
  added: []
  patterns:
    - "addopts marker exclusion with CLI override (last -m wins)"
    - "@settings between @schema.parametrize() and test fn (schemathesis 4.x)"
key-files:
  created: []
  modified:
    - testing/pytest/pyproject.toml
    - testing/pytest/uv.lock
    - testing/pytest/conftest.py
    - testing/pytest/conftest_helpers/schema.py
    - testing/pytest/tests/production/test_job_lifecycle.py
    - testing/pytest/tests/production/test_batch_state.py
    - testing/pytest/tests/api/test_schemathesis.py
decisions:
  - "Fixed create_user static hash by recomputing with the same embedded salt (minimal diff) rather than generating a fresh salt"
  - "Left schema.py cadmin default-record hash untouched — it mirrors the production seed record and no test authenticates as cadmin"
  - "Did not touch backend code for the 3 surfaced behavioral failures — out of test-infra scope, reported below"
metrics:
  duration: "~15 min"
  completed: "2026-07-06"
  tasks: 3
  commits: 5
---

# Quick Task 260706-pw4: Fix Test-Infra Root Causes Summary

Pinned bcrypt 4.3.*/passlib 1.7.2 to backend versions, default-excluded integration tests, added ErrorLog to test schema, fixed product_key fixture drift, and capped schemathesis fuzz at 10 examples — plus one deviation: the create_user fixture's static bcrypt hash never matched 'test'.

## Commits

| Hash | Scope |
|------|-------|
| b33c7054 | pyproject.toml + uv.lock: bcrypt/passlib pins + `addopts = "-m 'not integration'"` |
| b7a21808 | conftest.py: corrected static bcrypt hash for 'test' (deviation, see below) |
| 387f3a3d | schema.py: `Collection(name='ErrorLog')` in test schema init |
| bb0c4101 | test_job_lifecycle.py + test_batch_state.py: `g["product"]["product_key"]` |
| ec3c1d4e | test_schemathesis.py: `@settings(max_examples=10, deadline=None)` |

## Verification Results

- `bcrypt.__version__` 4.3.0, `passlib.__version__` 1.7.2 after `uv sync`
- Default collection: 212/226 collected, **14 deselected** (all `tests/integration/sparkplug_*` — the report said 10; 4 more were marked since). `-m integration` on the CLI selects the 14.
- Auth: **11/12 pass** (was 4/12). test_11 fails on pre-existing backend behavior (below).
- Production: **12/14 pass**. The 2 failures are backend behavior, not fixture drift (below).
- Schemathesis: collects cleanly, 1 parametrized test, settings applied.
- Combined `tests/api/test_auth.py tests/production/`: 37 passed, 3 failed in ~9s.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] create_user static bcrypt hash never matched 'test'**
- **Found during:** Task 1 verification — after the pin, auth returned 401 instead of the expected 200.
- **Issue:** The fixture's static `psw_hash` (`...Iq2GRNyGeUxBRjLJSAVaKSrv2VMQHIS`) does not verify against 'test': recomputing `bcrypt.hashpw(b'test', <embedded salt>)` yields checksum `IBT9lwNPQQcv/tCK/1Wpw.8fe0YTtLi`. Under bcrypt 5 every auth call 500'd at the backend self-test before verification ran, masking this. The plan's expectation "bcrypt pin alone fixes auth" was one layer short.
- **Fix:** Replaced the hash with the recomputed value (same salt); verified round-trip via passlib CryptContext. This is NOT an alternative version pin — the pins landed exactly as planned.
- **Files modified:** testing/pytest/conftest.py (line 330)
- **Commit:** b7a21808

## What Surfaced After the ErrorLog Fix (reported, not chased)

Working 5xx error logging now exposes real errors instead of `DocumentInsertError ... collection or view not found: ErrorLog` noise:

**1. tests/collaboration/test_issues.py — 8/9 fail with a REAL underlying error**
`backend/api/events/collaboration/issue_updated.py:16` — `self.tx.collection('Issue').update(self.info.issue_data)` raises `arango.exceptions.DocumentUpdateError: [HTTP 400][ERR 1227] invalid document type`. The `issue_data` passed to the transaction update is not a valid Arango document (likely missing `_key`/wrong shape). All issue-lifecycle events past create (update/critical/close/reopen/delete) hit this. test_01 (create) passes.

**2. tests/production — 2 residual failures, both backend behavior:**
- `test_job_started_already_active_returns_422`: duplicate JOB_STARTED returns **500** instead of 422. Root cause: the 422 exception-mapping tuple in `backend/api/endpoints/traceability.py:99-112` includes `JobIsActiveError` but NOT `JobIsStartedError` (raised at `events/production/job_started.py:29`), so it falls through to the generic 500 handler.
- `test_active_batch_changed_inactive_job_returns_422`: ACTIVE_BATCH_CHANGED on an inactive job (`job.active == false`) succeeds with **200** — the event's `apply()` has no inactive-job guard.

**3. tests/api/test_auth.py::test_11_first_token_revoked_on_re_auth**: after a second auth, whoami with the first token returns **200** instead of 401 — first token not actually revoked on re-auth. Pre-existing backend behavior surfaced once auth stopped 500ing.

All three touch backend production code (`traceability.py` overlaps the in-flight serial work) — out of scope for this test-infra task per plan output ("touching only test-infra files").

## Known Stubs

None.

## Threat Flags

None — test-infra only; no new endpoints, auth paths, or trust-boundary changes. Dependency change is a pin-down to production versions (T-q260706pw4-SC accepted per plan).

## Self-Check: PASSED

---

## Follow-up (2026-07-08): fuzz exclusion — commit 3446cb7e

The Fix 5 cap (`max_examples=10`) was insufficient. The 2026-07-07 full run
still took **7h10m**: ~165 operations each fire the ASGI lifespan per case,
and hypothesis shrinking ran on ~90 failing operations. Worse, fuzzed
requests mutate skip-truncate collections (Counter, Config), poisoning
subsequent tests in the same session (`test_counter_default_exists` failed
in-suite, passes in isolation).

**Fix:** `pytestmark = pytest.mark.fuzz` on test_schemathesis.py;
`addopts = "-m 'not integration and not fuzz'"`. Opt-in via `pytest -m fuzz`.

**Final default-suite baseline: 190 passed / 21 failed in 25s** (was 46
failed / 175 passed, with fuzzing pushing the wall clock past an hour).

Remaining 21 failures (all root-caused, none test-infra):
- 1 auth: `test_11_first_token_revoked_on_re_auth` — backend doesn't revoke
  first token on re-auth (pre-existing behavior)
- 11 collaboration: real bug unmasked by ErrorLog fix —
  `DocumentUpdateError [ERR 1227] invalid document type` from
  `events/collaboration/issue_updated.py:16`; messages 422 payload-shape drift
- 2 production: `JobIsStartedError` missing from 422-mapping in
  `endpoints/traceability.py`; ACTIVE_BATCH_CHANGED accepts inactive jobs
- 6 serial: test/code drift (overlaps in-flight serial workstream)
- 1 flaky: `test_queue_reordered_when_job_reopened` (passes in isolation)

The ~90 fuzz-found endpoint failures (5xx on fuzzed input) are logged in
/tmp/new-baseline.log — a separate hardening backlog, visible via `-m fuzz`.
