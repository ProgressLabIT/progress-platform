# Backend tests

Pytest suite covering the FastAPI app, event pipeline, and bridge automations.

## Run

```bash
cd testing/pytest
uv sync
uv run pytest                                          # everything
uv run pytest tests/unit/                              # pure-Python, no Docker (~4s)
uv run pytest tests/integration/                       # full ArangoDB + NATS mock
uv run pytest tests/production/                        # domain-specific
uv run pytest -k "test_job_started"                    # by name
uv run pytest --cov                                    # with coverage
```

## Test subtrees — pick the right home

| Subtree | What goes there | Cost |
|---------|-----------------|------|
| `tests/unit/` | Pure-Python: state machines, parsers, format converters, outbound HTTP via `httpx.MockTransport`. **No backend imports that pull in `utils.db`, `utils.nats_client`, or `events.*` chains at module level.** | ~4s, no Docker |
| `tests/integration/` | Anything that calls into the FastAPI app, instantiates an `Event`, or asserts on real persisted state | ArangoDB testcontainer + ~8s startup |
| `tests/production/`, `tests/batch/`, `tests/movement/`, `tests/serial/`, `tests/step/`, `tests/collaboration/`, `tests/api/`, etc. | Domain-grouped integration tests | Same as `tests/integration/` |
| `tests/factories/`, `tests/infrastructure/` | Smoke tests for fixtures themselves | Same as integration |

**Rule of thumb:** if your test needs a `db` parameter, it's not a unit test.

## Why `tests/unit/` is special

The repo-root `conftest.py` declares **session-scope autouse fixtures** that:

1. Spin up `arangodb:3.11` via testcontainers (~8s)
2. Initialize the schema in a fresh ArangoDB `PROGRESS_TEST` database
3. Monkey-patch the `db` singleton across `utils.db`, `utils.auth`, `events.base_event`
4. Mock NATS (`publish_sync`, `connect`, `drain`)
5. Truncate non-system collections after each test

This is the right shape for the integration suite — testing principle #4 says *real database, never mocked*. But pure-Python unit tests pay 8s for nothing and break on any environment where the Docker socket is not at `/var/run/docker.sock` (e.g. macOS Docker Desktop, which uses `~/.docker/run/docker.sock`).

`tests/unit/conftest.py` overrides each autouse fixture (`arango_container`, `db`, `mock_nats`, `_capture_config_defaults`, `truncate_collections`) with a same-named no-op. Pytest's nearest-conftest resolution makes the overrides win for everything under `tests/unit/`; tests in any other subtree continue to use the real testcontainer parents unchanged.

**Adding a new unit subdirectory:** drop a new directory under `tests/unit/`. The parent `tests/unit/conftest.py` covers it automatically — no further conftest work needed.

**Adding a new integration test:** put it under any sibling of `tests/unit/` (or create a new domain directory). The repo-root fixtures kick in automatically.

## macOS gotcha — Docker socket path for integration tests

Docker Desktop on macOS does not symlink `/var/run/docker.sock`. Testcontainers fails with `Connection aborted FileNotFoundError`. Fix:

```bash
launchctl setenv DOCKER_HOST unix:///Users/$USER/.docker/run/docker.sock
```

Or export `DOCKER_HOST` in your shell rc. Affects every testcontainers project — set once.

`tests/unit/` does not need this since its conftest overrides skip Docker entirely.

## Conventions

- `async def` test methods — pytest-asyncio is in auto mode
- Class-based grouping by feature (`TestJobLifecycle`)
- Sequential tests within a class share state via class variables
- BDD-style docstrings on each test (Given / When / Then)
- Plain `assert` with descriptive f-string messages
- Factories in root `conftest.py` (`create_user`, `create_product`, `create_production_graph`, …) — see [.planning/codebase/TESTING.md](../../.planning/codebase/TESTING.md) for the full FACT-01..FACT-14 catalog

## What is mocked

- NATS — `publish_sync` is a noop in integration tests; not exercised at all in unit tests
- WeasyPrint — stubbed at import time (GTK not available)
- Auth tokens — `verify_token` overridden via `app.dependency_overrides` (integration only)

## What is NOT mocked

- ArangoDB — real container in integration; absent in unit
- FastAPI app — real ASGI transport in integration; absent in unit
- Event pipeline — runs through real `BaseEvent.save()` in integration
- Pydantic validation — always real

## See also

- `.planning/codebase/TESTING.md` — full testing-strategy reference
- `tests/helpers.py` — shared assertion helpers (`assert_event_dispatched`)
- `conftest_helpers/schema.py` — ArangoDB schema bootstrap for the testcontainer
