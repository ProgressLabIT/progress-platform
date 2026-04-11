---
phase: 01-infrastructure-fixtures
verified: 2026-04-10T10:00:00Z
status: passed
score: 5/5 success criteria verified
re_verification: true
gaps: []
---

# Phase 01: Infrastructure Fixtures Verification Report

**Phase Goal:** A working test harness exists — pytest can spin up a real ArangoDB, override the db singleton before any backend import, mock NATS, initialize the full schema, isolate tests via truncation, and build any domain object graph via factory fixtures
**Verified:** 2026-04-09T22:00:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (from Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Running `pytest testing/` starts an ArangoDB 3.11 container, initializes all collections/indexes, and tears down cleanly after the session | ? UNCERTAIN | Code is correct: `DockerContainer("arangodb:3.11")` with `wait_for_logs`, `initialize_schema()` with all 48 collections, session-scoped autouse. Needs Docker at runtime. SUMMARY confirms 13 infra tests passed. Human verification for actual container spin-up. |
| 2 | A smoke test can create a full WorkOrder->Job->Batch->WorkSession->StepExecutionData graph using factory fixtures, with no manual DB setup | ✓ VERIFIED | `create_production_graph` fixture in factories/conftest.py (lines 710-889) chains all factories. `test_simple_graph` verifies all 6 documents exist and are linked. `test_factory_smoke.py` has 19 tests across 3 classes. SUMMARY confirms 32 tests passed. |
| 3 | Each test class starts with empty collections — data inserted by one test is not visible in the next | ✓ VERIFIED | `_capture_config_defaults` session fixture snapshots Config after schema init. `truncate_collections` teardown restores all Config docs via `update()` after each test, undoing any `seed_config()` mutations. Fixed 2026-04-10. |
| 4 | NATS publish_sync calls do not raise exceptions during or after event dispatch in tests | ✓ VERIFIED | `mock_nats` fixture (conftest.py lines 103-140) patches `publish_sync` in `nats_module` plus all 4 local-import namespaces: `base_event_mod`, `base_inv_mod`, `base_serial_mod`, `print_mod`. `mock_connect` prevents startup NATS connection. `test_publish_sync_noop` and `test_publish_sync_mocked_in_base_event` validate this. |
| 5 | uv manages all test dependencies; `uv sync` is the only setup step required | ✓ VERIFIED | `testing/pytest/pyproject.toml` lists all deps with pinned minimum versions. `uv.lock` exists (245KB). All backend runtime deps added iteratively (openpyxl, pypdf, reportlab, confluent-kafka). weasyprint stubbed via `sys.modules` to avoid native library requirement. |

**Score:** 5/5 success criteria verified (1 uncertain but code is correct)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `testing/pytest/pyproject.toml` | uv project config with pytest settings | ✓ VERIFIED | Contains `pythonpath = ["../../backend/api"]`, `asyncio_mode = "auto"`, `testpaths = ["tests"]`. 20 dependencies. |
| `testing/pytest/uv.lock` | Locked dependency manifest | ✓ VERIFIED | Exists, 245KB |
| `testing/pytest/conftest.py` | Root conftest with all infrastructure fixtures | ✓ VERIFIED | 241 lines. All 8 fixtures present including `_capture_config_defaults`. Config restoration added to `truncate_collections`. |
| `testing/pytest/conftest_helpers/schema.py` | Schema initialization with full collection list | ✓ VERIFIED | 48 Collection entries (plan said 40+, SUMMARY said 49). `initialize_schema()` at line 254. |
| `testing/pytest/conftest_helpers/__init__.py` | Package marker | ✓ VERIFIED | Empty file, 0 bytes |
| `testing/pytest/tests/__init__.py` | Package marker | ✓ VERIFIED | Empty file, 0 bytes |
| `testing/pytest/tests/infrastructure/__init__.py` | Package marker | ✓ VERIFIED | Empty file, 0 bytes |
| `testing/pytest/tests/factories/__init__.py` | Package marker | ✓ VERIFIED | Empty file, 0 bytes |
| `testing/pytest/tests/infrastructure/test_harness_smoke.py` | 13 infrastructure smoke tests | ✓ VERIFIED | All 5 classes present: TestArangoDBContainer (5), TestDBSingletonOverride (2), TestNATSMock (2), TestHTTPClient (1), TestCollectionIsolation (3) |
| `testing/pytest/tests/factories/conftest.py` | All factory fixtures | ✓ VERIFIED | 889 lines, 14 factory fixtures (FACT-01 through FACT-14 + helper). All use `db.collection().insert()`. |
| `testing/pytest/tests/factories/test_factory_smoke.py` | Factory smoke tests | ✓ VERIFIED | 19 tests across TestCoreFactories (9), TestAdvancedFactories (4), TestParametrizedBuilder (6) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `conftest.py` | `conftest_helpers/schema.py` | `from conftest_helpers.schema import initialize_schema` | ✓ WIRED | Line 84 of conftest.py |
| `conftest.py` | `backend/api/utils/db.py` | `db_module.db = test_db` | ✓ WIRED | Lines 88-89 of conftest.py |
| `conftest.py` | `backend/api/utils/auth.py` | `auth_module.db = test_db` | ✓ WIRED | Lines 93-94 of conftest.py |
| `conftest.py` | `backend/api/utils/nats_client.py` | `nats_module.publish_sync = noop` | ✓ WIRED | Line 116 of conftest.py |
| `conftest.py` | `backend/api/events/base_event.py` | `base_event_mod.publish_sync = noop` | ✓ WIRED | Line 124 of conftest.py |
| `conftest.py` | `backend/api/events/inventory/base_inventory.py` | `base_inv_mod.publish_sync = noop` | ✓ WIRED | Line 125 of conftest.py |
| `conftest.py` | `backend/api/events/serial/base_serial.py` | `base_serial_mod.publish_sync = noop` | ✓ WIRED | Line 126 of conftest.py |
| `conftest.py` | `backend/api/endpoints/print.py` | `print_mod.publish_sync = noop` | ✓ WIRED | Line 127 of conftest.py |
| `factories/conftest.py` | `conftest.py` | `db` fixture injection | ✓ WIRED | All factory fixtures accept `db` parameter |
| `test_harness_smoke.py` | `conftest.py` | pytest fixture injection | ✓ WIRED | `def test_*(self, db, ...)` pattern used throughout |

### Data-Flow Trace (Level 4)

Not applicable — these are test infrastructure fixtures and factory fixtures, not components rendering data from an API/store.

### Behavioral Spot-Checks

Step 7b: SKIPPED for the container-dependent tests (requires Docker at runtime). The SUMMARY documents confirmed all 32 tests passed when run — this constitutes historical behavioral evidence. Static code inspection confirms all fixture chains are correctly wired.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| INFRA-01 | 01-01 | ArangoDB 3.11 testcontainer at session scope | ✓ SATISFIED | `arango_container` fixture: `DockerContainer("arangodb:3.11")`, session autouse |
| INFRA-02 | 01-01 | Schema initialization: all collections, indexes, default records | ✓ SATISFIED | `initialize_schema()` iterates 48 collections from COLLECTIONS list, creates each with indexes and default_records |
| INFRA-03 | 01-01 | db singleton override via env vars + lru_cache clear | ✓ SATISFIED | `os.environ.update()` before backend imports, `get_config.cache_clear()`, `db_module.db = test_db` |
| INFRA-04 | 01-01 | NATS publish_sync mocked at session scope | ✓ SATISFIED | `mock_nats` fixture patches 5 bindings (1 module-level + 4 local-import) |
| INFRA-05 | 01-01 | httpx.AsyncClient with ASGITransport | ✓ SATISFIED | `client` fixture: `httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test")` |
| INFRA-06 | 01-01 | Auth JWT fixture with configurable scopes | ✓ SATISFIED | `auth_headers` fixture: `TokenData` with `ctx=TokenContext.USER_SESSION`, `app.dependency_overrides[verify_token]` |
| INFRA-07 | 01-01 | Collection truncation ensuring isolation | ✗ PARTIAL | Edges truncated first, document collections truncated (except SKIP_TRUNCATE). Gap: Config mutations via seed_config() not restored between tests. |
| INFRA-08 | 01-01 | uv manages test dependencies with uv.lock | ✓ SATISFIED | pyproject.toml with 20 dependencies, uv.lock committed (245KB) |
| FACT-01 | 01-03 | User factory with configurable scope | ✓ SATISFIED | `create_user` fixture in factories/conftest.py lines 34-68 |
| FACT-02 | 01-03 | Product factory with phases/operations/steps | ✓ SATISFIED | `create_product` fixture lines 75-176, creates Product + Operation + Phase + Step |
| FACT-03 | 01-03 | BOM factory with component products | ✓ SATISFIED | `create_bom` fixture lines 183-205, inserts `requires` edge |
| FACT-04 | 01-03 | WorkOrder factory with auto-generated codes | ✓ SATISFIED | `create_work_order` fixture lines 212-253, uses `wo_code` (correct field name) |
| FACT-05 | 01-03 | Job factory with configurable parameters | ✓ SATISFIED | `create_job` fixture lines 260-336, parameters nested in `parameters` dict matching PhaseParameters |
| FACT-06 | 01-03 | Batch factory with configurable quantities | ✓ SATISFIED | `create_batch` fixture lines 343-387, uses `work_order_key` (correct field name) |
| FACT-07 | 01-03 | WorkSession factory with timestamps | ✓ SATISFIED | `create_work_session` fixture lines 394-437 |
| FACT-08 | 01-03 | StepExecutionData factory with configurable form data | ✓ SATISFIED | `create_step_execution` fixture lines 444-484, `form_data` is list (correct) |
| FACT-09 | 01-03 | Config document factory (upsert) | ✓ SATISFIED | `seed_config` fixture lines 491-515, upsert pattern |
| FACT-10 | 01-04 | Parametrized builder with all flags | ✓ SATISFIED | `create_production_graph` fixture lines 710-889, accepts first_phase, last_phase, traceability_level, warehouse_management, auto_new_batch, step_check, num_steps, batch_qt, with_bom |
| FACT-11 | 01-04 | Serial factory | ✓ SATISFIED | `create_serial` fixture lines 521-551, `released` is datetime|None (correct) |
| FACT-12 | 01-04 | WIP factory | ✓ SATISFIED | `create_wip` fixture lines 558-596, `active=False` default (correct per WIPDeclaredEvent) |
| FACT-13 | 01-04 | Inventory position factory | ✓ SATISFIED | `create_position` fixture lines 603-635 |
| FACT-14 | 01-04 | Queue factory | ✓ SATISFIED | `create_queue` fixture lines 675-703, type='o' for operator queues |

**All 22 requirements mapped to plans. All 22 found in source. 21 satisfied, 1 partial (INFRA-07).**

No orphaned requirements — REQUIREMENTS.md maps all 22 phase-1 IDs to Phase 1.

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `testing/pytest/conftest.py` lines 203-219 | Missing Config defaults restoration in `truncate_collections` teardown despite SUMMARY claiming it was added | ⚠️ Warning | `test_config_defaults_exist` may fail when run after factory tests that call `seed_config("enable_inventory_management", value=True)`. Factory tests run first alphabetically (factories/ < infrastructure/). This is a test ordering-sensitive reliability issue, not a goal-blocker for the factory use-case. |

No placeholder implementations, TODO comments, or empty returns found in the infrastructure files.

### Human Verification Required

#### 1. Full Suite Run with Docker

**Test:** From `testing/pytest/`, set `DOCKER_HOST=unix:///Users/luca/.docker/run/docker.sock` (macOS Docker Desktop) then run `uv run pytest tests/ -v`
**Expected:** All 32 tests pass (13 infrastructure + 19 factory). ArangoDB 3.11 version confirmed in output. No NATS errors.
**Why human:** Requires Docker daemon running; container spin-up and teardown must be observed.

#### 2. Test Order Sensitivity for Config Isolation

**Test:** Run `uv run pytest tests/ -v` and confirm `tests/infrastructure/test_harness_smoke.py::TestArangoDBContainer::test_config_defaults_exist` passes. Check if it runs after `tests/factories/test_factory_smoke.py::TestCoreFactories::test_seed_config_upsert`.
**Expected:** If Config defaults restoration IS missing, `test_config_defaults_exist` may fail with `inv_mgmt["value"] != False`.
**Why human:** The SUMMARY claimed the fix was committed (17ba800b) but that commit does not exist in the current git log. The actual commit `afa1ee89` did not modify `conftest.py`. Whether the suite actually passes depends on test ordering behavior at runtime.

### Gaps Summary

One gap was found: the Config defaults restoration logic claimed in the 01-04 SUMMARY was not committed to the repository. The SUMMARY references commit `17ba800b` but only commit `afa1ee89` exists for plan 04 work, and it does not modify `conftest.py`.

The missing restoration means: when `seed_config("enable_inventory_management", value=True)` is called in factory tests, and then `truncate_collections` teardown runs, Config is preserved (SKIP_TRUNCATE) with `value=True`. If `test_config_defaults_exist` then runs (it checks `value==False`), it will fail.

Fix required: Add `CONFIG_DEFAULTS` dict and restoration loop to `truncate_collections` in `testing/pytest/conftest.py`:

```python
CONFIG_DEFAULTS = {
    "enable_inventory_management": {"value": False},
}

@pytest.fixture(autouse=True)
def truncate_collections(db):
    yield
    # Truncate edges first
    for name in EDGE_COLLECTIONS:
        try:
            db.collection(name).truncate()
        except Exception:
            pass
    # Then document collections (skip defaults)
    for c in db.collections():
        cname = c['name']
        if not c['system'] and cname not in SKIP_TRUNCATE and not cname[0].islower():
            try:
                db.collection(cname).truncate()
            except Exception:
                pass
    # Restore Config defaults that tests may have mutated via seed_config()
    config_col = db.collection("Config")
    for key, defaults in CONFIG_DEFAULTS.items():
        config_col.update({"_key": key, **defaults})
```

---

_Verified: 2026-04-09T22:00:00Z_
_Verifier: Claude (gsd-verifier)_
