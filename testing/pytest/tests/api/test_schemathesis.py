"""Schemathesis fuzzing test — fail on any 5xx response to generated inputs.

Uses schemathesis.openapi.from_asgi() (v4 API) to load the OpenAPI schema from
the in-process FastAPI app. Auth is injected via the @schemathesis.auth() provider
pattern which sets the Authorization header and activates the verify_token
dependency override on each generated case.

Decisions: D-06 through D-11 (context doc).
- 5xx responses → test failure
- 401 responses → test failure (indicates auth injection broken)
- 422 responses → pass (expected from fuzzing with invalid payloads)
- Excluded routes: SSE (/notification/), multipart file uploads
"""
import pytest
import schemathesis
from hypothesis import settings
from schemathesis import AuthContext, Case

# Excluded from the default run (addopts -m 'not fuzz'):
# - even at max_examples=10, ~165 operations × ASGI-lifespan-per-case + shrinking
#   on failing endpoints runs for hours
# - fuzzed requests mutate skip-truncate collections (Counter, Config),
#   poisoning tests that run afterwards in the same session
# Run explicitly: uv run pytest -m fuzz
pytestmark = pytest.mark.fuzz

# ---------------------------------------------------------------------------
# Excluded route patterns — SSE and multipart file upload endpoints
# ---------------------------------------------------------------------------
_EXCLUDED_PATHS = {
    "/notification/{topic}",             # SSE stream — EventSourceResponse
    "/media/create",                     # POST UploadFile (actual path from audit)
    "/media/{media_key}",                # PATCH UploadFile
    "/org/{org_key}/image",              # POST UploadFile
    "/config/{key}/file",                # PUT UploadFile
    "/inventory/count-record/import",    # POST UploadFile + Form
}


# ---------------------------------------------------------------------------
# Auth provider — injects JWT header + FastAPI dependency override
# ---------------------------------------------------------------------------
@schemathesis.auth()
class ProgressJWTAuth:
    """Inject a fixture JWT token into every generated Schemathesis test case.

    get() returns the header value string.
    set() applies it to case.headers and activates the dependency override so
    FastAPI's verify_token returns a valid TokenData without hitting the DB.
    """

    def get(self, case: Case, ctx: AuthContext) -> str:
        return "Bearer test-token"

    def set(self, case: Case, data: str, ctx: AuthContext) -> None:
        from main import app
        from utils.auth import verify_token
        from models.auth import TokenData, TokenContext
        from datetime import datetime, timedelta

        # Build a fully scoped token for the request
        token_data = TokenData(
            jti="schemathesis-token",
            sub="schemathesis-user",
            ctyp="user",
            iat=datetime.utcnow(),
            exp=datetime.utcnow() + timedelta(hours=1),
            ctx=TokenContext.USER_SESSION,
            scope="operator production admin quality warehouse",
        )
        app.dependency_overrides[verify_token] = lambda: token_data

        # Set the header on the case
        if case.headers is None:
            case.headers = {}
        case.headers["Authorization"] = data


# ---------------------------------------------------------------------------
# Schema fixture — depends on db + mock_nats so backend is fully initialized
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def api_schema(db, mock_nats):
    """Load OpenAPI schema from the ASGI app in-process.

    Schemathesis fires the FastAPI startup event for each sub-test (ASGI lifespan).
    The startup event calls nats_client.subscribe() which calls get_nats() — but
    the mock_nats fixture only patches connect() and publish_sync(), leaving _nc=None.
    We must also patch subscribe() as a no-op so startup doesn't raise RuntimeError.
    """
    import utils.nats_client as nats_module
    original_subscribe = nats_module.subscribe

    async def _noop_subscribe(subject, cb):
        pass

    nats_module.subscribe = _noop_subscribe

    from main import app
    schema = schemathesis.openapi.from_asgi("/openapi.json", app)

    # Restore after schema object is created (Schemathesis holds a ref to app)
    # Keep the override active for the session since sub-tests fire startup repeatedly
    return schema


# Lazy fixture reference — Schemathesis resolves this at test collection time
schema = schemathesis.pytest.from_fixture("api_schema")


# ---------------------------------------------------------------------------
# Fuzz test
# ---------------------------------------------------------------------------
@schema.parametrize()
@settings(max_examples=10, deadline=None)
def test_api_fuzzing(case):
    """Fuzz all non-excluded API endpoints. Fail on 5xx or 401."""
    # Skip excluded routes (SSE, multipart uploads)
    if case.path in _EXCLUDED_PATHS:
        pytest.skip(f"Excluded from fuzzing: {case.path}")

    response = case.call()

    # 5xx = server crash or unhandled error → failure
    assert response.status_code < 500, (
        f"Server error on {case.method} {case.path}: "
        f"HTTP {response.status_code}\n{response.text[:500]}"
    )

    # 401 = auth injection broken → failure
    assert response.status_code != 401, (
        f"Auth injection failed on {case.method} {case.path}: "
        f"HTTP {response.status_code}"
    )
    # 422 = FastAPI validation rejection of fuzzed input → expected, pass silently
