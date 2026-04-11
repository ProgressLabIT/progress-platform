# Domain Pitfalls

**Domain:** Automated test suite for event-sourced FastAPI + ArangoDB MES
**Researched:** 2026-04-08

---

## Critical Pitfalls

Mistakes that cause rewrites, flaky test suites, or major blockers.

---

### Pitfall 1: Module-Level `db` Singleton Created at Import Time

**What goes wrong:** `utils/db.py` instantiates `db = client.db(...)` at module level. When pytest imports event classes or endpoint modules before the testcontainer is running, the ArangoDB client connects to the URL from environment config (default `localhost:8529`), not the testcontainer's dynamic port. All subsequent `db.begin_transaction()` calls in events fail with connection errors — or worse, silently connect to a real local ArangoDB if one happens to be running.

**Why it happens:** Python's import system runs module-level code on first import. The `lru_cache` on `get_config()` locks in config at import time. There is no dependency injection for the `db` object — every event class does `from utils.db import db` and gets the singleton.

**Consequences:** Tests pass locally if developer has ArangoDB on port 8529 but fail in CI. Tests that appear to use testcontainer are actually mutating a real database. Teardown leaves data. Hours debugging "works locally, fails in CI."

**Prevention:**
- Set environment variables (`PROGRESS_ARANGO_URL`, `PROGRESS_DB_NAME`) **before** importing any backend module. Use a session-scoped conftest fixture that starts the testcontainer first, sets env vars, then forces `importlib.reload` or uses `PYTHONPATH`-isolated subprocess imports.
- Alternatively: patch `utils.db.db` using `unittest.mock.patch` at the conftest level before any import, pointing it to the testcontainer-connected client.
- The cleanest path: in `conftest.py`, start container, call `config.get_config.cache_clear()` after setting env vars, then import backend modules.

**Detection:** Run tests with no local ArangoDB running. If they error on connection rather than fixture setup, this pitfall is hit.

**Phase:** Testcontainers infrastructure phase (Phase 1).

---

### Pitfall 2: NATS `publish_sync` Called at Transaction Commit — Blows Up Without NATS

**What goes wrong:** `BaseEvent.save()` calls `_publish_collected_events()` after `commit_transaction()`. `publish_sync()` calls `asyncio.run_coroutine_threadsafe(get_nats().publish(...), get_loop())`. If NATS client is not connected, `get_nats()` raises `RuntimeError("NATS client not connected")`, which surfaces after the transaction commits — the event is already written to ArangoDB but the test gets a NATS error. Tests appear to fail at "post-processing" for unrelated reasons.

**Why it happens:** NATS publishing is tightly coupled to the `save()` lifecycle in BaseEvent. It is non-blocking for Kafka failures (the old design) but synchronous-enough that an unconnected NATS client raises immediately. The transition from Kafka to NATS-py happened recently (visible in `nats_client.py`).

**Consequences:** Every direct event instantiation test fails unless NATS is running or mocked. API integration tests through FastAPI lifespan may work (lifespan connects NATS) but direct event tests do not.

**Prevention:**
- Mock `utils.nats_client.publish_sync` at the session level in conftest: `monkeypatch.setattr("utils.nats_client.publish_sync", lambda *a, **kw: None)`. This is safe because NATS publishing is explicitly acknowledged as a side effect outside the transaction.
- Do NOT run a NATS testcontainer — it adds startup overhead and tests should not depend on message delivery to be correct.
- For API integration tests using FastAPI's `httpx.AsyncClient`, override the NATS connect in the lifespan or use `asgi-lifespan` to skip the startup hook.

**Detection:** Direct event instantiation test raises `RuntimeError: NATS client not connected` after the event's ArangoDB transaction commits successfully.

**Phase:** Testcontainers infrastructure phase (Phase 1); affects every subsequent phase.

---

### Pitfall 3: ArangoDB Transaction Collection Declaration Mismatch

**What goes wrong:** ArangoDB stream transactions require all write collections to be declared upfront via `get_tx_collections()`. If a new child event is added to a cascade (e.g., a new `SerialXxxEvent` added to `_handle_batch_serials`) but the parent event's `get_tx_collections()` is not updated, ArangoDB raises error 1652 (`unregistered collection used in transaction`) inside the transaction. This is a runtime error that only surfaces when the new code path is exercised.

**Why it happens:** `BaseProductionEvent.get_tx_collections()` lists 15+ collections. Adding a child event that writes to a collection not in that list is easy to miss. The inheritance chain (BaseEvent → BaseProductionEvent → BatchCompletedEvent) means the list lives far from where child events are added.

**Consequences:** Test for a new child event fails with an opaque ArangoDB error. Developer sees a transaction error and suspects test setup, not a missing collection declaration.

**Prevention:**
- Add a test that calls `get_tx_collections()` for each event and asserts the returned list is a superset of all collections accessed in `apply()` and all child event `get_tx_collections()`. This is a static analysis test, not a runtime test.
- Whenever adding a `create_as_child` call in any event, check the parent event's collection list.
- Document the pattern prominently in the test factory fixtures — factory docstrings should note which collections are required.

**Detection:** `ArangoServerError: 1652 unregistered collection used in transaction` in test output. The error appears mid-test rather than during fixture setup.

**Phase:** BatchCompletedEvent test suite (Phase 2/3); all cascade event phases.

---

### Pitfall 4: Test Isolation Failure Due to Shared ArangoDB State

**What goes wrong:** Unlike relational databases, ArangoDB does not support transaction rollback as a test isolation mechanism the way pytest-django does. After each test, documents inserted by the test remain in collections unless explicitly deleted. If tests share a session-scoped database (even via testcontainer), test B sees data created by test A. This causes cascading failures where the second test in a class fails because a "unique" job or work order already exists.

**Why it happens:** The pattern of "start container once per session, reuse" (which is correct for startup performance) requires explicit teardown. ArangoDB does not have `TRUNCATE` as a cheap operation for edge collections that have dependent edges. Truncating a collection leaves dangling edges in related edge collections (`batch_serial`, `wip`, `event_source`, `contains`, `is_in_position`).

**Consequences:** Tests pass in isolation but fail when run together. Order-dependent failures are notoriously hard to debug. The existing `testing/` suite has this same problem (per PROJECT.md).

**Prevention:**
- Use `scope="function"` database fixtures that truncate all test collections in teardown — including edge collections. Write a `clean_db()` helper that truncates in the correct dependency order (edges before documents).
- Alternatively: use a unique database name per test (UUID suffix), created fresh and dropped after each test. More overhead but perfect isolation. Feasible with testcontainers if the container is session-scoped but the database is function-scoped.
- Factory fixtures must track created documents and clean up via `_key` in teardown — do not rely on collection-level truncation for session-scoped databases.

**Detection:** Running pytest with `--randomly-seed=12345` (or `-p randomly`) causes different tests to fail than running in default order. Any "document already exists" or "unique constraint" error in the second test of a class.

**Phase:** Testcontainers infrastructure (Phase 1); enforcement needed before any domain test phase.

---

### Pitfall 5: `BatchCompletedEvent` Cascade Depth Makes Factory Fixture Graph Wrong

**What goes wrong:** `BatchCompletedEvent.apply()` reads `self.batch`, `self.job`, `self.job.parameters`, `self.job.traceability_level`, `self.job.first_phase`, `self.job.last_phase`, `self.job.next_batch_available`, work order BOM, serial data, WIP edges, Config documents (`enable_inventory_management`, `default_production_position`, `default_consumption_position`), and Counter records — all within a single transaction. A factory fixture that creates only the Job and Batch documents (the "obvious" prerequisites) will fail deep inside `_process_inventory_changes()` or `_handle_batch_serials()` with a NoneType attribute error or missing document error, not at the point of the missing dependency.

**Why it happens:** The apply() method is 200+ lines and has conditional branches (warehouse management enabled?, traceability enabled?, first phase?, last phase?, auto_new_batch?). Each branch accesses different sub-graphs. Tests that exercise a simple path (no serials, no inventory) work, but tests covering the full path fail because the Config document for `enable_inventory_management` is missing from the test DB.

**Consequences:** Half the BatchCompletedEvent test matrix silently skips branches because Config lookups return None and the branch is gated on `if self.warehouse_management_enabled`. The bug being tested is never actually tested.

**Prevention:**
- The factory fixture for BatchCompletedEvent must insert ALL Config documents used by the event: `enable_inventory_management`, `default_production_position`, `default_consumption_position`. Make this explicit in a `base_config` fixture dependency.
- Write the factory as a builder pattern — `BatchCompletedFixture.with_inventory().with_traceability().with_auto_new_batch()` — so each flag is explicit and the fixture assertively creates the required sub-graph.
- Start every test suite with a smoke assertion: `assert event.warehouse_management_enabled == True` before the main assertion, to catch missing Config silently disabling the branch.

**Detection:** Test passes but no `MovementCompletedEvent` child events appear in the Event collection — the warehouse management branch was silently skipped because Config was missing.

**Phase:** BatchCompletedEvent test suite (Phase 3); also relevant to StepCompletedEvent.

---

## Moderate Pitfalls

---

### Pitfall 6: pytest-asyncio Event Loop Scope Mismatch with Session-Scoped Testcontainer

**What goes wrong:** The testcontainer fixture is session-scoped (correct — expensive to start). If `asyncio_mode = "auto"` is not set and `asyncio_default_fixture_loop_scope` defaults to `function`, the async httpx.AsyncClient fixtures get a different event loop than the session-scoped NATS connect (if used) or the FastAPI lifespan. This causes "Future attached to a different loop" errors that appear intermittently.

**Prevention:**
- In `pyproject.toml` under `[tool.pytest.ini_options]`: set `asyncio_mode = "auto"` and `asyncio_default_fixture_loop_scope = "session"`.
- Keep all session-scoped async fixtures in the same event loop scope.
- For direct event tests (synchronous — `BaseEvent.save()` is sync), no asyncio fixtures are needed. Keep the sync test layer fully sync.

**Detection:** `RuntimeError: Task attached to a different event loop` or `ScopeMismatch` warnings from pytest-asyncio during test collection.

**Phase:** Testcontainers infrastructure (Phase 1).

---

### Pitfall 7: FastAPI Lifespan Not Triggered by `httpx.AsyncClient` Without `asgi-lifespan`

**What goes wrong:** `main.py` startup hook connects to NATS and initializes singletons (WebsocketManager, KafkaConsumerManager). When tests use `httpx.AsyncClient(app=app)` directly, the lifespan is not triggered unless the client is used as a context manager AND the ASGI lifespan protocol is activated. If the lifespan does not run, NATS is not connected, and the first event dispatch that reaches `publish_sync` raises.

**Prevention:**
- Use `asgi-lifespan` (`LifespanManager`) to wrap the app in tests, or use `AsyncClient` as a context manager with `ASGITransport`.
- Mock NATS at a lower level (mock `publish_sync`) so lifespan connection to NATS is irrelevant to test correctness. This is the recommended approach — do not run real NATS in tests.

**Detection:** API integration test raises `RuntimeError: NATS client not connected` on the first POST request that triggers an event.

**Phase:** HTTP API integration test layer (Phase 2).

---

### Pitfall 8: Schemathesis Fuzzing Against Endpoints That Require Precondition State

**What goes wrong:** Schemathesis stateless mode generates random inputs against endpoints like `POST /batch-complete`. These endpoints require precondition state: a running Job, an active Batch, a valid work session. Without the state, every fuzz request returns 409 or 422 — Schemathesis reports these as "no crashes found" but actually found nothing meaningful. The coverage looks good but the fuzzer never reached the event logic.

**Why it happens:** FastAPI's OpenAPI spec describes input schemas but not the precondition state requirements. Schemathesis stateless mode cannot infer that `batch_key` must correspond to a real active batch.

**Prevention:**
- Use Schemathesis stateful mode (`--stateful=links`) and add OpenAPI `links` to responses — e.g., the response from `POST /job/start` links `job_key` to `POST /batch/complete`. This allows Schemathesis to chain requests in order.
- Before running Schemathesis, seed the test database with a standard fixture state (one running work order, one active job, one batch). Schemathesis will then exercise the event logic, not just the precondition guards.
- The OpenAPI spec audit phase (ensuring complete input/output schemas) is a hard prerequisite to useful Schemathesis results.

**Detection:** Schemathesis run returns 100% "no failures" on production event endpoints, but manual test of a real payload produces a 500. All fuzz responses are 409/422.

**Phase:** Schemathesis / OpenAPI audit phase.

---

### Pitfall 9: Quasar Dialog Testing — `$q.dialog()` Not Available in Vitest JSDOM

**What goes wrong:** `ProgressBtn.vue` uses `$q.dialog()` (Quasar Dialog plugin) for confirmation steps. In Vitest with JSDOM, Quasar's plugin is not auto-installed. Calling `installQuasarPlugin` in the test setup is required — without it, `this.$q.dialog` is undefined and component methods throw. Additionally, QDialog uses Vue's `<Teleport>` to render outside the component tree, so `wrapper.find('.q-dialog')` always returns empty — the dialog is mounted in `document.body`, outside the wrapper's scope.

**Prevention:**
- Call `installQuasarPlugin(Quasar)` before all Vitest tests in `vitest.setup.ts`.
- To assert dialog behavior: do not try to find the dialog in the wrapper. Instead, emit the dialog's confirm event directly: `await wrapper.findComponent(QDialog).vm.$emit('ok')` or use `vi.spyOn(Quasar, 'dialog')` to capture dialog calls and assert arguments.
- For teleported content, use Vitest browser mode (Playwright-backed) which renders in a real browser — teleportation works correctly.

**Detection:** `TypeError: this.$q.dialog is not a function` or `wrapper.find('.q-dialog')` always returns `WrapperLike` with `exists() === false`.

**Phase:** Vue component unit test phase (ProgressBtn.vue, WorkSessionSteps.vue).

---

### Pitfall 10: Factory Fixtures That Use `create_as_child()` Outside a Transaction Context

**What goes wrong:** Test helpers that try to build domain object graphs by calling `SomeEvent.create_as_child(fake_parent, data)` will fail because `create_as_child` requires a `parent_event` with an active `tx` (TransactionDatabase). Outside a real event's `save()` lifecycle, there is no transaction context. Factory code that treats `create_as_child` as a convenience constructor will raise `ValueError: Secondary events must be initialized with a transaction and event_group`.

**Why it happens:** `create_as_child` is designed to be called from within `apply()` — it inherits the parent event's transaction. Factories that want to create a Batch by "replaying" a BatchCreatedEvent need to invoke the full event cycle, not just the child creation path.

**Prevention:**
- Factory fixtures should call events via their primary path: instantiate the event with valid info, call `event.save()`, which opens its own transaction. Do not try to create sub-graphs using `create_as_child` in fixture code.
- To build a full graph (WorkOrder → Job → Batch), chain primary events: `JobStartedEvent(...).save()` then `BatchCreatedEvent(...).save()`. This is the realistic path and exercises the full application logic.
- If you need lightweight document insertion (skipping event logic), insert directly via `db.collection('Batch').insert(...)` for performance-critical fixture setup, but clearly label these as "raw fixtures" vs "event fixtures."

**Detection:** `ValueError: Secondary events must be initialized with a transaction and event_group` in fixture setup, before any test assertion runs.

**Phase:** Factory fixture design (Phase 1 / foundation of all other phases).

---

## Minor Pitfalls

---

### Pitfall 11: Testcontainers ArangoDB Default Image Has No Collections

**What goes wrong:** The testcontainer starts a blank ArangoDB instance with no database schema. The application expects collections like `Job`, `Batch`, `WorkOrder`, `Event`, `event_source`, `wip`, `is_in_position`, etc. If the conftest fixture does not create these collections before tests run, every `db.collection('Job').insert(...)` call raises `CollectionNotFound`.

**Prevention:**
- Create a `setup_schema(db)` helper in conftest that creates all collections and edge collections. Run it once in the session-scoped fixture after the container starts.
- Maintain a canonical `COLLECTIONS` and `EDGE_COLLECTIONS` list in the test conftest. When a new collection is added to the application, add it here — missing from this list will surface immediately.
- Do not use the ArangoDB init scripts approach (mounting a script to docker-entrypoint) — it complicates the testcontainer setup unnecessarily.

**Detection:** `ArangoServerError: collection or view not found` on first fixture document insert.

**Phase:** Testcontainers infrastructure (Phase 1).

---

### Pitfall 12: `cached_property` in Events Caches Across Test Invocations

**What goes wrong:** `BatchCompletedEvent` uses `@cached_property` for `warehouse_management_enabled` and `batch_component_serials_map`. These are instance-level caches, so they reset per event instantiation. However, if a test helper holds a reference to the event instance and calls methods on it after the transaction commits (e.g., to inspect state), the cached properties may return stale values from the now-committed transaction scope.

**Prevention:**
- Do not inspect event instances after `.save()` returns — the response is `event.response`, not the event itself.
- Tests should assert on the database state (query collections directly) rather than on event instance attributes.

**Detection:** Test assertion reads `event.warehouse_management_enabled` after save and gets `False` even though Config was set correctly — the cache captured the pre-setup state.

**Phase:** BatchCompletedEvent and MovementCompletedEvent test suites.

---

### Pitfall 13: `_copy_batch_media_to_serials` Depends on Filesystem Path `/media/...`

**What goes wrong:** `BatchCompletedEvent._copy_batch_media_to_serials()` calls `shutil.copytree` on `/media/traceability/{wo_key}/{batch_key}/`. In tests, this path does not exist. If the traceability path is exercised (batch with serials, batch with step form data containing file fields), the `glob()` call returns empty (no error), but if the directory exists partially, `shutil.copytree` may raise `FileNotFoundError`.

**Prevention:**
- In tests that exercise the serial path, create a temp directory and mock the `/media` base path, or use `tmp_path` pytest fixture and monkeypatch `Path` in `batch_completed.py`.
- The simplest approach: ensure test fixtures do not include file-type form fields, which are the only source of actual media content. Serial-only tests (no file uploads) exercise the glob on an empty directory, which returns safely.

**Detection:** `FileNotFoundError` in tests that exercise traceability with file form fields.

**Phase:** BatchCompletedEvent serial handling tests.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|----------------|------------|
| Testcontainers conftest setup | Module-level `db` singleton bakes in wrong URL at import (Pitfall 1) | Set env vars before any backend import; `cache_clear()` config |
| Testcontainers conftest setup | NATS not running, `publish_sync` raises post-commit (Pitfall 2) | Mock `publish_sync` at session scope |
| Testcontainers conftest setup | Empty ArangoDB — no collections (Pitfall 11) | `setup_schema()` helper in session fixture |
| Factory fixtures | Using `create_as_child` outside a transaction (Pitfall 10) | Chain primary events only in factories |
| Factory fixtures | Test isolation — shared ArangoDB state (Pitfall 4) | Per-function DB cleanup; truncate edge collections in order |
| BatchCompletedEvent tests | Missing Config documents silently skip branches (Pitfall 5) | `base_config` fixture; smoke assertions on branch flags |
| BatchCompletedEvent tests | Transaction collection mismatch with new child events (Pitfall 3) | Static test on `get_tx_collections()` completeness |
| BatchCompletedEvent tests | `_copy_batch_media_to_serials` filesystem dependency (Pitfall 13) | No file-type fields in serial test fixtures |
| HTTP API integration tests | FastAPI lifespan not triggered — NATS not connected (Pitfall 7) | Mock `publish_sync`; use `ASGITransport` with lifespan |
| HTTP API integration tests | Async event loop scope mismatch (Pitfall 6) | `asyncio_mode = auto`, session loop scope in pyproject.toml |
| Schemathesis fuzzing | No precondition state — fuzzer never reaches event logic (Pitfall 8) | Seed DB fixture; stateful mode with OpenAPI links |
| Vue component tests | QDialog teleport invisible to JSDOM wrapper (Pitfall 9) | `installQuasarPlugin`; spy on `$q.dialog`; browser mode for E2E |

---

## Sources

- [ArangoDB Stream Transactions: Locking and Isolation](https://docs.arangodb.com/3.10/develop/transactions/locking-and-isolation/) — HIGH confidence (official docs)
- [ArangoDB Transaction Limitations](https://docs.arangodb.com/3.11/develop/transactions/limitations/) — HIGH confidence (official docs)
- [python-arango Transactions documentation](https://docs.python-arango.com/en/main/transaction.html) — HIGH confidence (official docs)
- [testcontainers-python ArangoDB module](https://testcontainers-python.readthedocs.io/en/latest/modules/arangodb/README.html) — HIGH confidence (official docs)
- [Testcontainers Best Practices — Docker](https://www.docker.com/blog/testcontainers-best-practices/) — MEDIUM confidence
- [Quasar Testing: Dialogs with Teleported Wrapper](https://github.com/quasarframework/quasar/discussions/17084) — MEDIUM confidence (community discussion, verified by Quasar maintainers)
- [QDialog not mounted in tests · quasar-testing issue](https://github.com/quasarframework/quasar-testing/issues/72) — MEDIUM confidence
- [Schemathesis Stateful Testing](https://schemathesis.readthedocs.io/en/stable/explanations/stateful/) — HIGH confidence (official docs)
- [pytest-asyncio Concepts: event loop scope](https://pytest-asyncio.readthedocs.io/en/stable/concepts.html) — HIGH confidence (official docs)
- [FastAPI Async Tests](https://fastapi.tiangolo.com/advanced/async-tests/) — HIGH confidence (official docs)
- [Testing lifespan + state in FastAPI — GitHub Discussion](https://github.com/fastapi/fastapi/discussions/10800) — MEDIUM confidence
- Source code analysis: `backend/api/events/base_event.py`, `backend/api/utils/db.py`, `backend/api/utils/nats_client.py`, `backend/api/events/production/batch_completed.py` — HIGH confidence (primary source)
