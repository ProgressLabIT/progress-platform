---
phase: 01-infrastructure-fixtures
plan: 04
subsystem: test-infrastructure
tags: [factories, smoke-tests, tdd, arangodb, pytest]
dependency_graph:
  requires: ["01-02", "01-03"]
  provides: ["complete-factory-set", "factory-smoke-tests"]
  affects: ["02-batch-completed-event"]
tech_stack:
  added: []
  patterns: ["parametrized-builder", "function-scope-factories", "config-default-restoration"]
key_files:
  created:
    - testing/pytest/tests/factories/test_factory_smoke.py
  modified:
    - testing/pytest/tests/factories/conftest.py
    - testing/pytest/conftest.py
decisions:
  - "Serial.released field is datetime|None per actual model, not bool — factory uses None for unreleased"
  - "WIP active=False for unbooked (available) WIP, matching WIPDeclaredEvent behavior"
  - "create_production_graph passes first_phase/last_phase flags to create_job so BatchCompletedEvent reads them correctly from Job document"
  - "Config default restoration added to truncate_collections teardown to prevent seed_config() leaking state between tests"
metrics:
  duration: ~45 minutes
  completed: 2026-04-09T21:16:15Z
  tasks_completed: 2
  files_changed: 3
requirements:
  - FACT-10
  - FACT-11
  - FACT-12
  - FACT-13
  - FACT-14
---

# Phase 01 Plan 04: Advanced Factory Fixtures and Smoke Tests Summary

Advanced factory fixtures (Serial, WIP, Position, Queue, InventoryAtPosition) and a parametrized production graph builder added to the factory fixture set. 19 smoke tests created and all passing — full combined suite (32 tests) green.

## What Was Built

**Task 1: Advanced factory fixtures** — appended to `testing/pytest/tests/factories/conftest.py`:

- `create_serial` (FACT-11): inserts Serial documents linked to products; `released` field is `datetime|None` matching actual model
- `create_wip` (FACT-12): inserts unbooked WIP edge records between phases with `active=False` matching `WIPDeclaredEvent`
- `create_position` (FACT-13): inserts Position documents for inventory location tests
- `create_inventory_at_position` (helper): inserts `is_in_position` edge records linking Position to Product with quantity
- `create_queue` (FACT-14): inserts operator Queue records (type='o') for job assignment tests
- `create_production_graph` (FACT-10): parametrized builder accepting flags `first_phase`, `last_phase`, `traceability_level`, `warehouse_management`, `auto_new_batch`, `step_check`, `num_steps`, `batch_qt`, `with_bom`; returns dict with all created objects

**Task 2: Factory smoke tests** — created `testing/pytest/tests/factories/test_factory_smoke.py`:

- `TestCoreFactories` (9 tests): individual fixture verification for all core factories
- `TestAdvancedFactories` (4 tests): Serial, WIP, Position, Queue factories
- `TestParametrizedBuilder` (6 tests): simple graph, non-first-phase WIP, traceability serials, warehouse config, BOM component, step_check flag

## Test Results

```
19 passed in factory smoke tests
32 passed total (infrastructure + factories combined)
```

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| `released` is `datetime\|None`, not `bool` | Actual `Serial` model uses `datetime\|None`; `None` = unreleased |
| `create_wip` defaults `active=False` | `WIPDeclaredEvent` creates WIP with `active=False`; active WIP has `_to=Job/...` not Phase |
| `create_production_graph` passes `first_phase`/`last_phase` to `create_job` | `BatchCompletedEvent.apply()` reads `self.job.first_phase` and `self.job.last_phase` to decide WIP actions |
| Config defaults restored in `truncate_collections` teardown | `seed_config()` changes Config but SKIP_TRUNCATE prevents full wipe; without restoration `test_config_defaults_exist` fails when run after factory tests |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed `released` field type in `create_serial`**
- **Found during:** Task 1 implementation
- **Issue:** Plan specified `released: bool = False` but `Serial` model uses `released: datetime | None`
- **Fix:** Changed to `released: "datetime | None" = None`
- **Files modified:** `testing/pytest/tests/factories/conftest.py`
- **Commit:** 0fea3d19

**2. [Rule 1 - Bug] Fixed `create_wip` default `active` value**
- **Found during:** Task 1 implementation via `WIPDeclaredEvent` source inspection
- **Issue:** Plan specified `active: bool = True` but newly declared WIP in system has `active=False`
- **Fix:** Changed default to `active: bool = False`
- **Files modified:** `testing/pytest/tests/factories/conftest.py`
- **Commit:** 0fea3d19

**3. [Rule 1 - Bug] Fixed parameter name mismatch in `create_production_graph`**
- **Found during:** Task 1 implementation; `create_batch` uses `work_order_key` not `wo_key`; same for `create_work_session`
- **Issue:** Plan's builder called `create_batch(... wo_key=...)` but fixture parameter is `work_order_key`
- **Fix:** Changed to use correct `work_order_key=` and `phase_key=` parameter names
- **Files modified:** `testing/pytest/tests/factories/conftest.py`
- **Commit:** 0fea3d19

**4. [Rule 1 - Bug] Fixed test isolation — Config defaults not restored between tests**
- **Found during:** Task 2 verification (full suite run showed `test_config_defaults_exist` failing after factory tests)
- **Issue:** `truncate_collections` skips Config (to preserve defaults) but `seed_config()` changes values; subsequent tests see modified Config
- **Fix:** Added `CONFIG_DEFAULTS` dict and restoration loop to `truncate_collections` teardown
- **Files modified:** `testing/pytest/conftest.py`
- **Commit:** 17ba800b

**5. [Rule 3 - Blocking] Restored missing backend files to worktree**
- **Found during:** Task 2 test run
- **Issue:** Worktree had sparse backend (missing `events/`, `managers/`, `middlewares/`, `utils/nats_client.py`) from a previous broken commit; tests couldn't import backend modules
- **Fix:** Restored full `backend/api/` from commit `ad356a00`, plus correct `conftest.py`/`schema.py`/`config.py` from `0430d3e4`
- **Files modified:** Multiple backend files
- **Commit:** 17ba800b

## Known Stubs

None — all factory outputs produce real ArangoDB documents verified via `db.collection(...).get(...)` assertions.

## Self-Check: PASSED

- testing/pytest/tests/factories/conftest.py: FOUND
- testing/pytest/tests/factories/test_factory_smoke.py: FOUND
- .planning/phases/01-infrastructure-fixtures/01-04-SUMMARY.md: FOUND
- Commit 0fea3d19 (Task 1): FOUND
- Commit 17ba800b (Task 2): FOUND
