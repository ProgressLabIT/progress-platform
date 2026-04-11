# Phase 1: Infrastructure + Fixtures - Context

**Gathered:** 2026-04-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a working pytest harness: ArangoDB testcontainer, db singleton override, NATS mock, schema initialization, test isolation via collection truncation, uv project management, and all factory fixtures for the domain object graph. No tests for business logic — only infrastructure and fixture smoke tests.

</domain>

<decisions>
## Implementation Decisions

### Test Suite Location
- **D-01:** Pytest suite lives at `testing/pytest/` inside the existing `testing/` directory, alongside Cypress and Robot Framework
- **D-02:** Test files organized by domain/event: `tests/infrastructure/`, `tests/step/`, `tests/batch/`, `tests/progress/`, `tests/movement/`, `tests/factories/`

### Schema Initialization
- **D-03:** Reuse `deploy/scripts/db_init.py` — import and call its schema creation functions directly from a session-scoped conftest fixture
- **D-04:** Skip `wait_for_db_ready()` loop — call init logic directly since the testcontainer is already ready when the fixture runs

### uv Project Layout
- **D-05:** `pyproject.toml` and `uv.lock` live at `testing/pytest/` — uv project root is the pytest suite directory
- **D-06:** Backend source made importable via `pythonpath = ["../../backend/api"]` in `[tool.pytest.ini_options]` in pyproject.toml — declarative, no sys.path manipulation

### Fixture Scope Hierarchy
- **D-07:** ArangoDB testcontainer — session scope (one container for the entire test run)
- **D-08:** Schema initialization via db_init.py — session scope (runs once after container starts)
- **D-09:** NATS mock via monkeypatch.setattr — session scope (mock once for all tests)
- **D-10:** httpx.AsyncClient with ASGITransport — session scope (no real TCP, auth via JWT headers per-request not cookies, DB isolation handled separately)
- **D-11:** JWT auth token fixture — function scope (cheap to generate, tests need different scopes)
- **D-12:** Factory fixtures (WorkOrder, Job, Batch, etc.) — function scope with raw `db.collection().insert()`, never `create_as_child()`
- **D-13:** Collection truncation between tests — function scope (edges before documents, respecting dependency order)
- **D-14:** Config document seeding — required in factories to avoid silent branch skipping in BatchCompleted

### Pre-Planning Decisions (carried forward)
- **D-15:** db singleton override: set `PROGRESS_*` env vars before backend module import + clear `get_config` lru_cache
- **D-16:** NATS `publish_sync` mocked at session scope to prevent post-commit crashes

### Claude's Discretion
- Factory smoke tests in `tests/factories/` — Claude to determine what validation is needed to ensure factory outputs match real event outputs
- conftest.py split strategy — single root conftest vs per-domain conftest files, Claude to decide during planning

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Database & Schema
- `backend/api/utils/db.py` — Module-level db singleton (`conf = get_config()`, `db = client.db(...)`) — this is what needs to be overridden before import
- `backend/api/utils/config.py` — `get_config()` with `@lru_cache()`, uses `PROGRESS_*` env prefix and pydantic-settings
- `deploy/scripts/db_init.py` — 13KB canonical schema init script — creates all collections, edge collections, indexes, default records. Reuse for test schema initialization.

### Testing Strategy
- `km/testing/strategy.md` — Defines spec-first development loop, real database requirement, test layers. This project implements that strategy.

### Event Architecture
- `backend/api/events/base_event.py` — BaseEvent abstract class with `save()` → `pre_processing()` → `apply()` → `store_event()` → `commit_transaction()` flow. Events manage their own ArangoDB transactions.
- `backend/api/models/event.py` — EventType enum with all 50+ event types

### Domain Models
- `backend/api/models/` — Pydantic models for all domain entities (products, jobs, batches, serials, inventory)
- `backend/api/endpoints/production.py` — Production endpoint handlers (StepCompleted, BatchCompleted dispatch)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `deploy/scripts/db_init.py` — Schema creation functions to be imported directly
- `backend/api/utils/config.py` — `Settings` class with all env var definitions needed for test configuration
- `backend/api/utils/auth.py` — JWT signing logic to replicate in test token fixture

### Established Patterns
- Module-level singletons in `utils/db.py` — must set env vars before import
- `@lru_cache()` on `get_config()` — must clear cache after env var override
- Events use internal transactions via `Event.save()` — cannot be wrapped in outer transactions (no nesting in ArangoDB)
- Pydantic v2 models with ArangoDB field aliases (`_id`, `_key`, `_rev`, `_from`, `_to`)

### Integration Points
- `backend/api/main.py` — FastAPI app instance for ASGITransport
- `backend/api/endpoints/` — HTTP routes for API integration tests
- `backend/api/events/` — Event classes for direct instantiation tests

</code_context>

<specifics>
## Specific Ideas

- Session-scoped httpx.AsyncClient because ASGITransport has no TCP overhead and auth is JWT Bearer (header per request), not cookies — no session state leakage
- Factory smoke tests should validate that raw-insert factory outputs match what real events would produce, catching drift if event logic changes
- The BatchCompleted 32-combination parametrize matrix requires surgical control over preconditions (first/last phase, traceability, warehouse, auto_new_batch) — raw inserts are essential for this

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-infrastructure-fixtures*
*Context gathered: 2026-04-09*
