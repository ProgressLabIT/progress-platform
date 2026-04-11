---
phase: 01-infrastructure-fixtures
plan: "02"
subsystem: testing/pytest
tags: [infrastructure, smoke-tests, pytest, arangodb, testcontainers]
depends_on: ["01-01"]
provides: ["01-03", "01-04"]

dependency_graph:
  requires:
    - "01-01: conftest.py fixtures, conftest_helpers/schema.py"
  provides:
    - "Verified working test harness that 01-03 and 01-04 can build on"
  affects:
    - "testing/pytest/conftest.py (weasyprint stub, import order)"
    - "testing/pytest/conftest_helpers/schema.py (python-arango 8.x API fix)"
    - "testing/pytest/pyproject.toml (backend runtime deps)"

tech_stack:
  added:
    - "openpyxl>=3 — required by events/inventory/count_imported.py"
    - "pypdf>=4 — required by endpoints/serial.py"
    - "reportlab>=4 — required by backend PDF generation utilities"
    - "confluent-kafka — required by backend Kafka producer/consumer"
  patterns:
    - "sys.modules stub for native-library-dependent packages (weasyprint)"
    - "BDD-style docstrings: Given/when/then in test methods"
    - "Test class grouping by infrastructure concern"

key_files:
  created:
    - "testing/pytest/tests/infrastructure/test_harness_smoke.py"
  modified:
    - "testing/pytest/conftest_helpers/schema.py (bug fix: _conn._url → _conn._hosts[0])"
    - "testing/pytest/conftest.py (weasyprint stub added before backend imports)"
    - "testing/pytest/pyproject.toml (added 4 backend runtime deps)"
    - "testing/pytest/uv.lock (updated after dep changes)"

decisions:
  - "weasyprint is stubbed via sys.modules (not installed) — GTK/pango not available on macOS dev; tests never exercise PDF rendering"
  - "DOCKER_HOST env var required on macOS Docker Desktop (socket at ~/.docker/run/docker.sock, not /var/run/docker.sock)"

metrics:
  duration: "~35 minutes"
  completed: "2026-04-09"
  tasks_completed: 1
  tasks_total: 1
  files_created: 1
  files_modified: 4
---

# Phase 01 Plan 02: Infrastructure Smoke Tests Summary

Infrastructure smoke tests that validate all fixtures from Plan 01 work correctly: ArangoDB testcontainer with schema init, db singleton override in utils.db and utils.auth, NATS publish_sync mock, httpx ASGI client reaching /hello, and collection truncation preserving Config/Counter/Queue defaults.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create infrastructure smoke tests | 0430d3e4 | tests/infrastructure/test_harness_smoke.py, conftest.py, schema.py, pyproject.toml, uv.lock |

## Verification

All 13 smoke tests pass:

```
tests/infrastructure/test_harness_smoke.py::TestArangoDBContainer::test_container_reachable PASSED
tests/infrastructure/test_harness_smoke.py::TestArangoDBContainer::test_all_collections_exist PASSED
tests/infrastructure/test_harness_smoke.py::TestArangoDBContainer::test_config_defaults_exist PASSED
tests/infrastructure/test_harness_smoke.py::TestArangoDBContainer::test_counter_default_exists PASSED
tests/infrastructure/test_harness_smoke.py::TestArangoDBContainer::test_queue_default_exists PASSED
tests/infrastructure/test_harness_smoke.py::TestDBSingletonOverride::test_db_module_points_to_testcontainer PASSED
tests/infrastructure/test_harness_smoke.py::TestDBSingletonOverride::test_auth_module_db_overridden PASSED
tests/infrastructure/test_harness_smoke.py::TestNATSMock::test_publish_sync_noop PASSED
tests/infrastructure/test_harness_smoke.py::TestNATSMock::test_publish_sync_mocked_in_base_event PASSED
tests/infrastructure/test_harness_smoke.py::TestHTTPClient::test_hello_endpoint PASSED
tests/infrastructure/test_harness_smoke.py::TestCollectionIsolation::test_insert_then_truncation PASSED
tests/infrastructure/test_harness_smoke.py::TestCollectionIsolation::test_previous_data_gone PASSED
tests/infrastructure/test_harness_smoke.py::TestCollectionIsolation::test_config_survives_truncation PASSED
13 passed, 6 warnings in 4.67s
```

ArangoDB 3.11 confirmed reachable. Collection truncation preserves Config/Counter/Queue defaults while clearing User and other test data.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed python-arango 8.x BasicConnection API mismatch in schema.py**
- **Found during:** Task 1 — first test run
- **Issue:** `conftest_helpers/schema.py:274` used `sys_db._conn._url` which doesn't exist on `BasicConnection` in python-arango 8.x. The attribute is `_hosts` (a list).
- **Fix:** Changed `sys_db._conn._url` to `sys_db._conn._hosts[0]`
- **Files modified:** `testing/pytest/conftest_helpers/schema.py`
- **Commit:** 0430d3e4

**2. [Rule 2 - Missing] Added weasyprint stub to prevent macOS native library errors**
- **Found during:** Task 1 — second test run (after openpyxl was added)
- **Issue:** `endpoints/serial.py` → `utils/dhr.py` → `weasyprint` imports fail on macOS without GTK/pango system libraries (`libgobject-2.0-0`). Backend imports triggered by the `mock_nats` fixture crash before any test runs.
- **Fix:** Added `sys.modules.setdefault("weasyprint", ...)` stub at the top of `conftest.py` before any backend imports. Also removed `weasyprint` from `pyproject.toml` dependencies.
- **Files modified:** `testing/pytest/conftest.py`, `testing/pytest/pyproject.toml`
- **Commit:** 0430d3e4

**3. [Rule 3 - Blocking] Added missing backend runtime dependencies to pyproject.toml**
- **Found during:** Task 1 — iterative test runs as each missing module was encountered
- **Issue:** Backend modules imported during test setup required `openpyxl`, `pypdf`, `reportlab`, and `confluent-kafka` which were not in pyproject.toml.
- **Fix:** Added all four packages to `pyproject.toml` dependencies and ran `uv sync`.
- **Files modified:** `testing/pytest/pyproject.toml`, `testing/pytest/uv.lock`
- **Commit:** 0430d3e4

**4. [Rule 3 - Blocking] Docker socket path on macOS Docker Desktop**
- **Found during:** Task 1 — initial test run
- **Issue:** Docker Desktop on macOS uses `~/.docker/run/docker.sock` instead of `/var/run/docker.sock`. Tests must be run with `DOCKER_HOST=unix:///Users/luca/.docker/run/docker.sock`.
- **Fix:** Tests run correctly with the env var set. This is a developer environment note, not a code change. Not fixed in code — the `TESTCONTAINERS_DOCKER_SOCKET_OVERRIDE` or `DOCKER_HOST` env var must be set on this machine.
- **Note:** In CI/Linux environments the default `/var/run/docker.sock` works; no change needed there.

## Known Stubs

None — all tests exercise real infrastructure (real ArangoDB container, real ASGI app, real collections). The weasyprint stub is a test-environment adaptation, not a stub that affects test correctness.

## Self-Check: PASSED

- `testing/pytest/tests/infrastructure/test_harness_smoke.py` — FOUND
- `testing/pytest/conftest_helpers/schema.py` — FOUND (modified)
- `testing/pytest/conftest.py` — FOUND (modified)
- `testing/pytest/pyproject.toml` — FOUND (modified)
- Commit `0430d3e4` — FOUND
