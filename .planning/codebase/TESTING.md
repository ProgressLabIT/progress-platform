# Testing Patterns

**Analysis Date:** 2026-04-15

## Test Framework

**Backend Integration Tests:**
- pytest >= 9.0 with pytest-asyncio (auto mode)
- testcontainers >= 4.14 for real ArangoDB 3.11
- httpx with ASGITransport for in-process FastAPI testing
- Config: `testing/pytest/pyproject.toml`

**API Fuzzing:**
- Schemathesis >= 4.15 for OpenAPI-driven property-based testing
- Tests at `testing/pytest/tests/api/test_schemathesis.py`

**E2E Browser Tests:**
- Playwright (JS) with Chromium
- Config: `testing/playwright/playwright.config.js`
- Requires full stack running at `http://localhost`

**Load Testing:**
- Locust >= 2.0
- Scenarios at `testing/locust/` (production queries, inventory movements, batch completion)

**Frontend Unit Tests:**
- None -- `test` script is a no-op. No vitest or jest config exists.

**Run Commands:**
```bash
# Backend integration tests (from testing/pytest/)
uv run pytest                          # Run all tests
uv run pytest tests/production/        # Run domain-specific tests
uv run pytest -k "test_job_started"    # Run by name match
uv run pytest --cov                    # With coverage (pytest-cov)

# E2E tests (from testing/playwright/)
npm test                               # All journeys
npm run test:login                     # Single journey

# Load tests
locust -f testing/locust/production_queries.py --headless -u 10 -r 2 --run-time 30s --host http://localhost:8000
```

## Test File Organization

**Location:** All tests in `testing/` directory -- NOT co-located with source code.

**Structure:**
```
testing/
├── pytest/
│   ├── pyproject.toml                    # pytest config, dependencies
│   ├── conftest.py                       # Infrastructure fixtures + factory fixtures (43KB)
│   ├── conftest_helpers/
│   │   └── schema.py                     # ArangoDB schema initialization
│   ├── tests/
│   │   ├── conftest.py                   # Minimal (factories registered in root conftest)
│   │   ├── helpers.py                    # Shared assertion helpers
│   │   ├── api/
│   │   │   ├── test_auth.py              # Auth endpoint tests
│   │   │   ├── test_openapi_audit.py     # OpenAPI schema validation
│   │   │   └── test_schemathesis.py      # Property-based API fuzzing
│   │   ├── batch/
│   │   │   ├── test_batch_completed_api.py    # HTTP API batch tests
│   │   │   └── test_batch_completed_direct.py # Direct event tests
│   │   ├── collaboration/
│   │   │   ├── test_issues.py
│   │   │   └── test_messages.py
│   │   ├── factories/
│   │   │   └── test_factory_smoke.py     # Validates factory fixtures produce valid docs
│   │   ├── infrastructure/
│   │   │   └── test_harness_smoke.py     # Validates test infrastructure itself
│   │   ├── movement/
│   │   │   ├── test_movement_completed.py
│   │   │   └── test_movement_with_serials.py
│   │   ├── production/
│   │   │   ├── test_batch_state.py
│   │   │   ├── test_job_lifecycle.py
│   │   │   └── test_work_orders.py
│   │   ├── progress/                     # (exists, contents TBD)
│   │   ├── serial/                       # (exists, contents TBD)
│   │   └── step/                         # (exists, contents TBD)
├── playwright/
│   ├── playwright.config.js
│   ├── login_to_batch_complete.spec.js
│   ├── stock_receipt.spec.js
│   ├── traceability_journey.spec.js
│   └── work_order_creation.spec.js
└── locust/
    ├── batch_completion.py
    ├── inventory_movement.py
    └── production_queries.py
```

**Naming:**
- Test files: `test_{domain}_{feature}.py`
- Test classes: `TestFeatureName` (e.g., `TestJobLifecycle`, `TestCoreFactories`)
- Test methods: `test_{scenario}_returns_{expected}` or `test_{scenario}_{outcome}`
- Playwright specs: `{journey_name}.spec.js`

## Test Infrastructure (pytest)

**ArangoDB Container (session scope):**
- Real ArangoDB 3.11 via testcontainers -- no mocks
- Started once per session, shared across all tests
- Schema initialized via `testing/pytest/conftest_helpers/schema.py`
- Fixture: `arango_container` in `testing/pytest/conftest.py`

**Database Override (session scope):**
- Module-level `db` singleton in `utils.db` is monkey-patched to point at testcontainer
- All modules that captured `from utils.db import db` at import time are also patched
- Fixture: `db` in `testing/pytest/conftest.py`

**NATS Mock (session scope):**
- `publish_sync` replaced with noop lambda across all modules that import it
- `connect` and `drain` mocked to prevent real NATS connections
- Fixture: `mock_nats` in `testing/pytest/conftest.py`

**WeasyPrint Stub:**
- Stubbed at import time (before any backend module loads) since it requires native GTK libraries
- `sys.modules.setdefault("weasyprint", ...)` with dummy HTML/CSS classes

**ASGI Test Client (session scope):**
- `httpx.AsyncClient` with `ASGITransport(app=app)` -- tests FastAPI in-process
- Fixture: `client` in `testing/pytest/conftest.py`

**Auth Headers (function scope):**
- Factory fixture returning configurable JWT auth headers
- Overrides `verify_token` dependency with test `TokenData`
- Usage: `auth_headers("operator production")` -- space-separated scope string
- Fixture: `auth_headers` in `testing/pytest/conftest.py`

**Collection Truncation (function scope, autouse):**
- After each test, truncates all non-system collections except `Config`, `Counter`, `CustomField`, `Queue`, `is_in_position`
- Edge collections truncated first, then document collections
- Config defaults captured at session start and restored after each test
- Fixture: `truncate_collections` in `testing/pytest/conftest.py`

## Test Structure Pattern

**BDD-style docstrings noting provenance:**
```python
class TestJobLifecycle:
    """HTTP API tests for job lifecycle events via POST /event."""

    async def test_job_started_returns_200(
        self, client, auth_headers, create_production_graph
    ):
        """Given a job in 'created' stage with an assigned operator
        When POST /event is called with JOB_STARTED
        Then the response status is 200 and contains job_data.
        Migrated from: production.robot 'Start job' test case.
        """
        g = create_production_graph()
        auth_headers("operator production")

        payload = _event_payload("JOB_STARTED", g)
        response = await client.post("/event", json=payload)

        assert response.status_code == 200
        detail = response.json().get("detail", {})
        assert "job_data" in detail
```

**Key conventions:**
- Tests are `async def` (pytest-asyncio auto mode handles event loop)
- Class-based grouping by feature (`TestJobLifecycle`, `TestCoreFactories`)
- Fixtures injected via parameter names -- no `@pytest.mark.usefixtures` unless autouse
- Assertions use plain `assert` with descriptive f-string messages

## Factory Fixtures

All factories defined in root `testing/pytest/conftest.py` (function scope). They use raw `db.collection().insert()` -- never event classes.

**Available factories:**

| Fixture | ID | Purpose |
|---------|-----|---------|
| `create_user` | FACT-01 | User documents with configurable scope |
| `create_product` | FACT-02 | Product + Phase + Operation + Step documents |
| `create_bom` | FACT-03 | BOM edges between products |
| `create_work_order` | FACT-04 | WorkOrder linked to product |
| `create_job` | FACT-05 | Job linked to work order and phase |
| `create_batch` | FACT-06 | Batch linked to job |
| `create_work_session` | FACT-07 | WorkSession linked to batch |
| `create_position` | FACT-08 | Inventory position documents |
| `create_serial` | FACT-09 | Serial number documents |
| `create_production_graph` | FACT-10 | Complete domain graph (user + product + WO + job + batch) |
| `create_issue` | FACT-11 | Issue documents |
| `create_custom_field` | FACT-12 | CustomField documents |
| `seed_config` | FACT-14 | Config document seeding |

**Factory usage pattern:**
```python
def test_something(self, db, client, auth_headers, create_production_graph):
    g = create_production_graph()  # Returns dict with all created docs
    auth_headers("operator production")
    # g["user"], g["product"], g["work_order"], g["job"], g["target_phase"], etc.
```

**Factory internals:**
- `_key()` generates 8-char UUID prefix for document `_key` fields
- `_now()` returns UTC ISO 8601 timestamp
- All factories return the inserted document dict (including `_key`)

## Shared Assertion Helpers

**Location:** `testing/pytest/tests/helpers.py`

```python
from tests.helpers import assert_event_dispatched

# Verify a child event was stored in the Event collection
event_doc = assert_event_dispatched(db, "BATCH_COMPLETED", job_key=job["_key"])
```

## Mocking

**What is mocked:**
- NATS messaging (`publish_sync` -> noop) -- session scope, automatic
- WeasyPrint native library -- stubbed at module level before imports
- Auth tokens -- `verify_token` dependency override per test

**What is NOT mocked:**
- ArangoDB -- real container via testcontainers (design principle)
- FastAPI app -- tested in-process via ASGI transport
- Event system -- events are tested through the real `BaseEvent.save()` pipeline
- Business logic in `apply()` methods -- runs against real DB transactions

## Playwright E2E Tests

**Config:** `testing/playwright/playwright.config.js`
- Timeout: 60s per test
- Workers: 1 (sequential -- journeys may share state)
- Browser: Chromium only
- Screenshots: only on failure
- Base URL: `PLAYWRIGHT_BASE_URL` env var (default `http://localhost`)

**Prerequisites:**
- Full stack running (docker-compose)
- `PLAYWRIGHT_USERNAME` and `PLAYWRIGHT_PASSWORD` env vars

**Journey specs:**
- `login_to_batch_complete.spec.js` -- E2E-01: Login -> select WO -> start job -> complete batch
- `stock_receipt.spec.js` -- inventory receipt flow
- `traceability_journey.spec.js` -- serial traceability end-to-end
- `work_order_creation.spec.js` -- WO creation flow

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
- `production_queries.py` -- supervisor dashboard reads (GET work orders, jobs, queues)
- `inventory_movement.py` -- inventory movement throughput
- `batch_completion.py` -- batch completion event throughput

**Pattern:**
```python
class ProductionQueriesUser(HttpUser):
    host = os.environ.get("PROGRESS_TEST_HOST", "http://localhost:8000")
    wait_time = between(0.3, 1.5)

    def on_start(self):
        # Authenticate and cache context
        resp = self.client.post("/auth", data={...})
        self.client.headers.update({"Authorization": f"Bearer {token}"})

    @task
    def get_work_orders(self):
        self.client.get("/work-order")
```

## CI/CD Integration

**GitLab CI:** `.gitlab-ci.yml`
- NO test stages in CI pipeline -- CI only builds Docker images on version tags (`v*.*.*`)
- Tests are run locally or in dev environments, not as part of the automated pipeline

## Coverage

**Requirements:** None enforced -- no coverage thresholds configured
**Tool:** pytest-cov available in dependencies but no `.coveragerc` or `[tool.coverage]` config

**Current coverage state:**
- Backend endpoints: partial -- production, batch, movement, serial domains have tests
- Backend events: tested indirectly through HTTP API and some direct event tests
- Backend utilities: no unit tests
- Frontend: no test coverage at all
- E2E: 4 Playwright journey specs covering critical paths

## Test Types Summary

| Type | Framework | Count | Isolation |
|------|-----------|-------|-----------|
| Backend integration | pytest + testcontainers | ~15 test files | Full (truncate after each) |
| API fuzzing | Schemathesis | 1 test file | Per-request |
| E2E browser | Playwright | 4 spec files | Shared state (sequential) |
| Load testing | Locust | 3 scenario files | N/A |
| Frontend unit | None | 0 | N/A |

---

*Testing analysis: 2026-04-15*
