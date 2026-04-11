# Project Research Summary

**Project:** Progress Platform Test Suite
**Domain:** Automated testing for event-sourced MES application
**Researched:** 2026-04-09
**Confidence:** HIGH

## Executive Summary

The Progress Platform requires a multi-layer test suite for an event-sourced FastAPI backend backed by ArangoDB, a Vue 3/Quasar frontend, and a complex domain model centered on a production event cascade (StepCompleted -> BatchCompleted -> 5-10 child events in a single ArangoDB transaction). The standard approach uses testcontainers for isolated ArangoDB instances, two backend test layers (HTTP API for nominal paths, direct event instantiation for cascade edge cases), Vitest for frontend components, and Playwright for critical E2E journeys.

The highest-risk area is the infrastructure foundation. The ArangoDB `db` singleton is created at module import time (`utils/db.py`), NATS publishing is tightly coupled to the event save lifecycle, and testcontainers starts with no schema. Every downstream phase depends on getting this right first — without correct env-var injection before backend imports, NATS mocking at session scope, and schema initialization in `conftest.py`, all subsequent tests produce misleading results.

The most complex single target is `BatchCompletedEvent`, which has 200+ lines of conditional logic, 7+ branches producing a permutation matrix of 32 combinations (first_phase, last_phase, auto_new_batch, traceability_level, warehouse_management). Silently skipping branches due to missing Config documents is the primary failure mode — factory fixtures must explicitly seed Config documents and assert branch flags before making domain assertions.

## Key Findings

### Recommended Stack

All versions verified April 2026 via PyPI/npm. No exotic choices — httpx and python-arango are already production dependencies.

**Core technologies:**
- **uv 0.11.4**: Python package manager — fast, lockfile support, `pyproject.toml` native
- **pytest 9.0.2 + pytest-asyncio 1.3.0**: Test runner — `asyncio_mode = "auto"` avoids per-test decorators
- **testcontainers[arangodb] 4.14.2**: Real ArangoDB per session — CI-friendly, fully isolated
- **httpx 0.28.1**: HTTP API test client — FastAPI's recommended async test client
- **schemathesis 4.13.0**: API fuzzing — `from_asgi()` integration, no running server needed
- **locust 2.43.4**: Load testing — Python-native, scriptable
- **Vitest 3.x + @quasar/quasar-app-extension-testing-unit-vitest**: Vue component tests
- **Playwright (Node)**: E2E browser tests — multi-browser, API mixing support

### Expected Features

**Must have (table stakes):**
- Real ArangoDB via testcontainers + collection truncation isolation
- Factory fixtures: WorkOrder -> Job -> Batch -> WorkSession -> StepExecutionData + Config documents
- Dual-layer backend tests: HTTP API (httpx) + direct event instantiation
- Deep test suites for StepCompleted, BatchCompleted, ProgressOverrideRequested, MovementCompleted
- Serial event coverage (Created, Updated, Linked, Released)
- OpenAPI spec completeness audit (input/output schemas, docstrings)

**Should have (competitive):**
- Schemathesis fuzzing against verified OpenAPI spec
- BatchCompleted 32-combination permutation matrix
- Event idempotency tests (replay without side effects)
- Locust concurrent event dispatch scenarios
- Vitest: ProgressBtn.vue, WorkSessionSteps.vue
- Playwright: 3 critical E2E journeys

**Defer (v2+):**
- GitLab CI/CD integration
- Visual regression snapshots
- Capacitor mobile testing
- Full coverage backfill on all existing code

### Architecture Approach

The test suite has 7 major components with strict dependency ordering. Infrastructure (`conftest.py`) is the foundation everything depends on. Backend tests use a dual-layer pattern where HTTP API tests cover realistic paths and direct event tests cover cascade branches that require impractical seed complexity via HTTP.

**Major components:**
1. **conftest.py (session scope)** — testcontainer lifecycle, schema init, NATS mock, httpx client, auth JWT
2. **factories/ module** — raw `db.collection().insert()` builders for domain object graphs; never `create_as_child()`
3. **Integration tests (dual-layer)** — API layer for nominal paths, direct event layer for cascade branches
4. **Vitest + Quasar plugin** — jsdom environment, `installQuasarPlugin()`, `$q.dialog` spying
5. **Playwright E2E** — production flow, work order, stock movement specs
6. **Schemathesis** — `from_asgi()` ASGI integration after OpenAPI spec audit
7. **Locust** — concurrent BatchCompleted scenarios, <100 concurrent users

### Critical Pitfalls

1. **`db` singleton at import time** — set `PROGRESS_ARANGO_URL` env vars before any backend import; call `get_config.cache_clear()` after container starts
2. **NATS `publish_sync` raises post-commit** — `monkeypatch.setattr("utils.nats_client.publish_sync", ...)` at session scope; affects every direct event test
3. **Missing Config documents silently skip branches** — `enable_inventory_management`, `default_production_position`, `default_consumption_position` must be in test DB; add smoke assertions before domain assertions
4. **ArangoDB has no test-rollback** — must explicitly truncate ALL collections (edges before documents) between tests
5. **Quasar `$q.dialog()` uses Teleport** — invisible to Vitest JSDOM wrapper; spy on `$q.dialog` instead of DOM traversal

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Test Infrastructure Foundation
**Rationale:** Everything depends on this — `db` singleton override, NATS mock, schema init, isolation pattern
**Delivers:** conftest.py, testcontainer lifecycle, factory fixtures, first smoke test
**Addresses:** All table stakes infrastructure
**Avoids:** Pitfalls 1, 2, 3, 4

### Phase 2: Critical Event Test Suites
**Rationale:** StepCompleted -> BatchCompleted is the highest-value cascade; ProgressOverrideRequested + MovementCompleted cover remaining critical paths
**Delivers:** Deep dual-layer tests for 4 critical events + serial events + collaboration events
**Uses:** pytest, testcontainers, httpx, factory fixtures from Phase 1
**Implements:** Both test layers (API + direct event)

### Phase 3: OpenAPI Spec Audit + Schemathesis + Locust
**Rationale:** Spec audit must precede fuzzing; Locust requires stable test environment
**Delivers:** Complete endpoint schemas/docstrings, Schemathesis fuzzing suite, Locust load scenarios
**Uses:** schemathesis, locust
**Implements:** API quality layer

### Phase 4: Frontend Tests (Vitest + Playwright)
**Rationale:** Independent of backend; requires Vitest environment fix (jsdom) first
**Delivers:** Vitest component tests for ProgressBtn + WorkSessionSteps, Playwright E2E for 3 critical journeys
**Uses:** Vitest, @vue/test-utils, Playwright
**Implements:** Frontend test layer

### Phase Ordering Rationale

- Infrastructure before all domain phases (db singleton, NATS mock are hard blockers)
- Critical event cascade before peripheral events (highest risk/value ratio)
- OpenAPI audit must precede Schemathesis (fuzzing incomplete spec = noise)
- Frontend is independent track, can run after infrastructure is stable

### Research Flags

Phases needing deeper research during planning:
- **Phase 1:** Validate the `db` singleton override strategy against actual `utils/db.py` + `get_config` `lru_cache`; run a spike
- **Phase 2:** BatchCompletedEvent fixture builder design (32-combination parametrize matrix) warrants a design session

Phases with standard patterns (skip research-phase):
- **Phase 3:** Schemathesis `from_asgi()` is well-documented; Locust is standard
- **Phase 4:** Vitest + Quasar extension is documented; Playwright is standard

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified via PyPI/npm April 2026 |
| Features | HIGH | Based on direct codebase analysis of 80+ event files |
| Architecture | HIGH | Verified from source code inspection of base_event.py, batch_completed.py, utils/db.py |
| Pitfalls | HIGH | Most pitfalls from direct code analysis; ArangoDB pitfalls confirmed by official docs |

**Overall confidence:** HIGH

### Gaps to Address

- **ArangoDB image version:** Confirm production uses 3.11 and pin testcontainer to match
- **Vitest/Quasar extension compatibility:** Verify against actual `@quasar/app-vite` version in `webapps/main/package.json`
- **`db` singleton override:** Confirm strategy works with `lru_cache` + import-time instantiation before finalizing conftest

---
*Research completed: 2026-04-09*
*Ready for roadmap: yes*
