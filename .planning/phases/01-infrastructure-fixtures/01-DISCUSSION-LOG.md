# Phase 1: Infrastructure + Fixtures - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-09
**Phase:** 01-infrastructure-fixtures
**Areas discussed:** Test suite location, Schema init strategy, uv project layout, Fixture scope hierarchy

---

## Test Suite Location

| Option | Description | Selected |
|--------|-------------|----------|
| testing/pytest/ | Inside existing testing/ dir alongside Cypress and Robot | ✓ |
| New top-level tests/ | Separate from existing testing/ directory | |
| Inside backend/ | Co-locate with source code being tested | |

**User's choice:** testing/pytest/
**Notes:** Keeps all tests centralized, existing tooling stays consistent.

### Sub-question: Test file organization

| Option | Description | Selected |
|--------|-------------|----------|
| By domain/event | Subdirs per event type (step/, batch/, progress/, movement/) | ✓ |
| By layer (API vs direct) | Subdirs per test layer (api/, events/) | |

**User's choice:** By domain/event
**Notes:** Mirrors backend events/ structure.

---

## Schema Init Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Reuse db_init.py | Import and call deploy/scripts/db_init.py from conftest | ✓ |
| Replicate in conftest | Write collection creation directly in conftest.py | |

**User's choice:** Reuse db_init.py
**Notes:** Stays in sync with production schema automatically.

### Sub-question: Wait loop handling

| Option | Description | Selected |
|--------|-------------|----------|
| Call init logic directly | Skip wait_for_db_ready() loop | ✓ |
| Call as-is with wait loop | Include the retry loop | |

**User's choice:** Call init logic directly
**Notes:** Container is already ready when fixture runs.

---

## uv Project Layout

| Option | Description | Selected |
|--------|-------------|----------|
| testing/pytest/ | pyproject.toml inside pytest suite directory | ✓ |
| Repo root | pyproject.toml at top of repo | |

**User's choice:** testing/pytest/
**Notes:** Test deps fully isolated from backend pip deps.

### Sub-question: Backend source importability

| Option | Description | Selected |
|--------|-------------|----------|
| pythonpath in pyproject.toml | Declarative pytest config setting | ✓ |
| sys.path in conftest.py | Imperative path manipulation | |

**User's choice:** pythonpath in pyproject.toml
**Notes:** User corrected initial recommendation of sys.path manipulation — prefer declarative pytest config over imperative hacks.

---

## Fixture Scope Hierarchy

### httpx.AsyncClient scope

| Option | Description | Selected |
|--------|-------------|----------|
| Session scope | One client for full test run | ✓ |
| Function scope | Fresh client per test | |
| Module scope | One client per test file | |

**User's choice:** Session scope
**Notes:** User provided detailed analysis. ASGITransport has no TCP overhead. Auth via JWT Bearer headers (not cookies) means no session state leakage. DB isolation handled by collection truncation, not client scope.

### JWT auth fixture scope

| Option | Description | Selected |
|--------|-------------|----------|
| Function scope | Fresh token per test | ✓ |
| Session scope | One token set per session | |

**User's choice:** Function scope
**Notes:** Tokens are cheap to generate, tests need different scopes.

### Factory fixture scope

| Option | Description | Selected |
|--------|-------------|----------|
| Function scope + truncation | Clean slate per test, raw insert factories | ✓ |
| You decide | Claude's discretion | |

**User's choice:** Function scope + truncation
**Notes:** User considered event-driven setup but agreed with raw-insert approach after discussion of: (1) ArangoDB can't nest transactions so rollback-per-test won't work with events, (2) parametrize matrix needs surgical control, (3) cascading test failures if seed events break, (4) speed.

---

## Claude's Discretion

- Factory smoke test coverage design
- conftest.py split strategy (single root vs per-domain)

## Deferred Ideas

None
