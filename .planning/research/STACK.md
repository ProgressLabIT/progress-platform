# Technology Stack

**Project:** Progress Platform Test Suite
**Researched:** 2026-04-08
**Overall confidence:** HIGH (versions verified via PyPI/npm search results)

---

## Recommended Stack

### Python Test Runner & Core

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| uv | 0.11.4 | Package/project manager | 10–100x faster than pip; lockfile support via uv.lock; pyproject.toml-native; replaces requirements.txt for the test suite. The existing backend keeps pip — uv is only for the new test project. |
| pytest | ^9.0.2 | Test runner | Current stable (9.0.2, April 2026). The entire Python test ecosystem converges on pytest. No reason to deviate. |
| pytest-asyncio | ^1.3.0 | Async test support | Current stable (1.3.0, Nov 2025). Required because FastAPI endpoints are `async def`. Use `asyncio_mode = "auto"` in pyproject.toml to avoid decorating every test. |
| pytest-cov | ^7.0.0 | Coverage reporting | Current stable (7.0.0, Nov 2025). Standard pytest coverage plugin; LCOV output for GitLab integration later. |

### Backend Integration Testing

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| httpx | ^0.28.1 | Async HTTP test client | Already a backend dependency (`httpx==0.*` in requirements.txt). FastAPI's official docs recommend `httpx.AsyncClient` over `TestClient` for async endpoints. Zero additional overhead. |
| testcontainers[arangodb] | ^4.14.2 | Real ArangoDB in tests | The testing strategy explicitly mandates real database — no mocks. Testcontainers 4.x bundles ArangoDB support as an extra (`pip install testcontainers[arangodb]`); the extra installs `python-arango` automatically. Use `arangodb:3.11` image to match production. Session-scoped container fixture in `conftest.py` for speed; function-scoped truncation for isolation. |
| python-arango | ^8.0 | ArangoDB client | Already a production dependency. Testcontainers[arangodb] extra pulls it in; used directly in fixture helpers to create test databases and seed collections. |
| factory-boy | NOT USED | — | Document databases don't benefit from ORM-oriented factories. Per `km/testing/strategy.md`: use plain fixture functions that insert documents via python-arango. |

### API Fuzzing

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| schemathesis | ^4.13.0 | OpenAPI property-based fuzzing | Built on Hypothesis; generates test inputs from the OpenAPI schema FastAPI produces. Use `schemathesis.openapi.from_asgi("/openapi.json", app)` for direct ASGI integration (no server needed). **Prerequisite:** complete OpenAPI spec audit must precede fuzzing — schemathesis only finds bugs that the schema exposes. |

### Load Testing

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| locust | ^2.43.4 | Load and concurrency testing | Current stable (2.43.4, April 2026). Python-native: scenarios are plain Python classes, no XML/YAML. Headless mode (`--headless`) for CI. Built-in HTML reports. FastAPI + Locust is a documented, well-tested pairing in the community. |

### Frontend Unit Testing

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| vitest | ^3.x | Component test runner | Vite-native; shares the same transform pipeline as `@quasar/app-vite@2`. Vitest 3 requires Vite 5, which the project already uses. Jest would require a separate Babel transform. |
| @vue/test-utils | ^2.x | Vue component mounting | Official Vue testing library. `mount()` / `shallowMount()` with full Composition API and `<script setup>` support. |
| @quasar/quasar-app-extension-testing-unit-vitest | >=2.0.0 | Quasar + Vitest glue | Provides `installQuasarPlugin()` which configures @vue/test-utils to boot Quasar on every mount. Without this, Quasar components throw at test time. Install via `quasar ext add @quasar/testing-unit-vitest`. Requires `@quasar/app-vite` >= 2.0.0 (already satisfied). |

### End-to-End Testing

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| playwright (Node) | ^1.52.x | E2E browser automation | Current Playwright stable is 1.58.x on PyPI for Python; use the Node/TypeScript version since the webapp is TypeScript-first. Native async/await, multi-browser (Chromium/Firefox/WebKit), multi-tab support for collaborative features. Explicitly chosen over Cypress in `km/testing/strategy.md`. |
| @playwright/test | ^1.52.x | Playwright test runner | Bundled with Playwright; handles browser lifecycle, parallel workers, HTML reporter. |

---

## Project Structure for the Test Suite

```
tests/                            # New test suite root (alongside existing testing/)
  pyproject.toml                  # uv-managed Python project for backend tests
  uv.lock                         # Lockfile committed to repo
  conftest.py                     # ArangoDB container, HTTP client, auth fixtures
  unit/
    test_validators.py
    test_event_logic.py
  integration/
    test_step_completed.py
    test_batch_completed.py
    test_progress_override.py
    test_movement_completed.py
    test_serial_events.py
    test_collaboration_events.py
  fuzzing/
    test_schemathesis.py          # schemathesis from_asgi parametrize suite
  load/
    locustfile.py                 # Locust scenarios

webapps/main/test/vitest/         # Vitest tests (inside webapp, managed by quasar ext)
  __tests__/
    ProgressBtn.spec.ts
    WorkSessionSteps.spec.ts

testing/playwright/               # E2E tests (existing dir, new files)
  tests/
    production_flow.spec.ts
    work_order_creation.spec.ts
    stock_movement.spec.ts
  playwright.config.ts
```

---

## pyproject.toml for Backend Tests

```toml
[project]
name = "progress-platform-tests"
version = "0.1.0"
requires-python = "==3.11.*"
dependencies = [
    "httpx>=0.28.1",
    "python-arango>=8.0",
]

[dependency-groups]
test = [
    "pytest>=9.0",
    "pytest-asyncio>=1.3",
    "pytest-cov>=7.0",
    "testcontainers[arangodb]>=4.14",
    "schemathesis>=4.13",
    "locust>=2.43",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["unit", "integration", "fuzzing"]

[tool.coverage.run]
source = ["backend/api"]
omit = ["*/tests/*"]
```

---

## Key Configuration Patterns

### ArangoDB Testcontainer (conftest.py)

```python
import pytest
from testcontainers.arangodb import ArangoDbContainer
from arango import ArangoClient

@pytest.fixture(scope="session")
def arango_container():
    with ArangoDbContainer("arangodb:3.11") as container:
        yield container

@pytest.fixture(scope="session")
def arango_client(arango_container):
    return ArangoClient(hosts=arango_container.get_connection_url())

@pytest.fixture(scope="session")
def test_db(arango_client):
    sys_db = arango_client.db(username="root", password="passwd")
    sys_db.create_database("progress_test")
    db = arango_client.db("progress_test", username="root", password="passwd")
    yield db
    sys_db.delete_database("progress_test")

@pytest.fixture(autouse=True)
def truncate_collections(test_db):
    """Truncate all collections between tests for isolation."""
    yield
    for collection in test_db.collections():
        if not collection["system"]:
            test_db.collection(collection["name"]).truncate()
```

**Why session scope for container:** Starting ArangoDB takes 5–15 seconds. Session scope starts it once; collection truncation between tests provides isolation without the startup cost.

### Schemathesis ASGI Pattern (fuzzing/test_schemathesis.py)

```python
import schemathesis
from backend.api.main import app  # import the FastAPI app directly

schema = schemathesis.openapi.from_asgi("/openapi.json", app)

@schema.parametrize()
def test_api_fuzzing(case):
    response = case.call_asgi()
    case.validate_response(response)
```

**Why from_asgi over from_url:** Eliminates network overhead; shares the same database fixtures; no server process to manage.

### Quasar + Vitest (test file header)

```typescript
import { installQuasarPlugin } from "@quasar/quasar-app-extension-testing-unit-vitest";
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import ProgressBtn from "src/components/ProgressBtn.vue";

installQuasarPlugin();

describe("ProgressBtn", () => {
  it("emits confirm when clicked", async () => {
    const wrapper = mount(ProgressBtn, { props: { label: "Complete Step" } });
    await wrapper.find("button").trigger("click");
    expect(wrapper.emitted("confirm")).toBeTruthy();
  });
});
```

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Package manager | uv | poetry | uv is faster and simpler; poetry's lockfile format is less standard; uv is now the ecosystem default for new projects |
| Package manager | uv | pip + requirements.txt | No lockfile; slow resolution; can't manage Python versions |
| DB in tests | testcontainers (real DB) | mocks / mongomock-arango | Strategy doc explicitly forbids mocks; they drift from real query behavior and miss transaction bugs |
| DB in tests | testcontainers | dedicated test DB server | testcontainers is fully isolated and CI-friendly; dedicated server has shared state risk |
| Frontend testing | vitest | jest | Vitest shares Vite's transform pipeline; jest requires separate Babel config; project already uses Vite |
| Frontend testing | vitest | cypress component | Slower; heavier; Playwright already covers E2E; Vitest is the right tool for unit/component |
| E2E | playwright | cypress | Already decided in km/testing/strategy.md: native async, multi-browser, multi-tab support |
| Load testing | locust | k6 | locust is Python-native; test scenarios can reuse Python fixture logic; k6 would require JS duplication |
| Load testing | locust | JMeter | JMeter is XML-based and heavyweight; locust is scriptable and CI-friendly |
| API fuzzing | schemathesis | restler | schemathesis is better integrated with pytest and Hypothesis; active development; from_asgi avoids server setup |
| Async fixtures | pytest-asyncio | anyio | pytest-asyncio is the standard for FastAPI; anyio offers marginal benefit for this stack |

---

## What NOT to Use

**factory_boy:** The existing `km/testing/strategy.md` explicitly calls this out. ArangoDB is a document DB — there's no ORM layer. Plain fixture functions that insert documents directly are simpler and more readable.

**Mocha + Supertest:** The existing fragmented suite that's being replaced. Do not add new tests there.

**Robot Framework:** In use for some BDD flows but being deprecated. The new suite uses pytest docstrings for human-readable intent without the step-definition ceremony.

**Cypress:** Replaced by Playwright for E2E. Do not add new Cypress tests.

**mock / unittest.mock for ArangoDB:** The strategy mandates real database. Mock DB calls hide the bugs that matter (data integrity, transaction behavior, query correctness).

**pytest-django style DB rollbacks:** ArangoDB transactions work differently from SQL rollbacks. Use collection truncation for isolation, not transaction rollbacks.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| pytest / pytest-asyncio / pytest-cov | HIGH | Versions verified via PyPI search results (April 2026) |
| uv | HIGH | Version 0.11.4 verified as current release (April 8, 2026) |
| testcontainers[arangodb] | HIGH | Version 4.14.2 verified; ArangoDB extra confirmed in official docs |
| httpx | MEDIUM | 0.28.1 confirmed as latest; no 2026 update found — may be stable at this version |
| schemathesis | HIGH | Version 4.13.0 verified; from_asgi pattern confirmed in official docs |
| locust | HIGH | Version 2.43.4 verified as current (April 1, 2026 release) |
| vitest + @quasar testing ext | MEDIUM | Vitest 3.x confirmed; Quasar ext compatibility requires verifying against `@quasar/app-vite` version in package.json before install |
| playwright | MEDIUM | 1.58.0 confirmed for Python; Node version likely aligned — verify exact Node package version at install time |

---

## Sources

- [testcontainers PyPI](https://pypi.org/project/testcontainers/) — version 4.14.2, ArangoDB extra
- [testcontainers ArangoDB docs](https://testcontainers-python.readthedocs.io/en/latest/modules/arangodb/README.html) — ArangoDbContainer usage
- [testcontainers modules page](https://testcontainers.com/modules/arangodb/) — official module listing
- [schemathesis PyPI](https://pypi.org/project/schemathesis/) — version 4.13.0
- [schemathesis pytest tutorial](https://schemathesis.readthedocs.io/en/stable/tutorials/pytest/) — from_asgi pattern
- [locust PyPI / docs](https://docs.locust.io/en/stable/installation.html) — version 2.43.4
- [pytest PyPI](https://pypi.org/project/pytest/) — version 9.0.2
- [pytest-asyncio PyPI](https://pypi.org/project/pytest-asyncio/) — version 1.3.0
- [pytest-cov changelog](https://pytest-cov.readthedocs.io/) — version 7.0.0
- [uv PyPI](https://pypi.org/project/uv/) — version 0.11.4
- [playwright Python PyPI](https://pypi.org/project/playwright/) — version 1.58.0
- [Quasar Vitest extension npm](https://www.npmjs.com/package/@quasar/quasar-app-extension-testing-unit-vitest) — install pattern
- [Quasar testing docs](https://testing.quasar.dev/packages/unit-vitest/) — installQuasarPlugin usage
- [FastAPI async tests](https://fastapi.tiangolo.com/advanced/async-tests/) — httpx.AsyncClient pattern
