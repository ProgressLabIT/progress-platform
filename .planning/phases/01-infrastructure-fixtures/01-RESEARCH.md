# Phase 1: Infrastructure + Fixtures - Research

**Researched:** 2026-04-09
**Domain:** pytest / testcontainers / ArangoDB / FastAPI ASGI testing / uv
**Confidence:** HIGH

## Summary

This phase builds the test harness that all subsequent phases depend on. The core challenge is not library configuration — it is import ordering. Python executes module-level code on import, so `utils/db.py` and `utils/auth.py` both instantiate the `db` singleton the moment they are imported. Env vars controlling the testcontainer URL must be set and `get_config` lru_cache must be cleared before any backend module is imported. This must be the very first thing `conftest.py` does, before any backend module appears in any import at session scope.

The second structural problem is `deploy/scripts/db_init.py`. It cannot be imported — it runs `get_secret()`, connects to `http://db:8529`, and calls `wait_for_db_ready()` at module level. The solution is to copy the `collections` list definition and the collection-creation loop into a standalone test helper function (`testing/pytest/conftest_helpers/schema.py`) that accepts a db handle and creates collections/indexes/default records.

NATS mocking is straightforward: `publish_sync` is referenced by name in `utils.nats_client`, and all callers import it from that module. Mocking `utils.nats_client.publish_sync` with `monkeypatch.setattr` at session scope covers all callers. Auth is more nuanced: `verify_token` does a live DB lookup of the Token collection to validate the token signature and revocation state — test JWT tokens require real Token records inserted into the test DB, or the `verify_token` FastAPI dependency must be overridden per-request via `app.dependency_overrides`.

**Primary recommendation:** Use `app.dependency_overrides[verify_token]` to bypass real token validation in ASGI tests. Factory fixtures use raw `db.collection().insert()`. Session conftest sets env vars and clears lru_cache before any backend import.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Pytest suite lives at `testing/pytest/` inside the existing `testing/` directory
- **D-02:** Test files organized by domain: `tests/infrastructure/`, `tests/step/`, `tests/batch/`, `tests/progress/`, `tests/movement/`, `tests/factories/`
- **D-03:** Reuse `deploy/scripts/db_init.py` schema — import and call its schema creation functions directly from a session-scoped conftest fixture
- **D-04:** Skip `wait_for_db_ready()` loop — call init logic directly since testcontainer is already ready
- **D-05:** `pyproject.toml` and `uv.lock` live at `testing/pytest/` — uv project root is the pytest suite directory
- **D-06:** Backend source made importable via `pythonpath = ["../../backend/api"]` in `[tool.pytest.ini_options]` in `pyproject.toml`
- **D-07:** ArangoDB testcontainer — session scope
- **D-08:** Schema initialization via db_init.py — session scope
- **D-09:** NATS mock via monkeypatch.setattr — session scope
- **D-10:** httpx.AsyncClient with ASGITransport — session scope
- **D-11:** JWT auth token fixture — function scope
- **D-12:** Factory fixtures — function scope with raw `db.collection().insert()`
- **D-13:** Collection truncation between tests — function scope (edges before documents)
- **D-14:** Config document seeding — required in factories
- **D-15:** db singleton override: set `PROGRESS_*` env vars before backend module import + clear `get_config` lru_cache
- **D-16:** NATS `publish_sync` mocked at session scope to prevent post-commit crashes

### Claude's Discretion

- Factory smoke tests in `tests/factories/` — Claude to determine what validation is needed
- conftest.py split strategy — single root conftest vs per-domain conftest files, Claude to decide during planning

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INFRA-01 | Testcontainers spins up ArangoDB 3.11 container at session scope with automatic cleanup | testcontainers 4.14.2 `GenericContainer` or `ArangoDbContainer`; session-scoped fixture |
| INFRA-02 | Schema initialization creates all collections, edge collections, indexes, and default records | Extract `collections` list from `db_init.py` into a helper function; call against testcontainer db handle |
| INFRA-03 | `db` singleton override injects testcontainer URL via env vars before backend import, clears `get_config` lru_cache | Must happen at session scope, before any backend module is imported; autouse conftest fixture |
| INFRA-04 | NATS `publish_sync` is mocked at session scope | Mock target: `utils.nats_client.publish_sync`; all 4 callers import from this module |
| INFRA-05 | httpx.AsyncClient with ASGITransport provides in-memory API test client | `httpx.AsyncClient(app=app, base_url="http://test", transport=ASGITransport(app))` |
| INFRA-06 | Auth JWT fixture generates valid tokens with configurable scopes | Use `issue_token()` from `utils/auth.py` + insert Token record, OR use `app.dependency_overrides` |
| INFRA-07 | Collection truncation between tests ensures full isolation (edges before documents) | Function-scoped autouse fixture; truncate edge collections first, then document collections |
| INFRA-08 | uv manages test suite dependencies via pyproject.toml with committed uv.lock | `uv init` at `testing/pytest/`; `[tool.pytest.ini_options]` in pyproject.toml |
| FACT-01 | User factory creates users with configurable scope strings | Raw `db.collection('User').insert()`; scope is a space-separated string |
| FACT-02 | Product factory creates products with configurable process (phases, operations, steps, form fields) | Raw inserts into Product, Phase, Operation, Step, CustomField collections |
| FACT-03 | BOM factory creates product bill-of-materials with component products | Raw inserts into `requires` edge collection |
| FACT-04 | WorkOrder factory creates work orders linked to products | Raw inserts into WorkOrder; WO code via counter or static test value |
| FACT-05 | Job factory creates jobs linked to work orders and phases | Raw inserts into Job; configurable step_check, auto_new_batch, production_batch_qt, std_processing_time |
| FACT-06 | Batch factory creates batches linked to jobs | Raw inserts into Batch; configurable quantities and status |
| FACT-07 | WorkSession factory creates work sessions linked to batches | Raw inserts into WorkSession |
| FACT-08 | StepExecutionData factory creates step execution records | Raw inserts into StepExecutionData |
| FACT-09 | Config document factory seeds required Config records | Config collection has default records from schema init; factory only needs to override specific keys |
| FACT-10 | Parametrized builder combines flags to create correctly linked domain object graphs | Orchestrates FACT-02 through FACT-08; returns all keys for test access |
| FACT-11 | Serial factory creates serial records linked to products | Raw inserts into Serial |
| FACT-12 | WIP factory creates work-in-progress edge records | Raw inserts into `wip` edge collection |
| FACT-13 | Inventory position factory creates positions with is_in_position records | Raw inserts into Position and `is_in_position` collections |
| FACT-14 | Queue factory creates site and operator queue records | Raw inserts into Queue; site queue default record already exists from schema init |
</phase_requirements>

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 9.0.3 | Test runner | Project standard (km/testing/strategy.md) |
| pytest-asyncio | 1.3.0 | Async test support | FastAPI endpoints are async; required for `async def test_*` |
| testcontainers | 4.14.2 | Spin up ArangoDB 3.11 container | Real database requirement (testing principle #4) |
| httpx | 0.28.1 | ASGI test client | FastAPI-native async HTTP client; ASGITransport for in-memory |
| pytest-cov | 7.1.0 | Coverage reporting | Strategy.md specifies pytest-cov |
| python-arango | 8.x | ArangoDB Python driver | Already in backend/api/requirements.txt |
| PyJWT | 2.0.x | JWT token generation for auth fixtures | Already in backend/api/requirements.txt |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| passlib | 1.7.2 | Password hashing for User factory | User records need bcrypt hash |
| pydantic-settings | 2.x | Already used by backend config | Imported transitively when backend code loads |
| python-dateutil | 2.8.x | Date utilities | Used by backend models |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| testcontainers GenericContainer | Local ArangoDB instance | testcontainers provides isolation and CI compatibility; local instance has state bleed risk |
| app.dependency_overrides for auth | Real Token DB records per test | dependency_overrides is simpler and avoids Token collection in truncation list; real records needed only for auth endpoint tests |
| Raw `db.collection().insert()` | factory_boy | factory_boy is ORM-oriented; document DB with nested dicts is simpler with plain functions (strategy.md confirms this) |

**Installation:**
```bash
# From testing/pytest/
uv add pytest pytest-asyncio testcontainers httpx pytest-cov python-arango PyJWT passlib python-dateutil pydantic pydantic-settings python-arango bcrypt python-jose cryptography python-multipart
```

**Version verification:** Versions above confirmed via PyPI registry on 2026-04-09.

---

## Architecture Patterns

### Recommended Project Structure

```
testing/pytest/
├── pyproject.toml           # uv project root; pytest config here
├── uv.lock                  # committed lock file
├── conftest.py              # root conftest: env override, db fixture, NATS mock, schema init, client
├── conftest_helpers/
│   └── schema.py            # extracted schema creation function (from db_init.py)
└── tests/
    ├── infrastructure/      # smoke tests: container starts, schema exists
    ├── factories/           # factory smoke tests: full graph creation
    ├── step/                # Phase 2: StepCompleted tests
    ├── batch/               # Phase 2: BatchCompleted tests
    ├── progress/            # Phase 2: ProgressOverrideRequested tests
    └── movement/            # Phase 2: MovementCompleted tests
```

### Pattern 1: Import-Order-Safe db Override

**What:** Set env vars and clear lru_cache before any backend module import.
**When to use:** Always — this is the only safe approach given module-level singleton instantiation in `utils/db.py`.

```python
# conftest.py — MUST be at top of file, before any backend imports

import os
import pytest

# Step 1: Set env vars BEFORE any backend module is imported
# These are read by utils/config.py Settings at import time
os.environ["PROGRESS_ARANGO_URL"] = "placeholder"  # overridden per fixture
os.environ["PROGRESS_DB_NAME"] = "PROGRESS_TEST"
os.environ["PROGRESS_JWT_SECRET"] = "test-secret-key-not-for-production"
os.environ["PROGRESS_API_DB_USERNAME"] = "root"
os.environ["PROGRESS_API_DB_PWD"] = ""

# Step 2: Clear lru_cache so get_config() re-reads env vars
from utils.config import get_config
get_config.cache_clear()

# NOW it's safe to import backend modules
from utils.db import db as _db_singleton
```

The problem: `PROGRESS_ARANGO_URL` must contain the testcontainer's actual URL, which isn't known until the container starts. The workaround:

```python
# Session-scoped fixture that overrides db singleton BEFORE container starts
# by patching utils.db.db and utils.db.client at the module level

@pytest.fixture(scope="session", autouse=True)
def arango_container():
    from testcontainers.core.container import DockerContainer
    container = (
        DockerContainer("arangodb:3.11")
        .with_env("ARANGO_NO_AUTH", "1")
        .with_exposed_ports(8529)
    )
    with container:
        port = container.get_exposed_port(8529)
        host = container.get_container_host_ip()
        url = f"http://{host}:{port}"

        # Override env var and clear cache
        os.environ["PROGRESS_ARANGO_URL"] = url
        get_config.cache_clear()

        # Re-point the module-level db singleton
        import utils.db as db_module
        from arango import ArangoClient
        new_client = ArangoClient(hosts=url)
        new_db = new_client.db("PROGRESS_TEST", username="root", password="")
        db_module.db = new_db
        db_module.client = new_client

        # Also patch auth.py's reference (imported separately)
        import utils.auth as auth_module
        auth_module.db = new_db

        yield new_db
```

**Critical:** `utils/auth.py` does `from utils.db import db` at import time — it captures a reference to the original `db` object, not a live reference to `utils.db.db`. After patching `utils.db.db`, `utils.auth.db` also needs patching.

### Pattern 2: Schema Initialization Helper

**What:** Extract collections definition from `db_init.py` into a test helper function. `db_init.py` cannot be imported directly — it has module-level code that calls `get_secret()` (opens `/run/secrets/progress_db_root_pwd`) and `wait_for_db_ready()`.

```python
# testing/pytest/conftest_helpers/schema.py

from arango import ArangoClient
from arango.database import StandardDatabase
from pydantic import BaseModel, Field
from datetime import datetime

class DBIndex(BaseModel):
    type: str | None = 'persistent'
    fields: list[str]
    name: str
    storedValues: list[str] | None = Field(None, exclude=True)

class Collection(BaseModel):
    name: str
    indexes: list[DBIndex] | None = []
    default_records: list[dict] | None = []

# Copy the `collections` list verbatim from db_init.py lines 156-384
COLLECTIONS = [
    Collection(name='Batch', indexes=[...]),
    # ... all collections
]

def initialize_schema(db: StandardDatabase) -> None:
    """Create all collections, indexes, and default records against the provided db handle."""
    for c in COLLECTIONS:
        db.create_collection(name=c.name, edge=c.name[0].islower())
        collection = db.collection(c.name)
        for index in c.indexes:
            collection.add_index(index.model_dump())
        if c.default_records:
            collection.insert_many(c.default_records)
```

### Pattern 3: NATS Mock

**What:** Mock `utils.nats_client.publish_sync` at session scope to prevent post-commit RuntimeError ("NATS client not connected").

```python
# conftest.py
import pytest

@pytest.fixture(scope="session", autouse=True)
def mock_nats_publish(session_mocker):
    # All callers do: from utils.nats_client import publish_sync
    # The name is bound in their local namespace — must mock the source module attribute
    import utils.nats_client as nats_module
    original = nats_module.publish_sync
    nats_module.publish_sync = lambda subject, data: None
    yield
    nats_module.publish_sync = original
```

Note: `session_mocker` requires `pytest-mock`. Alternatively use a manual patch as shown above. The four callers that import `publish_sync` are:
- `events/base_event.py`
- `events/inventory/base_inventory.py`
- `events/serial/base_serial.py`
- `endpoints/print.py`

All bind `publish_sync` from `utils.nats_client` at import time, so patching `utils.nats_client.publish_sync` after those modules are already imported will NOT work. The fix: patch must happen before those modules are imported, OR use `monkeypatch.setattr("utils.nats_client.publish_sync", ...)` which patches the module attribute and all subsequent calls through the module — but callers that already have a local binding (`from utils.nats_client import publish_sync`) will NOT see the patch.

**Correct approach:** Replace the function object in each caller's namespace explicitly:

```python
@pytest.fixture(scope="session", autouse=True)
def mock_nats_publish():
    import utils.nats_client as nats_module
    import events.base_event as base_event_module
    import events.inventory.base_inventory as base_inv_module
    import events.serial.base_serial as base_serial_module

    noop = lambda subject, data: None
    nats_module.publish_sync = noop
    base_event_module.publish_sync = noop
    base_inv_module.publish_sync = noop
    base_serial_module.publish_sync = noop
    yield
```

### Pattern 4: Collection Truncation (Test Isolation)

**What:** Truncate all collections after each test, edges before documents, to satisfy ArangoDB's referential structure.

```python
# conftest.py
EDGE_COLLECTIONS = [
    'batch_serial', 'can_use_print_template', 'contains', 'event_source',
    'has_tag', 'inventory_count_position_complete', 'inventory_count_record',
    'is_in_position', 'issue_rel', 'media_connection', 'message', 'movement',
    'requires', 'task_rel', 'wip',
]
DOCUMENT_COLLECTIONS_SKIP_TRUNCATE = ['Config', 'Counter', 'CustomField', 'Queue', 'is_in_position']

@pytest.fixture(autouse=True)
def truncate_collections(db):
    yield
    # Truncate edges first
    for name in EDGE_COLLECTIONS:
        db.collection(name).truncate()
    # Then documents (skip Config/Counter/Queue — re-seeded or static)
    for c in db.collections():
        if not c['system'] and c['name'] not in DOCUMENT_COLLECTIONS_SKIP_TRUNCATE:
            if not c['name'][0].islower():  # document collections
                db.collection(c['name']).truncate()
```

**Note:** Config, Counter, Queue default records are inserted at schema init time (session scope). Truncating them would break subsequent tests. Either re-seed them in the truncation fixture or exclude them. The CONTEXT.md decision D-14 says Config document seeding is required in factories — this means factories should upsert Config keys rather than relying on schema init defaults.

### Pattern 5: httpx AsyncClient with ASGITransport

```python
# Source: httpx official docs + FastAPI testing guide
import httpx
from httpx import ASGITransport
from main import app

@pytest.fixture(scope="session")
async def client():
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as c:
        yield c
```

**Auth override — recommended approach:** Use `app.dependency_overrides` to bypass the Token DB lookup:

```python
from utils.auth import verify_token
from models.auth import TokenData, TokenContext, ConsumerType
from datetime import datetime, timedelta

def make_token_data(scope: str = "operator") -> TokenData:
    return TokenData(
        jti="test-token-key",
        sub="test-user-key",
        ctyp=ConsumerType.USER,
        iat=datetime.utcnow(),
        exp=datetime.utcnow() + timedelta(hours=1),
        ctx=TokenContext.USER_SESSION,
        scope=scope,
    )

@pytest.fixture
def auth_override(scope: str = "operator production admin"):
    app.dependency_overrides[verify_token] = lambda: make_token_data(scope)
    yield
    app.dependency_overrides.clear()
```

This avoids inserting Token records into every test and does not require the JWT secret to match.

### Pattern 6: uv pyproject.toml layout

```toml
# testing/pytest/pyproject.toml
[project]
name = "progress-test-suite"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "pytest>=9.0",
    "pytest-asyncio>=1.3",
    "testcontainers>=4.14",
    "httpx>=0.28",
    "pytest-cov>=7.1",
    "python-arango>=8",
    "PyJWT>=2.0",
    "passlib>=1.7",
    "bcrypt>=4.3",
    "python-jose",
    "cryptography>=41.0",
    "pydantic>=2",
    "pydantic-settings>=2",
    "python-dateutil>=2.8",
    "python-multipart",
    "starlette",
    "fastapi",
    "uvicorn",
    "nats-py",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
pythonpath = ["../../backend/api"]
testpaths = ["tests"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Anti-Patterns to Avoid

- **Importing backend modules at conftest module level before env vars are set:** `utils/db.py` runs `conf = config.get_config()` and `db = client.db(...)` at module level. Any `import` at the top of conftest.py triggers this before the fixture runs.
- **Importing `db_init.py` directly:** It calls `get_secret()` and `wait_for_db_ready()` at module level — this will FileNotFoundError immediately.
- **Mocking only `utils.nats_client.publish_sync`:** Callers bind the name locally. Must also patch `events.base_event.publish_sync` and other caller namespaces.
- **Using `monkeypatch` for session-scoped fixtures:** `monkeypatch` is function-scoped by default; use manual patching or `pytest-mock`'s `session_mocker` for session scope.
- **Truncating Config/Counter/Queue:** These have default records inserted at schema init. Truncating them breaks tests that rely on defaults. Exclude from truncation or re-seed.
- **Wrapping Event.save() in an outer transaction:** ArangoDB does not support nested transactions. `Event.save()` creates its own transaction internally.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Container lifecycle | Manual Docker SDK calls | testcontainers `GenericContainer` | Handles port mapping, cleanup, wait strategies |
| Async test support | `asyncio.run()` wrappers | `pytest-asyncio` with `asyncio_mode = "auto"` | Handles event loop per test, session-scoped clients |
| Coverage | Manual tracking | `pytest-cov` | Integrates with pytest, generates reports |
| HTTP test client | `requests` against running server | `httpx.AsyncClient` + `ASGITransport` | In-memory, no TCP, no server process needed |

**Key insight:** The hard problem in this phase is import ordering and singleton mutation, not library selection. All libraries are straightforward — the complexity is managing Python's module-level execution side effects.

---

## Common Pitfalls

### Pitfall 1: Local Name Binding Defeats NATS Mock

**What goes wrong:** `publish_sync` called after mock is patched but raises RuntimeError anyway.
**Why it happens:** `from utils.nats_client import publish_sync` binds the name `publish_sync` to the current function object in the calling module's namespace. Patching `utils.nats_client.publish_sync` replaces the attribute on the module, but the local binding in `base_event.py` etc. still points to the original function.
**How to avoid:** Patch the name in every module that imported it: `events.base_event.publish_sync`, `events.inventory.base_inventory.publish_sync`, `events.serial.base_serial.publish_sync`.
**Warning signs:** Tests pass but `publish_sync` mock call count is 0; or tests fail with `RuntimeError: NATS client not connected`.

### Pitfall 2: db Module-Level Singleton Not Patched in auth.py

**What goes wrong:** Events that call auth-related utilities fail with ArangoDB connection error pointing to wrong host.
**Why it happens:** `utils/auth.py` does `from utils.db import db` at import time, binding its own local reference to the original db object. Patching `utils.db.db` does not update `utils.auth.db`.
**How to avoid:** After patching `utils.db.db`, also patch `utils.auth.db = new_db`. Audit all `from utils.db import db` imports.
**Warning signs:** Tests against auth-protected endpoints fail with connection errors to the wrong URL.

### Pitfall 3: db_init.py Module-Level Execution

**What goes wrong:** `import db_init` raises `FileNotFoundError: /run/secrets/progress_db_root_pwd`.
**Why it happens:** `db_init.py` calls `get_secret()` and connects to ArangoDB at module scope — the script was designed to run directly as `python db_init.py` in Docker.
**How to avoid:** Extract the `collections` list and schema creation loop into `conftest_helpers/schema.py`. Do not import from `db_init.py`.
**Warning signs:** ImportError or FileNotFoundError at session fixture startup.

### Pitfall 4: ArangoDB Container Not Ready When Schema Fixture Runs

**What goes wrong:** Schema init fails with connection error even though testcontainer started.
**Why it happens:** Container starting does not mean ArangoDB is accepting connections. Default testcontainers wait strategy (port open) triggers before ArangoDB finishes startup.
**How to avoid:** Add a wait strategy — wait for HTTP 200 on `/_api/version` endpoint. testcontainers `wait_for_logs("is ready for business")` or an HTTP readiness check.
**Warning signs:** `ConnectionRefusedError` or ArangoDB returns 503 during schema init.

### Pitfall 5: pytest-asyncio Mode Configuration

**What goes wrong:** `async def test_*` functions are collected but not actually executed as async — they pass trivially or pytest warns about coroutines.
**Why it happens:** Default `asyncio_mode = "strict"` requires explicit `@pytest.mark.asyncio` on every test function and fixture.
**How to avoid:** Set `asyncio_mode = "auto"` in `[tool.pytest.ini_options]`. This makes all `async def` functions/fixtures async automatically.
**Warning signs:** Tests complete in 0ms; no ArangoDB operations observed; coverage shows 0 lines hit.

### Pitfall 6: Session-Scoped Async Fixtures

**What goes wrong:** Session-scoped `async` fixture fails with "ScopeMismatch: You tried to access the function scoped fixture ... in a session scoped context."
**Why it happens:** `pytest-asyncio` requires explicit scope declaration for session-scoped async fixtures.
**How to avoid:** Decorate with `@pytest.fixture(scope="session")` and configure `asyncio_mode = "auto"`. In pytest-asyncio >= 0.21, also add `@pytest.mark.asyncio(loop_scope="session")` if using a shared event loop.
**Warning signs:** ScopeMismatch error at collection time; or fixture re-runs per test instead of once per session.

### Pitfall 7: Counter Collection Drift

**What goes wrong:** WO code generation tests fail intermittently because the Counter collection `next_tick` increments across tests.
**Why it happens:** Counter is excluded from truncation; `next_tick` drifts between test runs within a session.
**How to avoid:** Factory fixtures that generate WO codes should use a static test code string (e.g., `"WO-TEST-001"`) rather than calling the counter utility.
**Warning signs:** Tests that check WO codes fail on second run within session.

---

## Code Examples

### testcontainers ArangoDB Container

```python
# Source: testcontainers docs + ArangoDB Docker image docs
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

@pytest.fixture(scope="session", autouse=True)
def arango_container():
    container = (
        DockerContainer("arangodb:3.11")
        .with_env("ARANGO_NO_AUTH", "1")
        .with_exposed_ports(8529)
    )
    with container:
        wait_for_logs(container, "is ready for business")
        host = container.get_container_host_ip()
        port = container.get_exposed_port(8529)
        yield f"http://{host}:{port}"
```

Note: `ARANGO_NO_AUTH=1` disables ArangoDB authentication — simplest setup for test containers. All operations use the default root user with empty password.

### Complete db Singleton Override

```python
# Source: analysis of utils/db.py and utils/auth.py module structure

import os
import sys

# Must happen before any backend module is imported
os.environ.update({
    "PROGRESS_ARANGO_URL": "http://placeholder:8529",
    "PROGRESS_DB_NAME": "PROGRESS_TEST",
    "PROGRESS_JWT_SECRET": "test-secret",
    "PROGRESS_API_DB_USERNAME": "root",
    "PROGRESS_API_DB_PWD": "",
    "PROGRESS_NATS_URL": "nats://nowhere:4222",
})

from utils.config import get_config
get_config.cache_clear()

@pytest.fixture(scope="session", autouse=True)
def override_db(arango_container):
    url = arango_container  # the URL yielded by arango_container fixture
    os.environ["PROGRESS_ARANGO_URL"] = url
    get_config.cache_clear()

    from arango import ArangoClient
    import utils.db as db_module
    import utils.auth as auth_module

    new_client = ArangoClient(hosts=url)
    new_db = new_client.db("PROGRESS_TEST", username="root", password="")

    db_module.db = new_db
    db_module.client = new_client
    auth_module.db = new_db

    yield new_db
```

### Factory Smoke Test Pattern

```python
# tests/factories/test_full_graph.py
class TestFactorySmoke:
    """
    Feature: Factory Infrastructure
    All factory fixtures can compose a complete domain object graph
    (WorkOrder -> Job -> Batch -> WorkSession -> StepExecutionData)
    without requiring event dispatch.
    """

    async def test_full_graph_creation(self, db, work_order, job, batch, work_session, step_execution_data):
        """Given factory fixtures are called,
        when all objects are created,
        then each key exists in the database and references are consistent."""
        wo = db.collection('WorkOrder').get(work_order['_key'])
        assert wo is not None
        assert job['wo_key'] == work_order['_key']
        assert batch['job_key'] == job['_key']
        assert work_session['batch_key'] == batch['_key']
        assert step_execution_data['batch_key'] == batch['_key']
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `asyncio_mode = "strict"` (explicit marks) | `asyncio_mode = "auto"` | pytest-asyncio 0.18+ | All async tests work without decorator overhead |
| pytest-asyncio `event_loop` fixture override | `loop_scope` parameter on fixture | pytest-asyncio 0.21+ | Cleaner session-scoped async fixture control |
| testcontainers `ArangoDbContainer` | `GenericContainer` with image | testcontainers 4.x restructure | `GenericContainer` is more flexible; check if `ArangoDbContainer` exists in 4.14 |

**Deprecated/outdated:**
- `@pytest.mark.asyncio` on every test: Replaced by `asyncio_mode = "auto"` in config
- `pytest.ini` or `setup.cfg` for pytest config: Use `[tool.pytest.ini_options]` in `pyproject.toml`
- `@app.on_event("startup")` / `@app.on_event("shutdown")`: Deprecated in FastAPI (but still works); when using ASGITransport the lifespan events DO run, which means `startup_event()` in `main.py` will try to connect to NATS — the NATS mock must cover this

---

## Open Questions

1. **Does testcontainers 4.14 include `ArangoDbContainer`?**
   - What we know: testcontainers Python has community-maintained database modules
   - What's unclear: Whether `ArangoDbContainer` is available or if we need `GenericContainer`
   - Recommendation: Use `GenericContainer("arangodb:3.11")` — it's explicit and does not depend on a community module

2. **Does ASGITransport trigger FastAPI startup_event?**
   - What we know: `startup_event()` in `main.py` calls `nats_client.connect()` which tries to connect to NATS
   - What's unclear: Whether `httpx.AsyncClient(transport=ASGITransport(app))` triggers the lifespan
   - Recommendation: NATS mock must prevent the connection attempt. If `startup_event` runs, `nats_client.connect()` must be mocked OR `nats_url` must point to a mock. Safest: also mock `utils.nats_client.connect` to return a MagicMock.

3. **conftest.py split strategy**
   - What we know: Claude's Discretion (CONTEXT.md)
   - Recommendation: Single root `conftest.py` for infrastructure fixtures (db, client, truncation, NATS mock); per-domain conftest files (`tests/factories/conftest.py`, `tests/step/conftest.py`, etc.) for domain-specific factories. This avoids a 500-line root conftest and keeps factory fixtures close to the tests that use them.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|---------|
| Python 3.11 | Backend source compatibility | Yes | 3.11.14 | — |
| uv | Dependency management (INFRA-08) | Yes | 0.9.27 | — |
| Docker CLI | testcontainers (INFRA-01) | Yes | 28.5.1 | — |
| Docker daemon | testcontainers container startup | NOT RUNNING | — | Must start Docker Desktop before running tests |
| ArangoDB 3.11 image | INFRA-01 container | Pulled on first run | — | `docker pull arangodb:3.11` |

**Missing dependencies with no fallback:**
- Docker daemon must be running for testcontainers. `docker info` returns error currently — developer must start Docker Desktop before `pytest`.

**Missing dependencies with fallback:**
- None.

---

## Sources

### Primary (HIGH confidence)

- Direct code analysis: `backend/api/utils/db.py` — module-level singleton confirmed
- Direct code analysis: `backend/api/utils/config.py` — `@lru_cache()` on `get_config()` confirmed
- Direct code analysis: `backend/api/utils/nats_client.py` — `publish_sync` local binding pattern confirmed
- Direct code analysis: `backend/api/utils/auth.py` — `from utils.db import db` at import time confirmed
- Direct code analysis: `deploy/scripts/db_init.py` — module-level `get_secret()` / `wait_for_db_ready()` confirmed; `collections` list structure confirmed
- Direct code analysis: `backend/api/events/base_event.py` — transaction model, `publish_sync` import confirmed
- Direct code analysis: `backend/api/main.py` — `startup_event` NATS connect call confirmed
- PyPI registry: testcontainers 4.14.2, pytest 9.0.3, pytest-asyncio 1.3.0, httpx 0.28.1, pytest-cov 7.1.0 (verified 2026-04-09)
- `km/testing/strategy.md` — real database requirement, fixture approach, httpx + pytest-asyncio stack

### Secondary (MEDIUM confidence)

- testcontainers Python docs: `GenericContainer` API and wait strategy patterns
- pytest-asyncio docs: `asyncio_mode = "auto"` and `loop_scope` behavior
- FastAPI testing docs: `ASGITransport` and `app.dependency_overrides` pattern

### Tertiary (LOW confidence)

- ASGITransport lifespan trigger behavior — needs validation in smoke test (Open Question #2)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions verified from PyPI; library choices confirmed by strategy.md
- Architecture patterns: HIGH — derived from direct code analysis of actual modules
- Pitfalls: HIGH — import-order and local-binding pitfalls confirmed by reading actual source
- NATS mock target: HIGH — all four caller sites confirmed by grep

**Research date:** 2026-04-09
**Valid until:** 2026-07-09 (stable libraries; testcontainers API may change faster — verify on use)
