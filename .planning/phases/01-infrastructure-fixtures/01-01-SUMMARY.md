---
phase: 01-infrastructure-fixtures
plan: 01
subsystem: testing
tags: [pytest, testcontainers, arangodb, uv, httpx, nats, fastapi]

# Dependency graph
requires: []
provides:
  - uv pytest project at testing/pytest/ with all test dependencies locked
  - conftest_helpers/schema.py with full COLLECTIONS list (49 collections) and initialize_schema()
  - Root conftest.py with 7 infrastructure fixtures: ArangoDB container, db override, NATS mock, httpx client, auth override, collection truncation
  - Correct import ordering: env vars set before backend module imports prevent module-level singleton race
affects:
  - 01-02 (factory fixtures — depends on db fixture and schema)
  - 01-03 (StepCompleted tests — uses all fixtures)
  - 01-04 (BatchCompleted tests — uses all fixtures)

# Tech tracking
tech-stack:
  added:
    - uv (Python package manager, lockfile-based)
    - pytest>=9.0 with pytest-asyncio (asyncio_mode=auto)
    - testcontainers>=4.14 (ArangoDB 3.11 ephemeral container)
    - httpx>=0.28 with ASGITransport (in-process ASGI test client)
    - nats-py (mocked at session scope)
  patterns:
    - Env vars set via os.environ.update before any backend import at module level
    - lru_cache cleared after env override so get_config() re-reads new values
    - db singleton override: db_module.db = test_db + auth_module.db = test_db
    - NATS mock: patch publish_sync in module namespace + all 4 local-import namespaces
    - Session-scoped container + db fixtures; function-scoped truncation (autouse)
    - is_in_position edge collection preserved in SKIP_TRUNCATE to retain IN/OUT defaults

key-files:
  created:
    - testing/pytest/pyproject.toml
    - testing/pytest/uv.lock
    - testing/pytest/conftest.py
    - testing/pytest/conftest_helpers/__init__.py
    - testing/pytest/conftest_helpers/schema.py
    - testing/pytest/tests/__init__.py
    - testing/pytest/tests/infrastructure/__init__.py
    - testing/pytest/tests/factories/__init__.py
  modified: []

key-decisions:
  - "uv hatchling build config requires packages=[conftest_helpers] since no top-level package directory exists"
  - "DBIndex model needs unique field (not in original db_init.py model but used in Task collection)"
  - "Static bcrypt hash used for cadmin user to avoid passlib dependency at schema import time"
  - "initialize_schema wraps errors with duplicate-detection to allow re-use if db already exists"
  - "truncate_collections: edge collections truncated first, SKIP_TRUNCATE preserves schema-init defaults"

patterns-established:
  - "Import ordering pattern: os.environ.update → get_config.cache_clear() → backend imports"
  - "Fixture dependency chain: arango_container → db → mock_nats → client (session scope)"
  - "NATS mock patches module-level binding AND all 4 local-import bindings (base_event, base_inventory, base_serial, print)"
  - "Auth override via app.dependency_overrides[verify_token] cleared on fixture teardown"

requirements-completed:
  - INFRA-01
  - INFRA-02
  - INFRA-03
  - INFRA-04
  - INFRA-05
  - INFRA-06
  - INFRA-07
  - INFRA-08

# Metrics
duration: 25min
completed: 2026-04-09
---

# Phase 01 Plan 01: Infrastructure Fixtures Summary

**pytest infrastructure with testcontainers ArangoDB, db singleton override, NATS mock, and httpx ASGI client — 7 session/function fixtures wired via correct import ordering**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-04-09T00:00:00Z
- **Completed:** 2026-04-09T00:25:00Z
- **Tasks:** 2 of 2
- **Files modified:** 8 created

## Accomplishments

- uv project at `testing/pytest/` with 52 packages resolved and locked in uv.lock
- `conftest_helpers/schema.py` with 49 Collection entries verbatim from db_init.py and `initialize_schema()` function
- `conftest.py` with all 7 infrastructure fixtures using correct import ordering (env vars before any backend module import)

## Task Commits

1. **Task 1: Create uv project and schema helper** - `aae3a59c` (feat)
2. **Task 2: Create root conftest with all infrastructure fixtures** - `8fe8fca1` (feat)

## Files Created/Modified

- `testing/pytest/pyproject.toml` - uv project config with pytest settings (asyncio_mode, pythonpath, testpaths)
- `testing/pytest/uv.lock` - locked dependency manifest (52 packages)
- `testing/pytest/conftest_helpers/schema.py` - DBIndex/Collection models, COLLECTIONS list (49 entries), initialize_schema()
- `testing/pytest/conftest_helpers/__init__.py` - package marker
- `testing/pytest/conftest.py` - root conftest with 7 infrastructure fixtures
- `testing/pytest/tests/__init__.py` - package marker
- `testing/pytest/tests/infrastructure/__init__.py` - package marker
- `testing/pytest/tests/factories/__init__.py` - package marker

## Decisions Made

- Added `packages = ["conftest_helpers"]` to `[tool.hatch.build.targets.wheel]` in pyproject.toml because hatchling couldn't determine which files to ship without an explicit package directory matching the project name
- Added `unique: bool | None = None` to `DBIndex` model — the original db_init.py model omits this field but the Task collection uses `unique=True` on the code index
- Replaced `pwd_context.hash('resetme')` with a static bcrypt hash to avoid passlib dependency at schema import time
- `initialize_schema()` wraps `create_database` and `create_collection` in try/except for "already exists" errors to make it idempotent

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added hatchling wheel packages config**
- **Found during:** Task 1 (uv sync)
- **Issue:** `uv sync` failed — hatchling could not determine package directory since no `progress_test_suite/` directory exists
- **Fix:** Added `[tool.hatch.build.targets.wheel]` with `packages = ["conftest_helpers"]` to pyproject.toml
- **Files modified:** testing/pytest/pyproject.toml
- **Verification:** `uv sync` succeeded, all 52 packages installed
- **Committed in:** aae3a59c (Task 1 commit)

**2. [Rule 1 - Bug] Added unique field to DBIndex model**
- **Found during:** Task 1 (schema.py creation)
- **Issue:** db_init.py DBIndex model does not define `unique` but `Task` collection uses `DBIndex(fields=['code'], name='task-code', unique=True)` — Pydantic v2 with strict validation would reject the extra field
- **Fix:** Added `unique: bool | None = None` to DBIndex model
- **Files modified:** testing/pytest/conftest_helpers/schema.py
- **Verification:** Schema loads without validation errors
- **Committed in:** aae3a59c (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 missing critical, 1 bug fix)
**Impact on plan:** Both fixes required for uv sync to succeed and schema to load. No scope creep.

## Issues Encountered

None — both issues auto-fixed inline during task execution.

## User Setup Required

None — no external service configuration required. Docker must be available for testcontainers (ArangoDB container).

## Next Phase Readiness

- uv project functional: `cd testing/pytest && uv sync` installs all deps
- pytest collects without errors (exit 5 = no tests, expected)
- Schema helper ready for factory fixtures (Plan 02)
- Conftest fixtures ready — all infrastructure fixtures in place for writing first tests
- Blocker: Python 3.11 required (backend api compatibility) but uv resolved to 3.13 locally — pytest test runs will need `uv run --python 3.11` or `.python-version` file if backend imports are version-sensitive

---
*Phase: 01-infrastructure-fixtures*
*Completed: 2026-04-09*
