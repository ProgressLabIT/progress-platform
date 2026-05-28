"""ErrorLog capture tests — verifies 5xx failures are persisted to ArangoDB
with secrets redacted, and 4xx failures are not recorded.

Covers utils/error_log.py: the StarletteHTTPException handler (endpoint-raised
5xx, the dominant pattern in this codebase), the unhandled-exception handler,
and the redaction helper.
"""
import jwt
import pytest
from fastapi import Body, HTTPException
from starlette.requests import Request


@pytest.fixture
def error_log_ready(db):
    """Patch the error_log db singleton to the testcontainer and ensure the
    ErrorLog collection + TTL index exist (mirrors the runtime startup hook)."""
    import utils.error_log as error_log
    error_log.db = db
    error_log.ensure_collection()
    return error_log


@pytest.fixture
def throwaway_routes():
    """Register throwaway routes that deterministically raise, once."""
    from main import app

    existing = {getattr(r, "path", None) for r in app.router.routes}

    if "/_err500" not in existing:
        @app.post("/_err500")
        async def _err500(payload: dict = Body(...)):
            # Body is parsed (and cached on the request) before the failure — this
            # mirrors real endpoints that 500 inside business logic post-validation.
            raise HTTPException(status_code=500, detail="boom-traceback-string")

    if "/_err400" not in existing:
        @app.post("/_err400")
        async def _err400():
            raise HTTPException(status_code=400, detail="bad request")

    return app


def _bearer(user_key="test-user-key"):
    from utils.config import get_config
    from utils import auth
    token = jwt.encode({"sub": user_key}, get_config().jwt_secret, algorithm=auth.ALGORITHM)
    return {"Authorization": f"Bearer {token}"}


class TestRedaction:
    def test_redact_masks_sensitive_keys_recursively(self, error_log_ready):
        out = error_log_ready._redact({
            "username": "alice",
            "password": "hunter2",
            "nested": {"token": "abc", "keep": 1},
            "list": [{"new_password": "x"}, {"ok": "y"}],
        })
        assert out["username"] == "alice"
        assert out["password"] == "***REDACTED***"
        assert out["nested"]["token"] == "***REDACTED***"
        assert out["nested"]["keep"] == 1
        assert out["list"][0]["new_password"] == "***REDACTED***"
        assert out["list"][1]["ok"] == "y"


class TestHttpExceptionCapture:
    @pytest.mark.asyncio
    async def test_5xx_recorded_with_redacted_payload_and_user(self, client, db, error_log_ready, throwaway_routes):
        response = await client.post(
            "/api/_err500?token=secret-query-val&page=2",
            json={"username": "alice", "password": "hunter2", "data": {"ok": 1}},
            headers=_bearer("user-42"),
        )
        assert response.status_code == 500

        rows = list(db.collection("ErrorLog").all())
        assert len(rows) == 1
        row = rows[0]
        assert row["endpoint"] == "/api/_err500"
        assert row["method"] == "POST"
        assert row["status_code"] == 500
        assert "boom-traceback-string" in row["traceback"]
        assert row["user_key"] == "user-42"
        # payload redacted, non-secret retained
        assert row["payload"]["password"] == "***REDACTED***"
        assert row["payload"]["username"] == "alice"
        assert row["payload"]["data"] == {"ok": 1}
        # query redacted
        assert row["query"]["token"] == "***REDACTED***"
        assert row["query"]["page"] == "2"
        # time fields present (ts drives the TTL index)
        assert isinstance(row["ts"], (int, float))
        assert isinstance(row["timestamp"], str)
        # Authorization header value must never be stored
        assert "Bearer" not in str(row)

    @pytest.mark.asyncio
    async def test_4xx_not_recorded(self, client, db, error_log_ready, throwaway_routes):
        r400 = await client.post("/api/_err400", json={"x": 1})
        assert r400.status_code == 400
        r404 = await client.get("/api/this-route-does-not-exist")
        assert r404.status_code == 404

        assert list(db.collection("ErrorLog").all()) == []


class TestUnhandledExceptionHandler:
    @pytest.mark.asyncio
    async def test_unhandled_records_traceback_and_returns_opaque_500(self, db, error_log_ready):
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/widget",
            "raw_path": b"/api/widget",
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)

        try:
            raise RuntimeError("kaboom")
        except RuntimeError as exc:
            response = await error_log_ready.unhandled_exception_handler(request, exc)

        assert response.status_code == 500
        assert b"Internal Server Error" in response.body
        # opaque to client — no traceback leaked in the response body
        assert b"kaboom" not in response.body

        rows = list(db.collection("ErrorLog").all())
        assert len(rows) == 1
        assert rows[0]["status_code"] == 500
        assert rows[0]["error"] == "kaboom"
        assert "RuntimeError: kaboom" in rows[0]["traceback"]
        assert rows[0]["endpoint"] == "/api/widget"

    @pytest.mark.asyncio
    async def test_ttl_index_present(self, db, error_log_ready):
        idx = db.collection("ErrorLog").indexes()
        ttl = [i for i in idx if i.get("type") == "ttl"]
        assert ttl, "expected a TTL index on ErrorLog"
        assert ttl[0]["fields"] == ["ts"]
        # python-arango surfaces the TTL value as `expiry_time` (server field `expireAfter`)
        expiry = ttl[0].get("expiry_time", ttl[0].get("expireAfter"))
        assert expiry == 2592000
