# Architecture Research

**Domain:** Test suite for event-sourced FastAPI + ArangoDB + Vue 3/Quasar MES
**Researched:** 2026-04-08
**Confidence:** HIGH (based on direct codebase inspection, not speculation)

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     TEST INFRASTRUCTURE LAYER                    │
│  ┌──────────────────┐  ┌──────────────────────────────────────┐ │
│  │  conftest.py     │  │   factory fixtures                   │ │
│  │  (session scope) │  │   (class/function scope)             │ │
│  │  - ArangoDB TC   │  │   - WorkOrder → Job → Batch →        │ │
│  │  - DB lifecycle  │  │     WorkSession → StepExecData       │ │
│  │  - Auth tokens   │  │   - Inventory positions, serials     │ │
│  └────────┬─────────┘  └──────────────┬───────────────────────┘ │
└───────────┼────────────────────────────┼────────────────────────┘
            │                            │
┌───────────┼────────────────────────────┼────────────────────────┐
│           │   BACKEND TEST LAYERS       │                        │
│  ┌────────▼─────────┐  ┌───────────────▼──────────────────────┐ │
│  │  Layer 2 (API)   │  │  Layer 2 (Direct Event)              │ │
│  │  httpx.AsyncClient│  │  event.save() without HTTP           │ │
│  │  Full HTTP cycle  │  │  Edge cases, error paths             │ │
│  │  Main happy paths │  │  Child event cascade testing         │ │
│  └────────┬─────────┘  └───────────────┬──────────────────────┘ │
│           │                            │                        │
│  ┌────────▼────────────────────────────▼──────────────────────┐ │
│  │               Real ArangoDB (testcontainers)                │ │
│  │  Collections: Job, Batch, WorkOrder, WorkSession,           │ │
│  │  StepExecutionData, Event, event_source, Inventory*, Serial │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND TEST LAYERS                         │
│  ┌──────────────────────────┐  ┌──────────────────────────────┐ │
│  │  Vitest + @vue/test-utils│  │  Playwright E2E              │ │
│  │  ProgressBtn.vue         │  │  login → job → batch-complete│ │
│  │  WorkSessionSteps.vue    │  │  WO creation, stock movement │ │
│  │  JSDOM environment       │  │  Against real app server     │ │
│  └──────────────────────────┘  └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  QUALITY / LOAD TEST LAYERS                      │
│  ┌──────────────────────────┐  ┌──────────────────────────────┐ │
│  │  Schemathesis             │  │  Locust                      │ │
│  │  OpenAPI spec fuzzing     │  │  Concurrent event dispatch   │ │
│  │  Runs after spec audit    │  │  Production query load       │ │
│  └──────────────────────────┘  └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Built With |
|-----------|----------------|------------|
| `conftest.py` (session) | Spin up ArangoDB testcontainer, initialize collections/graphs to match prod schema, create auth JWT, expose `db` and `client` fixtures | testcontainers-python, python-arango, httpx |
| `conftest.py` (class/function) | Truncate collections between tests, provide domain object graph factories | python-arango, pytest fixtures |
| Factory fixtures | Insert realistic document graphs: WorkOrder→Job→Batch→WorkSession→StepExecData, InventoryPosition, Serial | python-arango direct inserts (no ORM) |
| Layer 2 API tests | Exercise endpoints via httpx.AsyncClient, assert HTTP status + response body, covers main happy paths | pytest-asyncio, httpx |
| Layer 2 direct event tests | Instantiate event classes directly, call `.save()`, assert DB state, covers edge cases and cascade paths that are hard to reach via HTTP | python-arango, pytest |
| NATS mock/stub | Allow tests to run without a real NATS broker; patch `publish_sync` so events complete without side-effect failures | pytest monkeypatch or nats-mock |
| Vitest unit tests | Fast component tests for ProgressBtn.vue and WorkSessionSteps.vue state machines | vitest, @vue/test-utils, jsdom |
| Playwright E2E | 5–10 critical user journeys against a fully-running stack | Playwright, real backend |
| Schemathesis | Fuzz OpenAPI spec after endpoint schema audit, property-based testing | Schemathesis CLI or pytest plugin |
| Locust | Concurrent load scenarios for event dispatch and query endpoints | Locust, Python |

## Recommended Project Structure

```
backend/api/
└── tests/
    ├── conftest.py              # ArangoDB TC session fixture, httpx client, auth JWT, truncation helpers
    ├── factories/
    │   ├── __init__.py
    │   ├── production.py        # make_work_order(), make_job(), make_batch(), make_work_session()
    │   ├── inventory.py         # make_position(), make_serial()
    │   └── traceability.py      # make_step_execution_data()
    ├── unit/
    │   ├── test_validators.py   # Pure function tests (no DB)
    │   └── test_transformations.py
    ├── integration/
    │   ├── test_step_completed.py       # StepCompletedEvent — happy path, last-step cascade
    │   ├── test_batch_completed.py      # BatchCompletedEvent — WIP, inventory, job close
    │   ├── test_progress_override.py    # ProgressOverrideRequestedEvent
    │   ├── test_movement_completed.py   # MovementCompletedEvent — all movement types
    │   ├── test_serial_events.py        # Serial lifecycle
    │   └── test_collaboration_events.py # Issues, messages, tasks
    └── schemathesis/
        └── test_api_fuzz.py             # Schemathesis stateful tests against OpenAPI spec

webapps/main/
└── src/
    └── components/
        ├── ProgressBtn.test.js          # Co-located with component (vitest.config.js: src/**/*.test.js)
        └── WorkSessionSteps.test.js     # (or views/WorkSessionSteps.test.js)

testing/
└── playwright/
    ├── playwright.config.ts
    └── tests/
        ├── production_flow.spec.ts      # login → start job → batch complete
        ├── work_order.spec.ts           # WO creation → BOM → release
        └── stock_movement.spec.ts       # movement → inventory verify

testing/
└── locust/
    ├── locustfile.py                    # EventDispatch, ProductionQuery, InventoryMovement scenarios
    └── tasks/
        ├── production.py
        └── inventory.py
```

### Structure Rationale

- **`tests/` co-located with `backend/api/`:** Tests import event classes, models, and utilities directly without install. Matches existing Python project layout and the testing strategy doc.
- **`factories/` separate from `conftest.py`:** Factories grow large quickly (50+ event types). Keeping them in modules keeps conftest focused on infrastructure.
- **`integration/` one file per domain event group:** Mirrors the event directory structure (`events/production/`, `events/inventory/`, etc.). Easy to find tests for a given event type.
- **`schemathesis/` in tests/:** Schemathesis tests are pytest tests; they share the httpx client fixture naturally.
- **Playwright in `testing/playwright/`:** Separate from pytest because it uses a different runner (Playwright test runner or pytest-playwright). Keeps the two test stacks clearly separated.
- **Frontend `.test.js` co-located:** Vitest config already specifies `src/**/*.test.js`. Co-location is standard Vitest convention.

## Architectural Patterns

### Pattern 1: Layered Fixture Pyramid

**What:** Fixtures organized by scope — session (container), class (truncation), function (factories) — so the expensive ArangoDB container starts once per session while each test class gets a clean slate.

**When to use:** Any test suite with a real database. The pyramid prevents both slow tests (recreate DB per test) and contamination (share state across tests).

**Trade-offs:** Setup is more complex upfront; payoff is 10-100x faster test runs vs. per-test container recreation.

```python
# conftest.py
@pytest.fixture(scope="session")
def arango_container():
    with ArangoContainer("arangodb:3.12") as container:
        yield container

@pytest.fixture(scope="session")
def db(arango_container):
    client = ArangoClient(hosts=arango_container.get_connection_url())
    db = client.db("_system", username="root", password="")
    db.create_database("progress_test")
    test_db = client.db("progress_test", username="root", password="")
    _init_collections(test_db)   # Mirror prod schema
    yield test_db

@pytest.fixture(autouse=True)
def truncate_collections(db):
    yield
    for col in MUTABLE_COLLECTIONS:
        db.collection(col).truncate()
```

### Pattern 2: Dual-Layer Event Testing

**What:** Each significant event is tested at two levels: HTTP API (realistic, end-to-end) and direct event instantiation (focused, edge-case coverage). The two layers are complementary, not redundant.

**When to use:** Event-sourced systems where a single HTTP call can cascade into 5+ child events. The API layer tests the integration; the direct layer tests the cascade logic in isolation.

**Trade-offs:** Writing tests at both layers takes more time. The payoff is that cascade edge cases (last batch → job close, WIP multi-phase, serial handling) are testable without complex HTTP setup.

```python
class TestBatchCompletedEvent:
    """
    Feature: Batch Completion
    When a batch is completed, WIP is updated, inventory movements are generated,
    and if it is the last batch the job is closed.
    """

    # API layer: realistic path
    async def test_complete_batch_via_api(self, client, seed_running_batch):
        response = await client.post(f"/jobs/{seed_running_batch['job_key']}/complete-batch", json={...})
        assert response.status_code == 200

    # Direct layer: cascade edge case
    async def test_last_batch_triggers_job_close(self, db, seed_last_batch):
        event = BatchCompletedEvent(info={
            "active_batch_key": seed_last_batch["_key"],
            "completed_batch_qt": seed_last_batch["qt_total"],
            ...
        })
        event.save()
        job = db.collection("Job").get(seed_last_batch["job_key"])
        assert job["stage"] == "closed"
```

### Pattern 3: NATS Isolation via Monkeypatch

**What:** Tests patch `publish_sync` in `utils.nats_client` to a no-op. This prevents tests from needing a real NATS broker while still exercising the full event transaction.

**When to use:** All backend tests. NATS publication is best-effort (exceptions in `_publish_collected_events` are caught and logged, not re-raised), so patching it out has no effect on correctness assertions.

**Trade-offs:** NATS publication paths are not tested. This is acceptable — NATS integration is infrastructure behavior, not business logic. A separate integration/smoke test can verify NATS connectivity in a dedicated environment.

```python
# conftest.py
@pytest.fixture(autouse=True)
def no_nats(monkeypatch):
    monkeypatch.setattr("utils.nats_client.publish_sync", lambda subject, data: None)
```

### Pattern 4: Spec-First Test Classes

**What:** Each test class maps to an acceptance criterion set. The class docstring is the spec; each method docstring is a Given/When/Then scenario. No BDD framework — just pytest docstrings.

**When to use:** All integration tests. Enforces the spec-first loop: write the class + docstrings first (they fail), then implement.

**Trade-offs:** Slightly more verbose than bare `def test_x`. Payoff is that tests serve as living documentation without a separate `.feature` file maintenance burden.

## Data Flow

### Test Data Flow (Backend)

```
pytest session start
    ↓
ArangoContainer starts (testcontainers)
    ↓
conftest creates "progress_test" DB + initializes collections
    ↓
conftest creates httpx.AsyncClient (with auth header)
    ↓
Test class setup: factory fixtures insert document graph
    WorkOrder → Job → Batch → WorkSession → StepExecutionData
    InventoryPosition (if needed)  Serial (if needed)
    ↓
Test runs:
  Option A (API layer):  httpx.AsyncClient.post() → FastAPI → Event.save() → ArangoDB tx
  Option B (Direct):     EventClass(info={...}).save() → ArangoDB tx (NATS patched out)
    ↓
Test asserts:
  Response body (API) OR direct DB query (both layers)
    ↓
autouse truncate_collections fixture runs
    ↓
Next test class (clean collections, same container)
```

### Event Cascade Data Flow (what tests must traverse)

```
StepCompletedEvent.save()
    ├── Writes StepExecutionData
    └── if last step:
        └── BatchCompletedEvent.create_as_child()
                ├── WorkSessionClosedEvent.create_as_child()
                ├── if not first_phase: WIPRemovedEvent.create_as_child()
                ├── if not last_phase: WIPDeclaredEvent.create_as_child()
                ├── if last_phase: BatchReleasedEvent.create_as_child()
                ├── _process_inventory_changes() → MovementCompletedEvent(s)
                ├── _handle_batch_serials() → SerialLinkedEvent / SerialUpdatedEvent
                └── if last batch: JobClosedEvent.create_as_child()
                        └── if auto_new_batch:
                                ├── BatchCreatedEvent.create_as_child()
                                └── WorkSessionCreatedEvent.create_as_child()
```

This cascade means a single `StepCompletedEvent.save()` call can write to 8+ collections in one ArangoDB transaction. Tests must seed the correct graph depth for each branch to be reachable.

### Key Data Flows

1. **Happy path (step → batch → new batch):** Requires WorkOrder + Job (multi-batch qty) + Batch + WorkSession + all required Steps seeded. All steps completed → BatchCompleted → auto BatchCreated.
2. **Job close path:** Job must have `qt_planned == qt_completed + batch.qt_total`. Same cascade as above plus JobClosed at the end.
3. **WIP cascade path:** Job must have `first_phase=False` or `last_phase=False`. Requires seeded WIP records for WIPRemoved to succeed.
4. **Inventory path:** Job must have inventory movements configured (BOM with components). Requires seeded InventoryPosition documents.
5. **Serial path:** Job must have `traceability_level` set. Requires seeded Serial documents assigned to the batch.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Initial build | One conftest.py, factories as simple functions, tests co-located in `tests/integration/`. Session-scoped container. |
| 50+ test files | Extract factories to dedicated module. Add `pytest-xdist` for parallelism — but requires per-worker DB isolation (separate DB name per worker or collection namespacing). |
| CI pipeline | Testcontainers works in Docker-in-Docker (DinD). Playwright needs `--ipc=host` or `playwright install-deps`. Locust runs headless. |

## Anti-Patterns

### Anti-Pattern 1: Mock the Database

**What people do:** Replace ArangoDB with a mock or in-memory store to make tests faster.

**Why it's wrong:** The entire business logic is in `apply()` methods that use AQL queries, ArangoDB transactions with specific collection locks, and graph traversals. None of this can be faithfully mocked. The testing strategy doc explicitly rules this out (Principle #4).

**Do this instead:** Use testcontainers-python with a real ArangoDB image. Container startup takes ~5 seconds once per session; individual test truncation takes milliseconds.

### Anti-Pattern 2: Test the Event Cascade Only at the HTTP Layer

**What people do:** Write only API-level tests and rely on integration coverage to reach edge cases.

**Why it's wrong:** The `BatchCompletedEvent.apply()` method alone has 7+ conditional branches (last batch, last phase, first phase, serial handling, auto_new_batch, WIP cascade, inventory). Reaching all branches via HTTP requires complex, brittle seed data. Timeout- and auth-related test failures also obscure the real assertion.

**Do this instead:** Use the dual-layer pattern. API tests cover the nominal path; direct event tests cover each conditional branch independently with minimal seed data.

### Anti-Pattern 3: Session-Scoped Mutable State in Factories

**What people do:** Create domain objects once at session scope and mutate them across tests.

**Why it's wrong:** `BatchCompletedEvent` marks a batch as complete. If the same batch fixture is reused across tests in the class, the second test sees an already-completed batch and fails with `ValueError: Job is already closed`.

**Do this instead:** Factories at `function` scope (default pytest fixture scope). Truncation in `autouse` teardown ensures the next test starts clean. The testcontainers session fixture is expensive; the factory fixtures are cheap.

### Anti-Pattern 4: Vitest Environment Set to `node` for Vue Component Tests

**What people do:** Leave the existing `vitest.config.js` with `environment: 'node'` and try to test Vue components.

**Why it's wrong:** The current config (`environment: 'node'`) is correct for utility/composable testing but will fail when testing components that use DOM APIs (`document`, `window`, Quasar UI). `@vue/test-utils` requires a DOM environment.

**Do this instead:** Switch to `environment: 'jsdom'` (or `'happy-dom'` for better performance) and install `@vue/test-utils` + `jsdom`. Quasar components also require a Quasar plugin installation in the test setup file.

### Anti-Pattern 5: Running Schemathesis Before the OpenAPI Spec is Complete

**What people do:** Point Schemathesis at the live OpenAPI spec immediately to find issues.

**Why it's wrong:** FastAPI auto-generates OpenAPI schemas from endpoints. If endpoints have `response_model=None` or missing `body` schemas, Schemathesis generates invalid test cases and produces noise rather than signal.

**Do this instead:** Audit every endpoint for complete input/output schemas first (the OpenAPI spec completeness audit requirement in PROJECT.md). Run Schemathesis only after the audit confirms all schemas are complete.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| ArangoDB (real) | testcontainers-python `ArangoContainer` — session scope | ArangoDB Docker image `arangodb:3.12`. `ARANGO_NO_AUTH=1` for tests to avoid credential setup. |
| NATS | monkeypatch `publish_sync` to no-op | Do not spin up a NATS container for unit/integration tests. Only needed for E2E smoke tests. |
| FastAPI app | `httpx.AsyncClient(app=app, base_url="http://test")` — ASGI transport | No running server needed; direct ASGI invocation. Override `utils.db.db` with test DB via `app.dependency_overrides`. |
| Playwright browsers | `playwright install chromium` in test setup | Playwright tests need the full app stack running (backend + frontend built). Use `docker compose up` against a test env. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| conftest.py ↔ FastAPI app | `app.dependency_overrides[get_db]` replaces prod DB with test DB | The global `db` singleton in `utils/db.py` is the hard part: it reads config at import time. Override via dependency injection or environment variables before import. |
| Factory fixtures ↔ ArangoDB | Direct `python-arango` inserts — no event classes | Bypasses event logic intentionally. Seeds the exact pre-condition state. |
| Direct event tests ↔ Event classes | `from events.production.batch_completed import BatchCompletedEvent` — direct import | Test runner must set `PYTHONPATH=backend/api` so imports resolve without a running server. |
| Vitest ↔ Quasar components | Quasar plugin must be installed in test setup | `installQuasarPlugin` from `@quasar/quasar-app-extension-testing-unit-vitest` or manual install. |
| Schemathesis ↔ FastAPI | Schemathesis reads `/openapi.json` from a running test server | Use `pytest-asyncio` + `httpx` to serve the app, or point at a running `uvicorn` instance. |
| Locust ↔ backend | Locust `HttpUser` hits the real API at a base URL | Run Locust against a dedicated load-test environment, not the testcontainers DB. |

## Sources

- Direct codebase inspection: `backend/api/events/base_event.py`, `events/production/batch_completed.py`, `events/production/step_completed.py`
- `km/testing/strategy.md` — spec-first loop, real DB principle, test layer definitions
- `.planning/codebase/ARCHITECTURE.md` — event cascade data flow, transaction scope
- `.planning/PROJECT.md` — explicit requirements list and tool selection rationale
- `.planning/codebase/STRUCTURE.md` — file locations, naming conventions
- testcontainers-python docs (HIGH confidence — standard pattern for containerized test DBs)
- Vitest docs: `environment: 'jsdom'` requirement for DOM-dependent components (HIGH confidence)

---
*Architecture research for: Progress Platform test suite*
*Researched: 2026-04-08*
