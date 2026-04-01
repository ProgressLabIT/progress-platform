# Testing Strategy

## Principles

1. **Spec-first development.** Every new feature starts with a written specification (acceptance criteria in markdown), then tests, then implementation. Tests are the executable form of the spec.
2. **Grow coverage from the frontier.** Don't backfill tests on existing code. Write tests for new features and, when touching existing code, cover the parts you modify (boy scout rule).
3. **No BDD framework.** We want BDD's discipline (human-readable intent, living documentation) without the ceremony of `.feature` files and step definitions. Pytest docstrings and markdown specs achieve this at lower maintenance cost.
4. **Real database in tests.** Use a dedicated ArangoDB test database, not mocks. Mocks drift from reality and hide the bugs that matter most — data integrity, query correctness, transaction behavior.
5. **AI-assisted loop.** The spec is the contract between human intent and AI implementation. AI generates tests from specs and writes code to pass them.

## Test Layers

### Layer 1 — Unit Tests

Pure functions, domain logic, data transformations. No I/O, no database.

- **Scope:** Utility functions, validators, data mapping, event logic that can be tested without a database.
- **Speed:** Milliseconds.
- **When to write:** Whenever logic is complex enough to have edge cases worth documenting.

### Layer 2 — Integration Tests (primary layer)

Full request/response cycles using `httpx.AsyncClient` against a seeded ArangoDB test database. This is where most testing effort goes.

Each test class maps to a feature. Docstrings describe the scenario in plain language — these serve as living documentation.

```python
class TestBatchRelease:
    """
    Feature: Batch Release
    A production batch can be released when all quality checks pass,
    making it available for downstream operations.
    """

    async def test_release_batch_with_passing_checks(self, client, seed_batch):
        """Given a batch with all quality checks passing,
        when the operator releases it,
        then status becomes RELEASED and a batch_released event is recorded."""
        response = await client.post(f"/batches/{seed_batch['_key']}/release")

        assert response.status_code == 200
        assert response.json()["status"] == "RELEASED"

    async def test_cannot_release_batch_with_failing_checks(self, client, seed_failing_batch):
        """Given a batch with a failing quality check,
        release must be rejected with a clear error."""
        response = await client.post(f"/batches/{seed_failing_batch['_key']}/release")

        assert response.status_code == 422
        assert response.json()["code"] == "QUALITY_CHECK_FAILED"
```

### Layer 3 — E2E Tests (future, sparse)

Playwright tests covering 5–10 critical user journeys. Not a full suite — only the paths where breakage would directly impact production users.

**Why Playwright over Cypress:**

- Native async/await, no automatic waiting magic to debug.
- Multi-browser support (Chromium, Firefox, WebKit) out of the box.
- Better support for multi-tab and multi-user scenarios (relevant for collaborative features).
- First-class API testing support — can mix API calls and UI interactions in the same test.

**Target journeys (initial candidates):**

- Login → navigate to production overview → start a job.
- Create a work order → assign BOM → release to production.
- Record a stock movement → verify inventory update.

E2E tests will not be implemented until the backend integration test infrastructure is solid and stable.

## The Feature Development Loop

```
1. SPEC   → Write acceptance criteria in specs/features/<name>.md
2. TESTS  → Generate pytest integration tests from the spec
3. RED    → Run tests, confirm they fail (contract is set)
4. CODE   → Write implementation to make tests pass
5. GREEN  → Tests pass, spec is now living documentation
6. COMMIT → Tests travel with the feature forever
```

### Spec Format

Specs live in `specs/features/` as markdown files. They define the feature context and acceptance criteria that directly map to test cases.

```markdown
# Feature: Work Order Release

## Context
Production managers release work orders to authorize shop floor execution.
A work order requires a valid BOM before it can be released.

## Acceptance Criteria
- AC1: A DRAFT work order with a valid BOM can be released → status becomes RELEASED
- AC2: A DRAFT work order without a BOM cannot be released → 422 with BOM_REQUIRED
- AC3: A non-DRAFT work order cannot be released → 409 with INVALID_TRANSITION
- AC4: Release creates a traceability event with timestamp and acting user
```

Each acceptance criterion becomes one or more test functions. The spec file is the source of truth; the tests are its executable form.

## Tooling

| Concern | Tool | Notes |
|---|---|---|
| Test runner | `pytest` | With `pytest-asyncio` for async test support |
| API testing | `httpx.AsyncClient` | FastAPI's native async test client |
| DB isolation | Test ArangoDB database | Created in `conftest.py`, seeded per-test or per-class, torn down after |
| Seed data | Fixture functions | Simple functions that insert documents via `python-arango`. No ORM, no `factory_boy` — document DB doesn't benefit from ORM-oriented factories |
| Coverage | `pytest-cov` | Track coverage, don't chase 100% |
| E2E (future) | Playwright | When backend test infra is stable |

## Project Structure

```
specs/
  features/                    # Markdown specs (source of truth for behavior)
    work_order_lifecycle.md
    batch_release.md

backend/api/
  tests/
    conftest.py                # Test client, DB lifecycle, auth fixtures, seed helpers
    unit/
      test_validators.py
      test_transformations.py
    integration/
      test_work_orders.py
      test_batches.py
      test_production.py

testing/                       # E2E (future)
  playwright/
    tests/
      production_flow.spec.ts
    playwright.config.ts
```

## Test Database Strategy

- A dedicated `progress_test` ArangoDB database is created by `conftest.py` at session start.
- Collections and graphs are initialized to mirror the production schema.
- Each test class or module gets a clean state via setup/teardown that truncates collections (faster than recreating the database).
- Tests that modify data must be isolated — no test should depend on another test's side effects.

## What Not to Test

- Don't test framework behavior (FastAPI routing, Pydantic validation that's already declared in the model).
- Don't test trivial getters/setters or pass-through functions.
- Don't write E2E tests for flows that are already covered by integration tests unless the UI interaction itself is the risk.
- Don't mock the database. If a test needs data, seed it.

## Getting Started

Priority order for building the test infrastructure:

1. **`conftest.py`** — test client fixture with auth, ArangoDB test database lifecycle, basic seed data helpers. This is the most important file; everything depends on it.
2. **One integration test** — pick a simple existing endpoint, write 3–5 tests. This validates the infrastructure works end-to-end.
3. **First spec-driven feature** — use the full loop (spec → tests → implementation) for the next new feature.
