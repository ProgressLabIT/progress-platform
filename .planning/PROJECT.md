# Progress Platform Test Suite

## What This Is

A comprehensive automated test suite for the Progress Platform — a manufacturing execution system (MES) built on FastAPI + ArangoDB + Vue 3/Quasar. Replaces the fragmented testing approach (Mocha/Cypress/Robot Framework) with a modern unified stack: pytest + testcontainers for backend, Vitest + Playwright for frontend, Schemathesis for API fuzzing, and Locust for load testing.

## Core Value

Catch regressions in the critical production event chain (StepCompleted → BatchCompleted → JobClosed, inventory movements, WIP cascades, serial traceability) before they reach users.

## Requirements

### Validated

- ✓ Testcontainers-based ArangoDB test infrastructure — v2.0 (ArangoDB 3.11 ephemeral container, db singleton override, 7 session/function fixtures)
- ✓ Factory fixtures for domain object graphs — v2.0 (14 factories: WorkOrder → Job → Batch → WorkSession → StepExecution, + User, Product, BOM, Config, Serial, WIP, Position, Queue)
- ✓ Deep test suite for StepCompletedEvent — v2.0 (8 tests, dual-layer: direct + HTTP)
- ✓ Deep test suite for BatchCompletedEvent — v2.0 (24 tests, 9-row parametrize matrix)
- ✓ Deep test suite for ProgressOverrideRequestedEvent — v2.0 (16 tests, all PROG requirements except PROG-10/11)
- ✓ Deep test suite for MovementCompletedEvent — v2.0 (18 tests, all 16 movement types)
- ✓ Both test layers (HTTP API + direct event instantiation) — v2.0
- ✓ OpenAPI spec completeness audit — v2.0 (75+ routes, warn-only, introspection via app.routes)
- ✓ Schemathesis API fuzzing — v2.0 (non-multipart/non-SSE routes, zero 5xx on valid inputs)
- ✓ Vitest + @vue/test-utils unit tests for ProgressBtn.vue — v2.0 (8 behavioral tests)
- ✓ Vitest + @vue/test-utils unit tests for WorkSessionSteps.vue — v2.0 (11 tests)
- ✓ Playwright E2E tests for critical user journeys — v2.0 (3 journeys: login→batch complete, work order creation, stock receipt)
- ✓ Locust load test scenarios — v2.0 (batch completion, inventory movement, production queries)
- ✓ uv as Python package/project manager — v2.0

### Active

- [ ] Test coverage for serial events (SerialCreated, SerialUpdated, SerialLinked, SerialReleased)
- [ ] Test coverage for collaboration events (issues, messages, tasks)
- [ ] BATCH-13: Component serials trigger SerialLinkedEvent for each component (complex BOM + component serial fixture path)
- [ ] PROG-10: Inventory movements for warehouse-enabled ProgressOverride
- [ ] PROG-11: Inventory movement reversal for canceled batches
- [ ] GitLab CI/CD pipeline integration (after test suite is stable)
- [ ] Playwright E2E CI integration (requires live stack)
- [ ] Schemathesis coverage for multipart/file upload and SSE endpoints

### Out of Scope

- Backfilling tests on all existing code — grow coverage from the frontier per testing strategy
- Microcks contract testing — no clear benefit identified
- Mobile warehouse app (Capacitor) testing — focus on main webapp and backend
- Replacing existing Mocha/Cypress/Robot tests — new suite runs alongside, old tests deprecated organically

## Context

**Shipped v2.0:** 4 phases, 15 plans, 3 days (2026-04-09 → 2026-04-11).

**Test counts:** 75+ backend pytest tests, 19 Vitest component tests, 10 Playwright E2E scripts, Schemathesis fuzzer, 3 Locust scenarios.

**Infrastructure state:** `testing/pytest/` is a uv project with pyproject.toml + uv.lock. ArangoDB container spins up once per pytest session. All tests isolated via per-class collection truncation (`truncate_collections` autouse fixture).

**Known tech debt:** BATCH-13, PROG-10, PROG-11 unsatisfied (3/106 requirements). All require `manage_inventory=True` + warehouse interaction paths not built in factory fixtures.

**Backend architecture:** Event-sourced with 50+ event types. Events cascade via `create_as_child()` within ArangoDB transactions. The cascading nature makes deep isolated testing critical — validated by this milestone.

## Constraints

- **Database:** Must use real ArangoDB (via testcontainers), not mocks — per testing strategy principle #4
- **Python:** 3.11 (matching backend container)
- **Node.js:** 20.19.0 (matching webapp runtime)
- **Isolation:** Tests must be fully isolated — no shared state between test classes
- **Docker:** Required for testcontainers (ArangoDB) and Playwright browsers

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Testcontainers over dedicated test DB | Fully isolated, CI-friendly, no shared state risk | ✓ Good — zero cross-test contamination observed |
| Both API + direct event test layers | API for realism, direct for edge case coverage | ✓ Good — caught real bugs in both layers |
| Factory fixtures over static seeds | Domain object graphs are deeply interconnected; factories compose and maintain better | ✓ Good — 14 factories reused across all phases |
| Vitest + Playwright over Playwright-only | Fast component tests with Vitest, realistic E2E with Playwright | ✓ Good — component tests run in ms, E2E covers real journeys |
| uv over pip for test deps | Modern, fast, lockfile support, better dependency resolution | ✓ Good — `uv sync` is the only setup step |
| Schemathesis with spec audit first | Fuzzing only works well with complete OpenAPI schemas; audit endpoints first | ✓ Good — audit revealed 75+ routes missing response_model |
| Locust for load testing | Python-native, scriptable, integrates with test knowledge | ✓ Good — 3 scenarios deliverable standalone |
| Warn-only OpenAPI audit | Fixing 75+ endpoints is a separate production engineering effort | ✓ Good — audit reports state, doesn't gate CI |
| Exclude multipart/SSE from Schemathesis | Framework can't auto-generate valid multipart/streaming inputs | ✓ Good — avoids false failures |
| BatchCompleted curated parametrize matrix | 32-combination exhaustive matrix infeasible; curated 9-row matrix covers all branch points | ⚠ Revisit — left BATCH-13 uncovered |
| db singleton override via env vars + lru_cache clear | Only way to inject test DB before module-level singleton creation | ✓ Good — works reliably across all test modules |
| NATS mock via monkeypatch.setattr on 5 namespaces | publish_sync imported in 4 local namespaces; must patch all | ✓ Good — no NATS exceptions in any test |

---
*Last updated: 2026-04-11 after v2.0 milestone*
