---
phase: 01-infrastructure-fixtures
status: issues_found
depth: standard
files_reviewed: 6
findings:
  critical: 1
  warning: 6
  info: 4
  total: 11
---

# Phase 01 Code Review — Infrastructure + Fixtures

## Summary

The infrastructure is well-structured and the design decisions (autouse session fixtures, singleton patching, schema-driven collection init) are sound. The isolation strategy (truncate-after-yield, SKIP_TRUNCATE) is correct and clearly reasoned. The factory system is comprehensive and the parametrized `create_production_graph` builder is a genuine force-multiplier for future test authoring.

Issues found are a mix of one silent correctness bug (multi-field index definitions), incomplete NATS mock coverage, and several lower-severity items including a deprecated API, a duplicate dependency, and a Python version mismatch between the requirement and the venv.

---

## Critical

### CR-001: Multi-field index definitions use string concatenation instead of a list (silent bug)

**File:** `testing/pytest/conftest_helpers/schema.py` — lines 22–23, 137, 205, 233, 248

**Issue:** Multiple `DBIndex` definitions pass multi-field indexes as a single comma-separated string inside a one-element list rather than as a multi-element list. For example:

```python
DBIndex(fields=['job_key, canceled'], name='batch-job-canceled')
```

`python-arango`'s `add_index()` receives `{"fields": ["job_key, canceled"]}`. ArangoDB treats this as a single field whose name is the literal string `"job_key, canceled"` — it does not split on commas. The compound index is **never created**; ArangoDB silently creates a single-field index on a non-existent field name instead.

Affected index definitions (non-exhaustive):
- `batch-job-canceled` — `['job_key, canceled']`
- `batch-wo-phase-canceled` — `['work_order_key, phase_key, canceled']`
- `job-target` — `['wo_key, phase_key, assigned_to, stage']`
- `sxd-batch-step-status-canceled` — `['batch_key, step_key, status, canceled']`
- `wip-target` — `['_to, wo_key, active, serial_key']`
- `ws-job-canceled` — `['job_key, canceled']`
- `ws-batch-canceled` — `['batch_key, canceled']`
- `phase-product-operation` — `['product_key, operation_key']`

**Fix:** Each field must be a separate list element:

```python
DBIndex(fields=['job_key', 'canceled'], name='batch-job-canceled')
DBIndex(fields=['work_order_key', 'phase_key', 'canceled'], name='batch-wo-phase-canceled')
DBIndex(fields=['wo_key', 'phase_key', 'assigned_to', 'stage'], name='job-target')
# etc.
```

This does not cause test failures today because the smoke tests do not assert on index existence or query plans, but it means compound indexes are absent from the test database, so any test that relies on index-covered queries will use collection scans and may not catch index regression bugs in production queries.

---

## Warnings

### CR-002: Incomplete NATS mock — `nats_request` and `get_nats`/`get_loop` not patched

**File:** `testing/pytest/conftest.py` — lines 103–135

**Issue:** The `mock_nats` fixture patches `publish_sync` across the four known local-binding sites and replaces `connect`/`drain` on the module. However two other NATS callsites are not covered:

1. `endpoints/print.py` line 13: `from utils.nats_client import request as nats_request` — used at line 213 in an async `await nats_request(...)` path. Any test that exercises the print endpoint's NATS code path will raise an unconnected-client error.
2. `events/production/commons/serial.py` lines 11, 24–26: `get_nats().publish(...)` — `get_nats()` returns the raw NATS client object. If this code path is exercised it will call `.publish()` on `None` (or the unconnected client), raising an `AttributeError` or a NATS error.

**Fix:** Add mock patches for both callsites in `mock_nats`:

```python
import endpoints.print as print_mod
async def mock_nats_request(subject, payload, timeout=5):
    return None
print_mod.nats_request = mock_nats_request

import events.production.commons.serial as serial_commons_mod
# Patch get_nats to return an object with a no-op publish
class _FakeNats:
    def publish(self, *a, **kw): return asyncio.coroutine(lambda: None)()
serial_commons_mod.get_nats = lambda: _FakeNats()
```

### CR-003: `datetime.utcnow()` is deprecated in Python 3.12+

**File:** `testing/pytest/conftest.py` — lines 175–176

**Issue:** `auth_headers` fixture uses `datetime.utcnow()` for `iat` and `exp` fields in `TokenData`. `datetime.utcnow()` was deprecated in Python 3.12 and emits `DeprecationWarning` at runtime. It produces a naive datetime; if `TokenData` or `PyJWT` validates timezone-awareness this will silently produce wrong offsets.

**Fix:** Use timezone-aware datetimes:

```python
from datetime import datetime, timedelta, timezone
token_data = TokenData(
    ...
    iat=datetime.now(timezone.utc),
    exp=datetime.now(timezone.utc) + timedelta(hours=1),
    ...
)
```

### CR-004: Session-scoped `client` fixture is `async` — may not work as expected with pytest-asyncio

**File:** `testing/pytest/conftest.py` — line 147–154

**Issue:** The `client` fixture is declared `scope="session"` and is `async`. `pytest-asyncio` with `asyncio_mode = "auto"` supports session-scoped async fixtures in some versions, but the behaviour is version-dependent and the event loop lifecycle for session-scoped fixtures has had multiple breaking changes between pytest-asyncio 0.21 and 0.24. Specifically, a session-scoped async fixture shares the event loop with all tests; if any test creates a sub-loop or uses `asyncio.run()` internally, the shared loop can be closed prematurely.

The version pin in `pyproject.toml` is `pytest-asyncio>=0.21` — this is a wide range that includes versions with incompatible session-loop semantics.

**Fix:** Pin `pytest-asyncio` to a specific minor version (e.g., `>=0.23,<0.25`) and add an explicit `asyncio_mode = "auto"` loop scope configuration if using pytest-asyncio 0.23+:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "session"
```

Also verify the `client` fixture works with the installed version via the existing `test_hello_endpoint` smoke test.

### CR-005: `initialize_schema` accesses a private internal attribute of `python-arango`

**File:** `testing/pytest/conftest_helpers/schema.py` — line 275

**Issue:**

```python
host_url = sys_db._conn._hosts[0]
```

`_conn` and `_hosts` are private implementation details of `python-arango`'s `BasicConnection` class. This will silently break if the library changes its internal structure between patch versions — the dependency is pinned only to `>=8` which is a wide range.

**Fix:** Pass the host URL explicitly to `initialize_schema` instead of extracting it from internals. The caller in `conftest.py` already has `url` available:

```python
# conftest.py
test_db = initialize_schema(sys_db, host_url=url)

# schema.py
def initialize_schema(sys_db, host_url: str) -> object:
    ...
    db = ArangoClient(hosts=host_url).db("PROGRESS_TEST", username="root", password="")
```

### CR-006: `auth_headers` fixture silently clears ALL dependency overrides on teardown

**File:** `testing/pytest/conftest.py` — lines 183–185

**Issue:**

```python
from main import app
app.dependency_overrides.clear()
```

If a test sets additional `dependency_overrides` beyond `verify_token` (e.g., for database injection or feature flags), the blanket `.clear()` in this fixture's teardown will remove them all, even overrides set by other fixtures with longer lifetimes. This is a hidden coupling that will cause hard-to-diagnose failures in future tests.

**Fix:** Only remove the specific override this fixture set:

```python
yield _make_headers
app.dependency_overrides.pop(verify_token, None)
```

### CR-007: `truncate_collections` skips edge collections not in `EDGE_COLLECTIONS` list

**File:** `testing/pytest/conftest.py` — lines 192–219

**Issue:** The `EDGE_COLLECTIONS` hard-coded list is the only path through which edge collections are truncated. The second pass (lines 214–218) skips lowercase-named collections (`not cname[0].islower()`), which is correct because they are edges — but this means any edge collection **not** in `EDGE_COLLECTIONS` is never truncated. Currently missing from the list: `event_source` (visible in schema.py line 250), and potentially any future edge collections added to schema.py.

Cross-checking schema.py: `event_source` is defined in COLLECTIONS but is absent from `EDGE_COLLECTIONS` in conftest.py.

**Fix:** Either derive `EDGE_COLLECTIONS` dynamically from the schema definition (single source of truth), or add `event_source` to the list and add a comment that it must be kept in sync with `schema.py`:

```python
EDGE_COLLECTIONS = [
    ...
    'event_source',  # parent-child event relationships
]
```

---

## Info

### CR-008: Duplicate `httpx` dependency in pyproject.toml

**File:** `testing/pytest/pyproject.toml` — lines 9 and 28

**Issue:** `"httpx>=0.28"` appears twice in the `dependencies` list. This is harmless (pip/uv deduplicates) but indicates a copy-paste error.

**Fix:** Remove the duplicate entry at line 28.

### CR-009: venv uses Python 3.13 but project specifies `>=3.11` and backend runs 3.11

**File:** `testing/pytest/pyproject.toml` — line 4; venv at `testing/pytest/.venv/lib/python3.13/`

**Issue:** The project `requires-python = ">=3.11"` and CLAUDE.md states Python 3.11 matches the backend container. The installed venv is Python 3.13. While 3.11-compatible code generally runs on 3.13, there are subtle differences (e.g., `datetime.utcnow()` deprecation warnings become louder, some `typing` behaviors differ). CI will likely run with a different Python version than the developer venv, potentially masking environment-specific failures.

**Fix:** Document the intended Python version explicitly (e.g., `requires-python = ">=3.11,<3.12"`) and align the venv to match the CI container Python version.

### CR-010: `create_production_graph` does not return inserted `step_executions` in a verified state

**File:** `testing/pytest/tests/factories/conftest.py` — lines 822–830

**Issue:** Step executions are created only for steps belonging to `target_phase`. The return dict includes `step_executions` but the `test_simple_graph` smoke test does not assert that these documents exist in the database (unlike `User`, `Product`, `WorkOrder`, `Job`, `Batch`, `WorkSession` which are all DB-verified). If `create_step_execution` has a schema mismatch it would not be caught by the smoke tests.

**Fix:** Add a DB existence assertion in `test_simple_graph`:

```python
for sxd in g["step_executions"]:
    assert db.collection("StepExecutionData").get(sxd["_key"]) is not None
```

### CR-011: `seed_config` fixture is not idempotency-safe if value key conflicts with `_key`

**File:** `testing/pytest/tests/factories/conftest.py` — lines 505–513

**Issue:** `_seed(key, **values)` builds `{"_key": key, **values}` for the update. If a caller accidentally passes `_key` as one of the `**values`, the dict will contain `_key` twice (Python dicts allow re-assignment, so the last `_key` wins — but the behavior is surprising and could corrupt the document key). This is low-risk in current usage but worth a guard.

**Fix:** Add an explicit check:

```python
def _seed(key: str, **values):
    if "_key" in values:
        raise ValueError("Do not pass '_key' as a value to seed_config; use the 'key' argument")
    ...
```
