# Feature Landscape: Test Suite for Event-Sourced FastAPI + ArangoDB MES

**Domain:** Automated test suite for a manufacturing execution system
**Researched:** 2026-04-08
**Overall confidence:** HIGH — based on direct codebase analysis + verified sources

---

## Table Stakes

Features that must exist for the test suite to be useful. Missing any of these = test suite is not production-ready.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Real ArangoDB via testcontainers | Mocks cannot catch AQL query bugs, transaction scope issues, or collection constraint violations. Testing strategy principle #4 mandates this. | Med | `arangodb:3.11` image; one container per session, one DB per test class |
| Factory fixtures for domain object graphs | WorkOrder → Job → Batch → WorkSession → StepExecutionData are deeply interdependent. Static seeds break on model changes. | Med | Build with pytest fixtures + factory functions rather than factory_boy (no ORM to integrate with) |
| Test isolation (no shared state between tests) | Existing Mocha suite is order-dependent. This is the #1 cause of flaky CI tests. | Med | Use per-test-class DB setup/teardown or per-test DB prefix naming |
| StepCompletedEvent deep tests | Last-step cascade into BatchCompletedEvent is the most critical business rule. Already identified as primary regression vector. | High | Happy path + last-step trigger + no-last-step + form data + work session handling |
| BatchCompletedEvent deep tests | Single event spawns 5–10 child events: WorkSessionClosed, WIPRemoved/Declared, BatchReleased, SerialLinked/Released, MovementCompleted, JobClosed. Each branch must be tested. | High | Requires explicit test permutations per boolean flag: first_phase, last_phase, auto_new_batch, traceability_level, warehouse_management |
| HTTP API integration test layer | Tests must exercise the real HTTP path (endpoint → event → DB). Direct event instantiation alone misses endpoint validation and middleware behavior. | Med | Use `httpx.AsyncClient` with `ASGITransport`; test over real FastAPI app |
| Direct event instantiation test layer | Edge cases (e.g., idempotency, invalid states, quantity mismatches) are cheaper and faster to cover without HTTP overhead. | Med | Instantiate events directly with transaction fixture; assert DB state |
| Precondition enforcement tests | Endpoints raise `HTTPException(409)` for invalid state transitions (e.g., completing an already-closed job). These are business rules, not implementation details. | Low | Parameterize invalid states per event type |
| Pydantic schema validation tests | Endpoints return 422 on malformed input. Must be tested to catch schema drift. | Low | Use Schemathesis or manual parametrize |
| Transaction atomicity tests | If `apply()` raises mid-cascade, the entire transaction (including all child events) must roll back. ArangoDB multi-collection transactions need explicit verification. | High | Inject failures mid-apply; assert zero documents written |
| Pytest conftest.py with shared ArangoDB fixtures | All tests depend on a running ArangoDB instance. Fixture setup/teardown must be centralized and reusable. | Low | Session-scoped container, function-scoped or class-scoped DB collections |
| ProgressOverrideRequestedEvent tests | Admin event with inventory reversal, WIP management, and time redistribution. Documented in PROJECT.md as required. | High | Increase/decrease variants; WIP management; time redistribution; inventory reversal |
| MovementCompletedEvent tests | Receipt, shipment, adjustment, transfer, serial traceability, container transfer. Multiple movement types, each with distinct DB mutations. | High | Parameterize by `InventoryMovementType` |
| Serial event tests | SerialCreated, SerialUpdated, SerialLinked, SerialReleased. Traceability correctness is a regulatory concern in MES. | Med | Verify edge collection (`contains`) and serial status transitions |
| OpenAPI spec completeness audit | Schemathesis fuzzing only works if schema is complete. Endpoints currently lack input/output schemas in many places. | Med | Manual review pass; add missing schemas before fuzzing |
| Schemathesis API fuzzing | Property-based testing against the OpenAPI spec catches schema mismatches, unexpected 500s, and edge-case inputs automatically. | Med | Requires complete OpenAPI spec first |
| Vitest unit tests for ProgressBtn.vue | ProgressBtn handles step completion, batch declaration, serial management — all with multiple async dialogs. Untested UI state machine. | Med | Mount with @vue/test-utils; stub axios/pinia; test dialog flow and emit events |
| Vitest unit tests for WorkSessionSteps.vue | Step rendering and completion flow. Second most critical UI component per PROJECT.md. | Med | Mount with stubs; verify slot rendering and step state display |
| Playwright E2E tests for critical journeys | Login → job → batch complete; work order creation; stock movement. Smoke tests that the integrated system works end-to-end. | High | 3 critical paths; real browser; requires running backend |
| Locust load scenarios for critical endpoints | Concurrent event dispatch (especially BatchCompleted) can trigger race conditions in job queue. No current concurrency tests. | Med | Scenario: concurrent batch completions on same job; inventory movement under load |

---

## Differentiators

Features that go beyond the minimum and add meaningful confidence or developer experience.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Snapshot testing for event cascades | Pin the exact set of child events created by BatchCompletedEvent. Regressions in cascade shape are detected immediately without inspecting DB state. | Med | Store expected event_source edges as JSON snapshot; assert on structure |
| Parametrized permutation matrix for BatchCompletedEvent | Systematically cover all combinations of `first_phase`, `last_phase`, `auto_new_batch`, `traceability_level`, `warehouse_management`. Prevents subtle branch-missing bugs. | High | 2^5 = 32 combinations; use `pytest.mark.parametrize`; skip known-invalid combos |
| Idempotency regression tests | Event sourcing requires events to be replayable without side effects. Currently flagged as a gap in CONCERNS.md. Saves are not idempotent if applied twice. | High | Re-save same event; assert DB state unchanged or explicit idempotency check |
| Job queue race condition tests | CONCERNS.md flags concurrent queue operations as a known risk. Locust or pytest-asyncio concurrent tasks can reproduce the race. | High | Fire N concurrent StepCompleted events on same batch; assert single BatchCompleted emitted |
| Collaboration event tests | Issues, messages, tasks. Lower risk than production events but part of completeness. | Low | Basic CRUD coverage via HTTP API layer |
| AQL query correctness tests | `utils/production`, `utils/inventory`, `utils/serial` query helpers have zero test coverage. Direct AQL test fixtures validate query semantics. | Med | Create known dataset; execute AQL; assert returned shape |
| Mutation coverage via coverage.py + pytest-cov | Line coverage alone misses logic branches. Branch coverage (--cov-branch) with a threshold gate prevents coverage regression. | Low | Add to CI later; set minimum threshold at ~70% for event handlers |
| pytest-xdist parallel test execution | Event handler tests are DB-heavy and slow to run serially. Parallelizing across workers with isolated DBs cuts CI time significantly. | Med | Requires per-worker DB isolation (prefix by worker ID) |
| Playwright visual regression snapshots | Detects unintended UI layout changes in critical production screens. Useful if the Quasar version is ever bumped. | High | High maintenance cost; only worth it on stable screens |
| Contract testing (Pact or similar) | If external systems consume the API (e.g., ERP integrations), consumer-driven contracts prevent breaking changes. | High | Not needed now — PROJECT.md explicitly excluded Microcks. Revisit when external consumers exist. |

---

## Anti-Features

Features to explicitly NOT build in this milestone. Building these wastes time or creates maintenance burden without proportional value.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Mock ArangoDB (MagicMock, monkeypatch on DB calls) | Mocks cannot catch AQL syntax errors, transaction scope issues, or collection constraint violations. They create a false sense of coverage that breaks in production. | Use real ArangoDB via testcontainers. Accept the startup overhead. |
| Full test coverage backfill of all existing code | PROJECT.md explicitly excludes this. Boiling-the-ocean approach creates low-value tests and delays the milestone indefinitely. | Grow coverage from the critical event chain frontier. |
| Unit tests for `dhr.py` | 1,297-line file with mixed concerns, 30+ debug prints, and potential security issues. Testing it locks in bad design. | Refactor first, then test. Don't write tests around a known-bad architecture. |
| Cypress/Robot Framework for new test scenarios | New test scenarios added to the old fragmented stack extend a dead-end. Old tests are being deprecated organically. | Write all new tests in pytest (backend) + Vitest/Playwright (frontend). |
| Mobile warehouse app (Capacitor) testing | Out of scope per PROJECT.md. Capacitor adds native bridge complexity with low regression risk at current stage. | Focus on main webapp and backend. Revisit after core test suite is stable. |
| GitLab CI/CD pipeline integration | Out of scope per PROJECT.md. Adding CI before the test suite is stable creates noise. | Stabilize test suite first. CI integration is the follow-up milestone. |
| Load tests simulating 10K+ concurrent users | The system is a multi-tenant MES, not a consumer app. Realistic load is tens to hundreds of concurrent operators. Over-engineering load scenarios wastes time. | Locust scenarios should simulate realistic MES usage: <100 concurrent users, focused on batch completion and inventory movement. |
| Playwright tests for admin/config screens | Admin screens are low-traffic, change frequently, and have minimal business logic in the UI. High maintenance cost, low regression value. | Cover admin flows via API tests. Reserve Playwright for operator-facing critical journeys. |
| Microcks contract testing | Explicitly ruled out in PROJECT.md. No external API consumers identified yet. | Revisit when an ERP or external integration is confirmed. |

---

## Feature Dependencies

```
ArangoDB testcontainer fixture
  → factory fixtures (WorkOrder → Job → Batch → WorkSession → StepExecutionData)
    → StepCompletedEvent tests
      → BatchCompletedEvent tests (cascade from StepCompleted)
        → MovementCompletedEvent tests (child of BatchCompleted)
        → Serial event tests (child of BatchCompleted)
        → WIP event tests (child of BatchCompleted)
        → JobClosedEvent tests (child of BatchCompleted)

OpenAPI spec audit
  → Schemathesis fuzzing (requires complete spec)

Vitest setup
  → ProgressBtn.vue unit tests
  → WorkSessionSteps.vue unit tests

Playwright setup
  → Critical E2E journeys (requires running backend)

BatchCompletedEvent tests (partial)
  → ProgressOverrideRequestedEvent tests (requires understanding of batch/job state)

HTTP API integration test layer
  → All endpoint-level tests
  → Schemathesis (can share the same app fixture)
```

---

## MVP Recommendation

Prioritize in this order:

1. **testcontainers ArangoDB infrastructure + conftest** — Everything depends on this.
2. **Factory fixtures for full domain object graph** — Must exist before any event tests.
3. **StepCompletedEvent deep tests** — The most-exercised production path. Entry point to the cascade.
4. **BatchCompletedEvent deep tests** — The most complex event. Most regression risk. Requires systematic permutation of branches.
5. **HTTP API integration layer setup** — Unlocks endpoint-level tests across all domains.
6. **ProgressOverrideRequestedEvent + MovementCompletedEvent tests** — Admin and inventory correctness.
7. **Serial event tests** — Traceability correctness.
8. **OpenAPI spec audit → Schemathesis fuzzing** — Schema completeness pays off in long-term quality.
9. **Vitest: ProgressBtn.vue + WorkSessionSteps.vue** — Frontend unit tests.
10. **Playwright: 3 critical E2E journeys** — Integration smoke tests.
11. **Locust: concurrent event scenarios** — Concurrency and race condition validation.

Defer:
- Collaboration event tests — lower risk; add after production events are covered
- pytest-xdist parallelization — add when test suite runtime exceeds 5 minutes
- Snapshot testing for event cascades — add after cascade structure is stable

---

## Sources

- Direct codebase analysis: `backend/api/events/base_event.py`, `step_completed.py`, `batch_completed.py`
- `.planning/codebase/CONCERNS.md` — idempotency gaps, race condition risks, fragile areas
- `.planning/PROJECT.md` — explicit scope constraints, testing strategy, constraints
- [Testing Event-Sourced Systems - EventSourcingDB](https://docs.eventsourcingdb.io/best-practices/testing-event-sourced-systems/) (MEDIUM confidence — referenced in search but unfetched)
- [Schemathesis pytest integration docs](https://schemathesis.readthedocs.io/en/stable/tutorials/pytest/) (HIGH confidence — official docs)
- [Testcontainers ArangoDB module](https://testcontainers.com/modules/arangodb/) (HIGH confidence — official page)
- [pytest-factoryboy documentation](https://pytest-factoryboy.readthedocs.io/) (HIGH confidence — official docs)
- [FastAPI testing guide - testdriven.io](https://testdriven.io/blog/fastapi-crud/) (MEDIUM confidence — verified community source)
- [Vue.js testing guide](https://vuejs.org/guide/scaling-up/testing) (HIGH confidence — official docs)
- [Locust FastAPI load testing](https://www.peterspython.com/en/blog/using-locust-to-load-test-a-fastapi-app-with-concurrent-users) (MEDIUM confidence — community verified)
