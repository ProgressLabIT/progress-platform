# Testing Patterns

**Analysis Date:** 2026-05-08

## Test Framework

**Backend Integration Tests:**
- pytest >= 9.0 with pytest-asyncio (auto mode)
- testcontainers >= 4.14 for real ArangoDB 3.11 (never mocked)
- httpx >= 0.28 with ASGITransport for in-process FastAPI testing
- Config: `testing/pytest/pyproject.toml` (requires Python >= 3.11)
- Dependency management: `uv` (see Run Commands)

**Frontend Component Tests:**
- Vitest 4.1.0 (Vue test framework)
- Config: `webapps/main/vitest.component.config.js`
- Environment: `happy-dom` (lightweight DOM simulation)
- Naming: `*.component.test.js` pattern
- Examples: `webapps/main/src/stores/rightDrawer.component.test.js`, `src/stores/userHub.component.test.js`

**API Fuzzing:**
- Schemathesis >= 4.15 for OpenAPI-driven property-based testing
- Tests at `testing/pytest/tests/api/test_schemathesis.py`

**E2E Browser Tests:**
- Playwright (JS) with Chromium
- Config: `testing/playwright/playwright.config.js`
- Manual-run (requires full stack at localhost)
- 4 journey specs: `login_to_batch_complete.spec.js`, `stock_receipt.spec.js`, `traceability_journey.spec.js`, `work_order_creation.spec.js`

**Load Testing:**
- Locust >= 2.0
- Scenarios at `testing/locust/` (batch_completion.py, inventory_movement.py, production_queries.py)

**Run Commands:**
```bash
# Backend integration tests (from testing/pytest/)
cd testing/pytest
uv sync                        # Install dependencies
uv run pytest                  # Run all tests
uv run pytest tests/production/        # Run domain-specific tests
uv run pytest -k "test_job_started"    # Run by name match
uv run pytest --cov                    # With coverage (pytest-cov)

# Frontend component tests
cd webapps/main
yarn test:components           # Run Vitest component tests

# E2E tests (from testing/playwright/)
npm test                       # All journeys
npm run test:login             # Single journey

# Load tests
locust -f testing/locust/batch_completion.py --headless -u 10 -r 2 --run-time 30s --host http://localhost:8000
```

## Test File Organization

**Backend (pytest):**
```
testing/pytest/
├── pyproject.toml                    # pytest config, dependencies
├── conftest.py                       # Infrastructure + factory fixtures (43KB)
├── conftest_helpers/
│   └── schema.py                     # ArangoDB schema initialization
└── tests/
    ├── conftest.py                   # Minimal (factories in root conftest)
    ├── helpers.py                    # Shared assertion helpers
    ├── api/
    │   ├── test_auth.py
    │   ├── test_openapi_audit.py
    │   └── test_schemathesis.py
    ├── batch/
    │   ├── test_batch_completed_api.py
    │   └── test_batch_completed_direct.py
    ├── collaboration/
    │   ├── test_issues.py
    │   └── test_messages.py
    ├── factories/
    │   └── test_factory_smoke.py
    ├── infrastructure/
    │   └── test_harness_smoke.py
    ├── movement/
    │   ├── test_movement_completed.py
    │   └── test_movement_with_serials.py
    ├── production/
    │   ├── test_batch_state.py
    │   ├── test_job_lifecycle.py
    │   └── test_work_orders.py
    ├── progress/, serial/, step/     # (directories exist, contents TBD)
    └── integration/
        └── sparkplug_session/        # Spike tests
```

**Frontend (Vitest):**
- Component tests co-located: `webapps/main/src/**/*.component.test.js`
- Run command: `yarn test:components` from `webapps/main/`
- Environment: `happy-dom` (no browser required)

**Playwright E2E:**
- `testing/playwright/`
- Journey specs: `{journey_name}.spec.js`
- Prerequisites: full stack running at `http://localhost`

**Naming:**
- Test files: `test_{domain}_{feature}.py` (pytest), `{component}.component.test.js` (Vitest)
- Test classes: `TestFeatureName` (e.g., `TestJobLifecycle`, `TestIssueLifecycle`)
- Test methods: `test_{scenario}` with BDD docstring (e.g., `test_01_create_critical_issue`)
- Playwright specs: `describe('{Journey Name (E2E-XX)}')` / `test('{step description}')`

## Test Infrastructure (pytest)

**ArangoDB Container (session scope):**
- Real ArangoDB 3.11 via testcontainers -- **NO mocks** (testing principle #4)
- Fixture: `arango_container()` in `testing/pytest/conftest.py:52`
- Started once per session, reused across all tests
- Schema initialized via `testing/pytest/conftest_helpers/schema.py`
- Wait condition: logs "is ready for business"

**Database Override (session scope, autouse):**
- Module-level `db` singleton in `utils.db` monkey-patched to point at testcontainer
- All modules that captured `from utils.db import db` at import time are also patched
- Fixture: `db()` in `testing/pytest/conftest.py:71`
- Patch locations: `utils.db`, `utils.auth`, `events.base_event`

**NATS Mock (session scope, autouse):**
- `publish_sync` replaced with noop lambda across modules that import it locally
- `connect()` and `drain()` mocked to prevent real NATS connections
- Fixture: `mock_nats()` in `testing/pytest/conftest.py:113`
- Patched modules: `utils.nats_client`, `events.base_event`, `events.inventory.base_inventory`, `events.serial.base_serial`, `endpoints.print`

**WeasyPrint Stub:**
- Stubbed at import time (before any backend module loads) -- `conftest.py:10`
- WeasyPrint requires native GTK libraries (not available in test environments)
- Stubs: `weasyprint`, `weasyprint.text`, `weasyprint.text.fonts`

**ASGI Test Client (session scope):**
- `httpx.AsyncClient` with `ASGITransport(app=app)` -- tests FastAPI in-process
- Fixture: `client()` in `testing/pytest/conftest.py:163`
- Base URL: `http://test`

**Auth Override (function scope):**
- Factory fixture returning callable that generates JWT auth headers
- Overrides `verify_token` dependency with test `TokenData`
- Fixture: `auth_headers()` in `testing/pytest/conftest.py:177`
- Usage: `auth_headers("operator production")` -- space-separated scope string
- Clears dependency overrides after each test

**Collection Truncation (function scope, autouse):**
- After each test, truncates all non-system collections except `Config`, `Counter`, `CustomField`, `Queue`, `is_in_position`
- Edge collections truncated first, then document collections
- Config defaults captured at session start (`_capture_config_defaults`) and restored after each test
- Fixture: `truncate_collections()` in `testing/pytest/conftest.py:232`

## Test Structure Pattern

**BDD-style docstrings with provenance:**
```python
class TestIssueLifecycle:
    """HTTP API tests for issue lifecycle events via POST /event."""

    issue_key: str = ""

    @pytest.mark.asyncio
    async def test_01_create_critical_issue(self, client, auth_headers):
        """Given a product context,
        when an ISSUE_CREATED event is sent with critical=True,
        then the issue is persisted with critical flag and returns issue_key.
        Migrated from: collaborations.robot 'Send critical product issue created event'.
        """
        auth_headers()
        payload = {
            "event_type": "ISSUE_CREATED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "issue_data": {
                "issue_type_key": "3142793",
                "critical": True,
                ...
            },
            "user_key": "test-user-key",
            "user_session_key": "test-session-key",
        }
        response = await client.post("/event", json=payload)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        detail = response.json().get("detail", {})
        assert "issue_key" in detail
        TestIssueLifecycle.issue_key = detail["issue_key"]
```

**Key conventions:**
- Tests are `async def` (pytest-asyncio auto mode)
- Class-based grouping by feature (`TestJobLifecycle`, `TestIssueLifecycle`)
- Sequential tests within class share state via class variables
- Fixtures injected via parameter names
- Assertions use plain `assert` with descriptive f-string messages
- Helper function pattern: `_issue_event()` extracts common payload construction

## Factory Fixtures (pytest)

All factories defined in root `testing/pytest/conftest.py` (function scope). They use raw `db.collection().insert()` -- never event classes.

**Available factories (FACT-01 through FACT-14):**

| Fixture | Purpose | Returns |
|---------|---------|---------|
| `create_user` | User documents with configurable scope | dict with `_key`, `username`, `scope`, etc. |
| `create_product` | Product + Phase + Operation + Step documents | dict with `product`, `phases`, `operations`, `steps`, `product_key` |
| `create_bom` | BOM edges between products | edge dict with `_from`, `_to`, `quantity` |
| `create_work_order` | WorkOrder linked to product | dict with `_key`, `wo_code`, `product_key`, `status`, etc. |
| `create_job` | Job linked to work order and phase | dict with `_key`, `job_code`, `wo_key`, `phase_key`, `status` |
| `create_batch` | Batch linked to job | dict with `_key`, `job_key`, `phase_key`, `status`, `active_qt` |
| `create_work_session` | WorkSession linked to batch | dict with `_key`, `batch_key`, `status`, `operator_key` |
| `create_position` | Inventory position documents | dict with `_key`, `location_key`, `product_key`, `quantity` |
| `create_serial` | Serial number documents | dict with `_key`, `code`, `product_key`, `status` |
| `create_production_graph` | Complete domain graph (user + product + WO + job + batch) | nested dict with all created docs |
| `create_issue` | Issue documents | dict with `_key`, `type_key`, `critical`, `linked_to`, etc. |
| `create_custom_field` | CustomField documents | dict with `_key`, `type`, `name`, `required` |
| `seed_config` | Config document seeding | mutates Config collection |

**Factory usage pattern:**
```python
def test_job_lifecycle(self, db, client, auth_headers, create_production_graph):
    # Create a complete domain graph
    g = create_production_graph()
    auth_headers("operator production")
    
    # Use created documents
    # g["user"], g["product"], g["work_order"], g["job"], g["target_phase"], etc.
    
    payload = {"event_type": "JOB_STARTED", ...}
    response = await client.post("/event", json=payload)
```

**Factory internals:**
- `_key()`: generates 8-char UUID prefix for document `_key` fields
- `_now()`: returns current UTC datetime as ISO 8601 string
- All factories return the inserted document dict (including `_key`)
- No ORM; raw Pydantic serializer integration via `ArangoClient(serializer=encoder)`

**Example: create_user (FACT-01)**
```python
@pytest.fixture
def create_user(db):
    """FACT-01: User factory — creates users with configurable scope strings."""
    def _create(
        scope: str = "operator production admin quality warehouse",
        username: str = None,
        **overrides,
    ):
        key = _key()
        doc = {
            "_key": key,
            "username": username or f"test-user-{key}",
            "name": "Test",
            "surname": "User",
            "active": True,
            # Static bcrypt hash for password 'test'
            "psw_hash": "$2b$12$LJ3m4ys3HIssFIGMqx0E3OIq2GRNyGeUxBRjLJSAVaKSrv2VMQHIS",
            "scope": scope,
            "site_key": "0",
            "reset_password": False,
            "trash": False,
            **overrides,
        }
        db.collection("User").insert(doc)
        return doc

    return _create
```

## Frontend Component Tests (Vitest)

**Setup:**
- Vitest 4.1.0 with `happy-dom` environment (no Chromium required)
- Config: `webapps/main/vitest.component.config.js`
- Globals enabled (no explicit imports of `describe`, `it`, `expect`, `beforeEach`)

**Test structure:**
```javascript
import { setActivePinia, createPinia } from 'pinia';
import { beforeEach, describe, expect, it } from 'vitest';
import { useRightDrawerStore } from './rightDrawer.js';

describe('useRightDrawerStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('initializes isOpen to false', () => {
    const store = useRightDrawerStore();
    expect(store.isOpen).toBe(false);
  });

  it('open() sets isOpen to true', () => {
    const store = useRightDrawerStore();
    store.open();
    expect(store.isOpen).toBe(true);
  });
});
```

**Patterns:**
- Always initialize Pinia with `setActivePinia(createPinia())` in `beforeEach()`
- Test store state, getters, and actions directly
- No mocking of API calls (test stores in isolation)

## Shared Assertion Helpers

**Location:** `testing/pytest/tests/helpers.py`

```python
from tests.helpers import assert_event_dispatched

# Verify a child event was stored in the Event collection
event_doc = assert_event_dispatched(db, "BATCH_COMPLETED", job_key=job["_key"])
```

## Mocking

**What is mocked:**
- NATS messaging (`publish_sync` -> noop) -- session scope, automatic (avoids real broker requirement)
- WeasyPrint native library -- stubbed at module level before imports (GTK not available in test env)
- Auth tokens -- `verify_token` dependency override per test via `app.dependency_overrides`

**What is NOT mocked:**
- ArangoDB -- real container via testcontainers (testing principle #4: "Real database in tests")
- FastAPI app -- tested in-process via ASGI transport
- Event system -- events tested through real `BaseEvent.save()` pipeline
- Business logic in `apply()` methods -- runs against real DB transactions
- Pydantic model validation -- validated against real schema

## Playwright E2E Tests

**Config:** `testing/playwright/playwright.config.js`
- Timeout: 60s per test
- Workers: 1 (sequential -- journeys may share state)
- Browser: Chromium only
- Screenshots: on failure only
- Base URL: `PLAYWRIGHT_BASE_URL` env var (default `http://localhost`)

**Prerequisites:**
- Full stack running: `docker-compose up`
- Browsers installed: `npm run install-browsers`
- Environment: `PLAYWRIGHT_USERNAME`, `PLAYWRIGHT_PASSWORD`, `PLAYWRIGHT_BASE_URL` (optional)

**Journey specs (4 critical paths):**
- `login_to_batch_complete.spec.js` -- E2E-01: Login -> batch list -> start job -> complete batch
- `stock_receipt.spec.js` -- E2E-03: Inventory -> stock receipt movement
- `work_order_creation.spec.js` -- E2E-02: Create work order flow
- `traceability_journey.spec.js` -- Serial traceability end-to-end

**Pattern:**
```javascript
test.describe('Journey Name (E2E-XX)', () => {
  test('step description', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    // ... interact and assert
  });
});
```

## Locust Load Tests

**Location:** `testing/locust/`

**Scenarios:**
- `production_queries.py` -- supervisor dashboard reads (GET work orders, jobs, queues)
- `inventory_movement.py` -- inventory movement throughput
- `batch_completion.py` -- batch completion event throughput

**Pattern:**
```python
class BatchCompletionUser(HttpUser):
    """Simulate an operator checking jobs and submitting batch updates."""
    host = os.environ.get("PROGRESS_TEST_HOST", "http://localhost:8000")
    wait_time = between(0.5, 2.0)

    def on_start(self):
        """Authenticate and store token for subsequent requests."""
        username = os.environ.get("PROGRESS_LOAD_USER", "admin")
        password = os.environ.get("PROGRESS_LOAD_PASSWORD", "changeme")

        resp = self.client.post("/auth", data={"username": username, "password": password})
        if resp.status_code == 200:
            token = resp.json().get("access_token", "")
            self.client.headers.update({"Authorization": f"Bearer {token}"})

    @task(3)
    def list_work_orders(self):
        """Read: list all active work orders."""
        self.client.get("/work-order")

    @task(1)
    def get_search_opts(self):
        """Read: fetch work order search options."""
        self.client.get("/work-order-search-opts")
```

**Run command:**
```bash
locust -f testing/locust/batch_completion.py --headless -u 10 -r 2 --run-time 30s --host http://localhost:8000
```

## CI/CD Integration

**GitLab CI:** `.gitlab-ci.yml`
- **NO test stages in CI pipeline** -- CI only builds Docker images on version tags (`v*.*.*`)
- Tests run locally or in dev environments, not in automated pipeline

## Coverage

**Requirements:** None enforced -- no coverage thresholds configured

**Tool:** pytest-cov available in dependencies

**Current coverage state:**
- Backend endpoints: partial -- production, batch, movement, serial domains have tests
- Backend events: tested indirectly through HTTP API and some direct event tests
- Backend utilities: no unit tests
- Frontend: no test coverage (webpack + Vitest setup exists but no tests written)
- E2E: 4 Playwright journey specs covering critical paths

## Test Types Summary

| Type | Framework | Count | Isolation |
|------|-----------|-------|-----------|
| Backend integration | pytest + testcontainers | ~15 test files | Full (truncate after each) |
| API fuzzing | Schemathesis | 1 test file | Per-request |
| Frontend component | Vitest + happy-dom | ~3 test files | Per-test (fresh Pinia) |
| E2E browser | Playwright | 4 spec files | Shared state (sequential) |
| Load testing | Locust | 3 scenario files | N/A |

---

*Testing analysis: 2026-05-08*
