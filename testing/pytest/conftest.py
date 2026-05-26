"""Repo-root pytest conftest.

Defines session-scope autouse fixtures that spin up a real ArangoDB
testcontainer, patch the `db` singleton, and mock NATS. Every test
inheriting from this conftest pays the testcontainer startup cost
(~8s) regardless of whether it touches the DB.

Pure-Python tests that do NOT need ArangoDB / NATS / event-class
imports live under `tests/unit/`. That subtree has its own conftest
(`tests/unit/conftest.py`) which overrides each autouse fixture here
with a no-op of the same name so unit tests run without Docker. See
`tests/unit/conftest.py` and `.planning/codebase/TESTING.md` § "Unit
Tests — No Docker, No ArangoDB" for the full rule.
"""
import os
import sys
import types
import uuid
import pytest
import asyncio
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# SECTION 0: Stub system-library-dependent modules BEFORE any backend import
# weasyprint requires native GTK/pango system libraries (libgobject-2.0-0, etc.)
# that are not available on macOS dev machines or minimal CI environments.
# We stub it out so endpoints that import it (endpoints/serial.py → utils/dhr.py)
# can be imported without error.  The actual PDF rendering is never called in tests.
# ---------------------------------------------------------------------------
_weasyprint_stub = types.ModuleType("weasyprint")
_weasyprint_stub.HTML = lambda *args, **kwargs: None
_weasyprint_stub.CSS = lambda *args, **kwargs: None
sys.modules.setdefault("weasyprint", _weasyprint_stub)
sys.modules.setdefault("weasyprint.text", types.ModuleType("weasyprint.text"))
sys.modules.setdefault("weasyprint.text.fonts", types.ModuleType("weasyprint.text.fonts"))

# CRITICAL: Set env vars BEFORE any backend module is imported (D-15)
# utils/db.py executes `conf = config.get_config()` and `db = client.db(...)` at module level
os.environ.update({
    "PROGRESS_ARANGO_URL": "http://placeholder:8529",
    "PROGRESS_DB_NAME": "PROGRESS_TEST",
    "PROGRESS_JWT_SECRET": "test-secret-key-not-for-production",
    "PROGRESS_API_DB_USERNAME": "root",
    "PROGRESS_API_DB_PWD": "",
    "PROGRESS_NATS_URL": "nats://nowhere:4222",
    "PROGRESS_MEDIA_PATH": "/tmp/test-media",
    "PROGRESS_API_ROOT_PATH": "/api",
})

# Clear lru_cache so get_config() re-reads env vars
from utils.config import get_config
get_config.cache_clear()

# NOW safe to import backend modules

from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs
import httpx
from httpx import ASGITransport


# ---------------------------------------------------------------------------
# SECTION 2: ArangoDB container fixture (session scope, autouse) — INFRA-01
# ---------------------------------------------------------------------------

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
        url = f"http://{host}:{port}"
        yield {"url": url, "host": host, "port": port}


# ---------------------------------------------------------------------------
# SECTION 3: db singleton override (session scope, autouse) — INFRA-03
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def db(arango_container):
    url = arango_container["url"]
    os.environ["PROGRESS_ARANGO_URL"] = url
    get_config.cache_clear()

    from arango import ArangoClient
    import utils.db as db_module
    from utils.db import encoder

    # Create new client and db pointing to testcontainer.
    # Pass the same pydantic serializer used in production so that
    # transaction.collection().insert(pydantic_model) serializes correctly.
    new_client = ArangoClient(hosts=url, serializer=encoder)
    # Create the PROGRESS_TEST database using sys db first
    sys_db = new_client.db("_system", username="root", password="")

    # Initialize schema (creates PROGRESS_TEST db + all collections) — INFRA-02, D-03
    from conftest_helpers.schema import initialize_schema
    initialize_schema(sys_db)

    # Re-get the PROGRESS_TEST db handle from new_client (which has the pydantic serializer).
    # initialize_schema creates its own bare ArangoClient internally — we must get the handle
    # via new_client so that transaction inserts of pydantic models serialize correctly.
    test_db = new_client.db("PROGRESS_TEST", username="root", password="")

    # Override the module-level singletons
    db_module.db = test_db
    db_module.client = new_client

    # CRITICAL: Patch ALL modules that did `from utils.db import db` at import time
    # They captured a local reference to the original db object
    import utils.auth as auth_module
    auth_module.db = test_db

    yield test_db


# ---------------------------------------------------------------------------
# SECTION 4: NATS mock fixture (session scope, autouse) — INFRA-04, D-16
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def mock_nats(db):  # depends on db to ensure backend modules are imported first
    import utils.nats_client as nats_module

    # Mock connect to prevent startup_event from connecting to real NATS
    original_connect = nats_module.connect
    async def mock_connect(url):
        return None
    nats_module.connect = mock_connect

    # Mock publish_sync — must patch in every module that imported it locally
    noop = lambda subject, data: None

    nats_module.publish_sync = noop

    # These modules do `from utils.nats_client import publish_sync` — local binding
    import events.base_event as base_event_mod
    import events.inventory.base_inventory as base_inv_mod
    import events.serial.base_serial as base_serial_mod
    import endpoints.print as print_mod

    base_event_mod.publish_sync = noop
    base_inv_mod.publish_sync = noop
    base_serial_mod.publish_sync = noop
    print_mod.publish_sync = noop

    # CRITICAL: base_event.py does `from utils.db import db` at import time, capturing
    # a reference to the placeholder db. Test files may import event classes at module
    # level (collection time), before any fixtures run. Patch the local binding here
    # so that event.save() uses the testcontainer db.
    base_event_mod.db = db

    # Also mock drain for shutdown
    original_drain = nats_module.drain
    async def mock_drain():
        return None
    nats_module.drain = mock_drain

    yield

    # Restore originals
    nats_module.connect = original_connect
    nats_module.publish_sync = lambda subject, data: None  # keep noop for safety
    nats_module.drain = original_drain


# ---------------------------------------------------------------------------
# SECTION 5: httpx AsyncClient fixture (session scope) — INFRA-05, D-10
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
async def client(db, mock_nats):
    from main import app
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as c:
        yield c


# ---------------------------------------------------------------------------
# SECTION 6: Auth override fixture (function scope) — INFRA-06, D-11
# ---------------------------------------------------------------------------

@pytest.fixture
def auth_headers():
    """Returns a factory function that generates auth headers with configurable scope."""
    from main import app
    from utils.auth import verify_token

    def _make_headers(scope: str = "operator production admin quality warehouse"):
        from models.auth import TokenData, TokenContext
        from datetime import datetime, timedelta
        token_data = TokenData(
            jti="test-token-key",
            sub="test-user-key",
            ctyp="user",
            iat=datetime.utcnow(),
            exp=datetime.utcnow() + timedelta(hours=1),
            ctx=TokenContext.USER_SESSION,
            scope=scope,
        )
        app.dependency_overrides[verify_token] = lambda: token_data
        return {"Authorization": "Bearer test-token"}

    yield _make_headers

    from main import app
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# SECTION 7: Collection truncation fixture (function scope, autouse) — INFRA-07, D-13
# ---------------------------------------------------------------------------

EDGE_COLLECTIONS = [
    'batch_serial', 'can_use_print_template', 'contains', 'event_source',
    'has_tag', 'inventory_count_position_complete', 'inventory_count_record',
    'issue_rel', 'media_connection', 'message', 'movement',
    'requires', 'task_rel', 'wip',
]
# These have default records from schema init — do NOT truncate
# is_in_position is an edge collection with defaults 'IN'/'OUT' — must be preserved
SKIP_TRUNCATE = {'Config', 'Counter', 'CustomField', 'Queue', 'is_in_position'}

# Snapshot of Config defaults from schema init — used to restore after each test.
# seed_config() mutates these (e.g. enable_inventory_management True→False),
# and Config is in SKIP_TRUNCATE so truncation alone doesn't reset them.
_CONFIG_DEFAULTS = None


@pytest.fixture(scope="session", autouse=True)
def _capture_config_defaults(db):
    """Capture Config defaults once after schema init for per-test restoration."""
    global _CONFIG_DEFAULTS
    config_col = db.collection("Config")
    _CONFIG_DEFAULTS = {doc["_key"]: doc for doc in config_col.all()}


@pytest.fixture(autouse=True)
def truncate_collections(db):
    yield
    # Truncate edges first (D-13: edges before documents)
    for name in EDGE_COLLECTIONS:
        try:
            db.collection(name).truncate()
        except Exception:
            pass
    # Then document collections (skip defaults)
    for c in db.collections():
        cname = c['name']
        if not c['system'] and cname not in SKIP_TRUNCATE and not cname[0].islower():
            try:
                db.collection(cname).truncate()
            except Exception:
                pass
    # Restore Config defaults — undo any seed_config() mutations
    # Also delete any Config keys that were inserted by tests (not in original snapshot)
    if _CONFIG_DEFAULTS:
        config_col = db.collection("Config")
        current_keys = {doc["_key"] for doc in config_col.all()}
        extra_keys = current_keys - set(_CONFIG_DEFAULTS.keys())
        for key in extra_keys:
            try:
                config_col.delete(key)
            except Exception:
                pass
        for key, doc in _CONFIG_DEFAULTS.items():
            try:
                # Strip _rev to avoid optimistic locking conflicts — we want to force restore
                restore_doc = {k: v for k, v in doc.items() if k != "_rev"}
                config_col.update(restore_doc, check_rev=False)
            except Exception:
                pass


# ===========================================================================
# FACTORY FIXTURES (FACT-01 through FACT-14)
# Defined here (root conftest) so they are available to ALL test subdirectories
# without any pytest_plugins re-registration.
#
# Per D-12: function scope, raw db.collection().insert(), never create_as_child().
# Per D-14: Config document seeding available via seed_config fixture.
# ===========================================================================

def _key():
    """Generate a short unique key suitable for test document _key fields."""
    return str(uuid.uuid4())[:8]


def _now():
    """Return current UTC datetime as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# FACT-01: User factory
# ---------------------------------------------------------------------------

@pytest.fixture
def create_user(db):
    """FACT-01: User factory — creates users with configurable scope strings.

    Scope is a space-separated string: 'operator', 'production', 'admin',
    'quality', 'warehouse', etc.

    The psw_hash is a static bcrypt hash for the password 'test'.
    Tests that need to authenticate via the API should use auth_headers fixture
    instead of calling verify_password directly.
    """
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
            # Static bcrypt hash for the password 'test' — avoids passlib import at fixture time
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


# ---------------------------------------------------------------------------
# FACT-02: Product factory
# ---------------------------------------------------------------------------

@pytest.fixture
def create_product(db):
    """FACT-02: Product factory — creates a product with Phase, Operation, and Step documents.

    Creates Product + Operation + Phase + Step documents.

    Does NOT create CustomField documents.  The `form_fields` parameter accepts
    a list of dicts, each containing a 'field_key' pointing to an already-existing
    CustomField document's _key.  That key is stored as `form_field_key` on the
    corresponding Step document.

    Tests needing CustomField documents must insert them separately via
    db.collection("CustomField").insert(...) before calling this factory.

    Returns a dict with keys:
        product         — the Product document dict
        phases          — list of Phase document dicts (one per phase)
        operations      — list of Operation document dicts (one per phase)
        steps           — list of Step document dicts (num_phases * steps_per_phase)
        product_key     — shortcut to product["_key"]
    """
    def _create(
        num_phases: int = 1,
        steps_per_phase: int = 1,
        form_fields: list = None,
        traceability_level: str = None,  # None, "batch", "serial"
        **product_overrides,
    ):
        product_key = _key()
        product = {
            "_key": product_key,
            "code": f"PROD-{product_key}",
            "description": f"Test Product {product_key}",
            "active": True,
            "trash": False,
            "technical_batch_qt": 0,
            "minimum_order_qt": 0,
            "process_phases": [],
            **product_overrides,
        }
        if traceability_level is not None:
            product["traceability_level"] = traceability_level
        db.collection("Product").insert(product)

        phases = []
        operations = []
        steps = []
        step_global_idx = 0

        for p_idx in range(num_phases):
            op_key = _key()
            operation = {
                "_key": op_key,
                "name": f"Operation {p_idx + 1}",
                "code": f"OP-{op_key}",
            }
            db.collection("Operation").insert(operation)
            operations.append(operation)

            phase_key = _key()
            phase = {
                "_key": phase_key,
                "product_key": product_key,
                "operation_key": op_key,
                "order": p_idx,
                "name": f"Phase {p_idx + 1}",
                "alias": f"P{p_idx + 1}",
            }
            db.collection("Phase").insert(phase)
            phases.append(phase)

            for s_idx in range(steps_per_phase):
                step_key = _key()
                step = {
                    "_key": step_key,
                    "phase_key": phase_key,
                    "operation_key": op_key,
                    "product_key": product_key,
                    "title": f"Step {s_idx + 1}",
                    "order": s_idx,
                    "type": "instruction",
                    "checks": [],
                    "input_fields": [],
                }
                # If form_fields provided for this step, set the reference key.
                # form_fields[i] must be a dict with 'field_key' pointing to
                # an already-existing CustomField document's _key.
                if form_fields and step_global_idx < len(form_fields):
                    step["form_field_key"] = form_fields[step_global_idx].get("field_key")
                db.collection("Step").insert(step)
                steps.append(step)
                step_global_idx += 1

        return {
            "product": product,
            "phases": phases,
            "operations": operations,
            "steps": steps,
            "product_key": product_key,
        }

    return _create


# ---------------------------------------------------------------------------
# FACT-03: BOM factory
# ---------------------------------------------------------------------------

@pytest.fixture
def create_bom(db):
    """FACT-03: BOM factory — creates bill-of-materials edges between products.

    Inserts a 'requires' edge from parent_product_key to component_product_key.
    The 'requires' is an edge collection linking Product documents.
    """
    def _create(
        parent_product_key: str,
        component_product_key: str,
        quantity: float = 1.0,
        **overrides,
    ):
        edge = {
            "_from": f"Product/{parent_product_key}",
            "_to": f"Product/{component_product_key}",
            "quantity": quantity,
            **overrides,
        }
        db.collection("requires").insert(edge)
        return edge

    return _create


# ---------------------------------------------------------------------------
# FACT-04: WorkOrder factory
# ---------------------------------------------------------------------------

@pytest.fixture
def create_work_order(db):
    """FACT-04: WorkOrder factory — creates work orders linked to products.

    Uses generated wo_code (not the counter-based autogeneration) to avoid
    counter drift between tests.

    Field names verified against WorkOrderFull (backend/api/models/production.py):
        wo_code, product_key, qt_planned, status (WorkStatus string value)

    wo_bom: [] — required by GET_WORKING_JOB_DATA AQL:
        FOR bom_line IN DOCUMENT(WorkOrder, j.wo_key).wo_bom
        Returns null if field is missing, crashing AQL with ERR 1563.
    """
    def _create(
        product_key: str,
        product_code: str = None,
        product_description: str = None,
        qt_planned: float = 10.0,
        status: str = "created",
        **overrides,
    ):
        key = _key()
        doc = {
            "_key": key,
            "wo_code": f"WO-TEST-{key}",
            "product_key": product_key,
            "product_code": product_code or f"PROD-{product_key}",
            "product_description": product_description or f"Test Product {product_key}",
            "qt_planned": qt_planned,
            "qt_completed": 0.0,
            "status": status,
            "active": False,
            "on_time": True,
            "critical": False,
            "progress": 0,
            "priority": False,
            "phase_sequence": [],
            "wo_docs": [],
            "wo_bom": [],  # required by GET_WORKING_JOB_DATA AQL: FOR bom_line IN DOCUMENT(WorkOrder, j.wo_key).wo_bom — null crashes with ERR 1563
            "created": _now(),
            **overrides,
        }
        db.collection("WorkOrder").insert(doc)
        return doc

    return _create


# ---------------------------------------------------------------------------
# FACT-05: Job factory
# ---------------------------------------------------------------------------

@pytest.fixture
def create_job(db):
    """FACT-05: Job factory — creates jobs linked to work orders and phases.

    Field names verified against Job model (backend/api/models/production.py):
        wo_key, wo_code, phase_key, phase_alias, product_key, product_code,
        product_description, operation_key, qt_planned, stage (WorkStatus string),
        active_batch_key, parameters (PhaseParameters as dict).

    Key configurable parameters:
        step_check      — whether step-by-step completion is enforced (maps to parameters.step_check)
        auto_new_batch  — whether to auto-create the next batch after completion
        production_batch_qt — quantity per batch
        std_processing_time — standard processing time in seconds
    """
    def _create(
        wo_key: str,
        phase_key: str,
        wo_code: str = None,
        phase_alias: str = None,
        product_key: str = None,
        product_code: str = None,
        product_description: str = None,
        operation_key: str = None,
        assigned_to: str = None,
        step_check: bool = False,
        auto_new_batch: bool = False,
        production_batch_qt: int = 1,
        std_processing_time: int = 60,
        stage: str = "created",
        qt_planned: float = 10.0,
        first_phase: bool = True,
        last_phase: bool = True,
        **overrides,
    ):
        key = _key()
        doc = {
            "_key": key,
            "wo_key": wo_key,
            "wo_code": wo_code or f"WO-TEST-{wo_key}",
            "phase_key": phase_key,
            "phase_alias": phase_alias or f"P-{phase_key}",
            "product_key": product_key or "unknown",
            "product_code": product_code or "PROD-unknown",
            "product_description": product_description or "Test Product",
            "operation_key": operation_key or "unknown",
            "stage": stage,
            "active": False,
            "critical": False,
            "qt_planned": qt_planned,
            "qt_completed": 0.0,
            "qt_released": 0.0,
            "progress": 0,
            "active_batch_key": None,
            "active_batch_qt": 0,
            "assigned_to": assigned_to,
            "first_phase": first_phase,
            "last_phase": last_phase,
            "next_batch_available": False,
            "on_time": True,
            "last_work_session_started": None,
            "step_sequence": [],
            # PhaseParameters as a plain dict — events read these via job.parameters.*
            "parameters": {
                "parallel_job_allowed": True,
                "step_check": step_check,
                "step_check_force_order": False,
                "production_batch_qt": production_batch_qt,
                "max_offline": 300,
                "auto_new_batch": auto_new_batch,
            },
            **overrides,
        }
        db.collection("Job").insert(doc)
        return doc

    return _create


# ---------------------------------------------------------------------------
# FACT-06: Batch factory
# ---------------------------------------------------------------------------

@pytest.fixture
def create_batch(db):
    """FACT-06: Batch factory — creates batches linked to jobs.

    Field names verified against Batch model (backend/api/models/traceability.py):
        job_key, phase_key, work_order_key, product_key (optional),
        qt_total, qt_pass, qt_scrap, start (required), active, canceled (string|None).

    Note: `canceled` is a string (event id) when canceled, None when not.
    """
    def _create(
        job_key: str,
        work_order_key: str = None,
        phase_key: str = None,
        product_key: str = None,
        qt_total: float = 1.0,
        qt_pass: float = 0.0,
        qt_scrap: float = 0.0,
        active: bool = True,
        canceled: str = None,
        **overrides,
    ):
        key = _key()
        doc = {
            "_key": key,
            "job_key": job_key,
            "work_order_key": work_order_key or "unknown",
            "phase_key": phase_key or "unknown",
            "qt_total": qt_total,
            "qt_pass": qt_pass,
            "qt_scrap": qt_scrap,
            "active": active,
            "start": _now(),
            "end": None,
            "unit_material_cost": 0.0,
            "value": 0.0,
            "canceled": canceled,
        }
        if product_key is not None:
            doc["product_key"] = product_key
        doc.update(overrides)
        db.collection("Batch").insert(doc)
        return doc

    return _create


# ---------------------------------------------------------------------------
# FACT-07: WorkSession factory
# ---------------------------------------------------------------------------

@pytest.fixture
def create_work_session(db):
    """FACT-07: WorkSession factory — creates work sessions linked to batches.

    Field names verified against WorkSession model (backend/api/models/traceability.py):
        user_session_key (optional), batch_key, job_key, phase_key,
        work_order_key, product_key, user_key (optional), start, end, active.

    Note: `canceled` is a string (event id) when canceled, None when not.
    """
    def _create(
        batch_key: str,
        job_key: str,
        work_order_key: str = None,
        phase_key: str = None,
        product_key: str = None,
        user_key: str = None,
        user_session_key: str = None,
        active: bool = True,
        canceled: str = None,
        **overrides,
    ):
        key = _key()
        doc = {
            "_key": key,
            "batch_key": batch_key,
            "job_key": job_key,
            "work_order_key": work_order_key or "unknown",
            "phase_key": phase_key or "unknown",
            "product_key": product_key or "unknown",
            "user_key": user_key,
            "user_session_key": user_session_key,
            "active": active,
            "start": _now(),
            "end": None,
            "duration": None,
            "hourly_cost": None,
            "canceled": canceled,
            **overrides,
        }
        db.collection("WorkSession").insert(doc)
        return doc

    return _create


# ---------------------------------------------------------------------------
# FACT-08: StepExecutionData factory
# ---------------------------------------------------------------------------

@pytest.fixture
def create_step_execution(db):
    """FACT-08: StepExecutionData factory — creates step execution records.

    Field names verified against StepExecutionData model (backend/api/models/traceability.py):
        job_key, user_key, work_session_key, batch_key, step_key,
        completed (datetime), status (StepStatus string value), form_data (list),
        modified (string|None), canceled (string|None).

    Note: `canceled` and `modified` are string event ids when set, None otherwise.
    """
    def _create(
        batch_key: str,
        step_key: str,
        job_key: str = None,
        user_key: str = None,
        work_session_key: str = None,
        status: str = "to_do",
        form_data: list = None,
        canceled: str = None,
        **overrides,
    ):
        key = _key()
        doc = {
            "_key": key,
            "batch_key": batch_key,
            "step_key": step_key,
            "job_key": job_key,
            "user_key": user_key,
            "work_session_key": work_session_key,
            "status": status,
            "form_data": form_data or [],
            "completed": None,
            "modified": None,
            "canceled": canceled,
            **overrides,
        }
        db.collection("StepExecutionData").insert(doc)
        return doc

    return _create


# ---------------------------------------------------------------------------
# FACT-09: Config factory
# ---------------------------------------------------------------------------

@pytest.fixture
def seed_config(db):
    """FACT-09: Config document factory — upserts Config records.

    Per D-14: Config seeding is required to control event branches
    (e.g., enable_inventory_management controls whether BatchCompletedEvent
    generates inventory movements).

    The schema init (via conftest.py initialize_schema) already inserts defaults;
    this fixture allows overriding specific config keys for test scenarios.

    Usage:
        seed_config("enable_inventory_management", value=True)
        seed_config("default_operation_parameters", step_check=True)
    """
    def _seed(key: str, **values):
        config_col = db.collection("Config")
        existing = config_col.get(key)
        if existing:
            config_col.update({"_key": key, **values})
        else:
            config_col.insert({"_key": key, **values})
        return config_col.get(key)

    return _seed


# ---------------------------------------------------------------------------
# FACT-11: Serial factory
# ---------------------------------------------------------------------------

@pytest.fixture
def create_serial(db):
    """FACT-11: Serial factory — creates serial records linked to products.

    Field names verified against Serial model (backend/api/models/serial.py):
        code (uppercased string), product_key, wo_key, released (datetime|None).

    Note: `released` is a datetime (not bool) in the actual model — None means unreleased.
    """
    def _create(
        product_key: str,
        code: str | None = None,
        wo_key: str | None = None,
        released: "datetime | None" = None,
        **overrides
    ):
        key = _key()
        doc = {
            "_key": key,
            "product_key": product_key,
            "code": (code or f"SN-{key}").upper(),
            "wo_key": wo_key,
            "released": released,
            "created": _now(),
            "deleted": False,
            **overrides,
        }
        db.collection("Serial").insert(doc)
        return doc

    return _create


# ---------------------------------------------------------------------------
# FACT-12: WIP factory
# ---------------------------------------------------------------------------

@pytest.fixture
def create_wip(db):
    """FACT-12: WIP factory — creates work-in-progress edge records between phases.

    The 'wip' edge collection links Phase documents:
        _from = Phase/{source_phase_key}
        _to   = Phase/{target_phase_key}

    Field names verified against WIPDeclaredEvent (backend/api/events/wip/wip_declared.py):
        _from, _to, wo_key, product_key, quantity, serial_key, active.

    Note: `active=False` matches newly declared (unbooked) WIP in the production system.
    Booked WIP has _to pointing to Job/{job_key} and active=True.
    """
    def _create(
        from_phase_key: str,
        to_phase_key: str,
        wo_key: str,
        product_key: str | None = None,
        quantity: int = 1,
        active: bool = False,
        serial_key: str | None = None,
        **overrides
    ):
        edge = {
            "_from": f"Phase/{from_phase_key}",
            "_to": f"Phase/{to_phase_key}",
            "wo_key": wo_key,
            "quantity": quantity,
            "active": active,
            "serial_key": serial_key,
            **overrides,
        }
        if product_key is not None:
            edge["product_key"] = product_key
        result = db.collection("wip").insert(edge)
        edge["_key"] = result["_key"]
        return edge

    return _create


# ---------------------------------------------------------------------------
# FACT-13: Position factory
# ---------------------------------------------------------------------------

@pytest.fixture
def create_position(db):
    """FACT-13: Inventory position factory — creates Position documents.

    Note: 'IN' and 'OUT' positions are created by schema init as default records.
    This factory creates ADDITIONAL custom positions for inventory movement tests.

    Field names verified against Position model via db_init.py and utils/inventory.py.
    """
    def _create(
        code: str | None = None,
        owned: bool = True,
        available: bool = True,
        disposable: bool = False,
        **overrides
    ):
        key = _key()
        pos_code = code or f"POS-{key}"
        doc = {
            "_key": key,
            "code": pos_code,
            "owned": owned,
            "available": available,
            "disposable": disposable,
            "fixed": False,
            "deleted": False,
            **overrides,
        }
        db.collection("Position").insert(doc)
        return doc

    return _create


# ---------------------------------------------------------------------------
# Helper: create_inventory_at_position
# ---------------------------------------------------------------------------

@pytest.fixture
def create_inventory_at_position(db):
    """Helper: Add inventory (product quantity) at a position via is_in_position edge.

    Creates the edge record that represents stock at a location.
    _from = Product/{product_key}   (matches InventoryChangedEvent orientation)
    _to   = Position/{position_key}
    """
    def _create(
        position_key: str,
        product_key: str,
        quantity: float = 1.0,
        serial_key: str | None = None,
        **overrides
    ):
        edge = {
            "_from": f"Product/{product_key}",
            "_to": f"Position/{position_key}",
            "quantity": quantity,
            "serial_key": serial_key,
            **overrides,
        }
        result = db.collection("is_in_position").insert(edge)
        edge["_key"] = result["_key"]
        return edge

    return _create


# ---------------------------------------------------------------------------
# FACT-14: Queue factory
# ---------------------------------------------------------------------------

@pytest.fixture
def create_queue(db):
    """FACT-14: Queue factory — creates operator queue records.

    The site queue (type='s') already exists from schema init defaults and is
    preserved by SKIP_TRUNCATE in conftest.py.
    This factory creates operator queues (type='o') for job assignment tests.

    Field names verified against db_init.py Queue default_records and
    Queue collection indexes (subqueue_target_key, type, independent).
    """
    def _create(
        user_key: str,
        work_orders: list | None = None,
        **overrides
    ):
        key = _key()
        doc = {
            "_key": key,
            "type": "o",
            "subqueue_target_key": user_key,
            "independent": False,
            "work_orders": work_orders or [],
            **overrides,
        }
        db.collection("Queue").insert(doc)
        return doc

    return _create


# ---------------------------------------------------------------------------
# FACT-10: Parametrized production graph builder
# ---------------------------------------------------------------------------

@pytest.fixture
def create_production_graph(
    db,
    create_user,
    create_product,
    create_work_order,
    create_job,
    create_batch,
    create_work_session,
    create_step_execution,
    seed_config,
    create_bom,
    create_serial,
    create_wip,
    create_position,
    create_inventory_at_position,
):
    """FACT-10: Parametrized builder — combines flags to create correctly linked domain object graphs.

    Flags:
        first_phase          — if False, creates upstream phase + WIP edge pointing to target phase
        last_phase           — if False, creates downstream phase (product has an extra phase after target)
        traceability_level   — "none" | "batch" | "serial" — controls Serial creation
        warehouse_management — if True, seeds Config to enable inventory management
        auto_new_batch       — sets job.parameters.auto_new_batch
        step_check           — sets job.parameters.step_check
        num_steps            — steps per phase
        batch_qt             — qt_total for the batch and production_batch_qt for the job
        with_bom             — if True, creates a component product and BOM (requires) edge

    Returns:
        dict with keys: user, product, work_order, job, batch, work_session,
        step_executions, target_phase, target_phase_idx, wip_records, serials, bom_data
    """
    def _create(
        first_phase: bool = True,
        last_phase: bool = True,
        traceability_level: str = "none",
        warehouse_management: bool = False,
        auto_new_batch: bool = False,
        step_check: bool = False,
        num_steps: int = 1,
        batch_qt: int = 1,
        with_bom: bool = False,
    ):
        # Determine how many phases the product needs:
        #   always 1 for the target phase
        #   +1 upstream if not first_phase
        #   +1 downstream if not last_phase
        total_phases = 1
        if not first_phase:
            total_phases += 1
        if not last_phase:
            total_phases += 1

        # Create user
        user = create_user()

        # Create product
        tl = traceability_level if traceability_level != "none" else None
        product_data = create_product(
            num_phases=total_phases,
            steps_per_phase=num_steps,
            traceability_level=tl,
        )

        # Identify the target phase index:
        #   - If first_phase is False, upstream phase is index 0, target is index 1
        #   - Otherwise target is index 0
        phases = product_data["phases"]
        target_phase_idx = 1 if not first_phase else 0
        target_phase = phases[target_phase_idx]

        # Create work order
        wo = create_work_order(
            product_key=product_data["product_key"],
            qt_planned=float(batch_qt * 10),
        )

        # Create job at target phase — pass first_phase/last_phase flags so
        # BatchCompletedEvent reads them correctly from the Job document.
        # product_key must match so PRODUCTS_INVENTORY_CONFIG can find the product.
        job_extra = {}
        if tl is not None:
            job_extra["traceability_level"] = tl

        job = create_job(
            wo_key=wo["_key"],
            phase_key=target_phase["_key"],
            assigned_to=user["_key"],
            step_check=step_check,
            auto_new_batch=auto_new_batch,
            production_batch_qt=batch_qt,
            first_phase=first_phase,
            last_phase=last_phase,
            product_key=product_data["product_key"],
            operation_key=target_phase.get("operation_key", "unknown"),
            **job_extra,
        )

        # Create batch — create_batch uses `work_order_key` (not wo_key) and `phase_key`
        batch = create_batch(
            job_key=job["_key"],
            work_order_key=wo["_key"],
            phase_key=target_phase["_key"],
            qt_total=float(batch_qt),
        )

        # Update job with active_batch_key so BatchCompletedEvent can find it
        db.collection("Job").update({"_key": job["_key"], "active_batch_key": batch["_key"]})
        job["active_batch_key"] = batch["_key"]

        # Create work session — create_work_session uses `work_order_key` (not wo_key)
        ws = create_work_session(
            batch_key=batch["_key"],
            job_key=job["_key"],
            work_order_key=wo["_key"],
            phase_key=target_phase["_key"],
        )

        # Create step executions for steps belonging to the target phase
        step_execs = []
        target_steps = [s for s in product_data["steps"] if s.get("phase_key") == target_phase["_key"]]
        for step in target_steps:
            sxd = create_step_execution(
                batch_key=batch["_key"],
                step_key=step["_key"],
                job_key=job["_key"],
            )
            step_execs.append(sxd)

        # Handle WIP for non-first phase: create an available WIP edge pointing to target phase
        wip_records = []
        if not first_phase:
            upstream_phase = phases[target_phase_idx - 1]
            wip = create_wip(
                from_phase_key=upstream_phase["_key"],
                to_phase_key=target_phase["_key"],
                wo_key=wo["_key"],
                product_key=product_data["product_key"],
                quantity=batch_qt,
            )
            wip_records.append(wip)

        # Warehouse management: seed Config flag + enable product-level inventory tracking
        if warehouse_management:
            seed_config("enable_inventory_management", value=True)
            # Product must have manage_inventory=True for PRODUCTS_INVENTORY_CONFIG to return True
            db.collection("Product").update({
                "_key": product_data["product_key"],
                "manage_inventory": True,
            })

        # BOM: create a component product and a requires edge
        bom_data = None
        if with_bom:
            component = create_product(num_phases=1, steps_per_phase=1)
            bom_edge = create_bom(
                parent_product_key=product_data["product_key"],
                component_product_key=component["product_key"],
                quantity=1.0,
            )
            bom_data = {
                "component_product": component,
                "bom_edge": bom_edge,
            }

        # Serials: create one per batch unit when traceability is enabled.
        # Also create batch_serial edges so GET_BATCH_SERIALS AQL traversal works
        # (BatchCompletedEvent._handle_batch_serials re-fetches via AQL, not passed keys).
        serials = []
        if traceability_level in ("batch", "serial"):
            for _ in range(batch_qt):
                serial = create_serial(
                    product_key=product_data["product_key"],
                    wo_key=wo["_key"],
                )
                serials.append(serial)
                # Link serial to batch via batch_serial edge collection
                db.collection("batch_serial").insert({
                    "_from": f"Batch/{batch['_key']}",
                    "_to": f"Serial/{serial['_key']}",
                })

        return {
            "user": user,
            "product": product_data,
            "work_order": wo,
            "job": job,
            "batch": batch,
            "work_session": ws,
            "step_executions": step_execs,
            "target_phase": target_phase,
            "target_phase_idx": target_phase_idx,
            "wip_records": wip_records,
            "serials": serials,
            "bom_data": bom_data,
        }

    return _create


# ---------------------------------------------------------------------------
# SECTION 8: Authenticated client fixture — AUTH-01
# Used by auth migration tests (Phase 5) and all subsequent phases (6-9).
# Performs the real auth flow via the API, not dependency overrides.
# ---------------------------------------------------------------------------

@pytest.fixture
async def authed_client(db, client, create_user):
    """AUTH-01: Authenticated client factory — performs real POST /api/auth + POST /api/session.

    Returns a dict with:
        client       — httpx.AsyncClient with auth cookie set
        user         — the User document dict
        session_key  — the active UserSession _key
        user_key     — the User _key
        access_token — the Bearer token from auth

    Unlike auth_headers (which overrides verify_token dependency),
    this fixture exercises the real auth endpoints end-to-end.
    The password for all test users is 'test' (matching the bcrypt hash in create_user).
    """
    user = create_user()
    username = user["username"]

    # Step 1: POST /api/auth with form data (OAuth2PasswordRequestForm)
    auth_response = await client.post(
        "/api/auth",
        data={"username": username, "password": "test"},
    )
    assert auth_response.status_code == 200, f"Auth failed: {auth_response.text}"
    auth_body = auth_response.json()
    assert auth_body["detail"]["action"] == "start_session"

    # Extract the access_token from response body (it's in the OAuth2 response)
    access_token = auth_body.get("access_token")
    assert access_token is not None, "Auth response missing access_token"

    # Step 2: POST /api/session with user_key
    session_response = await client.post(
        "/api/session",
        json={"user_key": user["_key"]},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert session_response.status_code == 200, f"Session start failed: {session_response.text}"
    session_body = session_response.json()
    session_key = session_body["detail"]["session_key"]

    return {
        "client": client,
        "user": user,
        "session_key": session_key,
        "user_key": user["_key"],
        "access_token": access_token,
    }
