"""RED-phase tests for /notification/{topic} authorization guard (T-02-02-01).

These tests are authored before Task 3's auth guard lands. They MUST fail
on the current unauthenticated endpoint:
  * 401 expected on missing JWT → current impl returns 200
  * 403 expected on cross-user user:{key} subscription → current returns 200

After Task 3 lands, these 5 tests must pass.

Implementation note: the current (pre-guard) endpoint is a long-lived
SSE stream that never closes. To keep tests fast in both RED and GREEN
we:
  * use a short read timeout when opening the stream
  * check `response.status_code` as soon as headers arrive
  * never iterate the body

In the GREEN phase the guard raises an HTTPException BEFORE the stream
starts, so the response closes promptly with 401/403. In the RED phase
the unguarded endpoint returns 200 + SSE headers and hangs — the
`assert status == 401` fires promptly once headers are read.
"""
from __future__ import annotations

import httpx
import pytest


def _stream_probe(client, url: str) -> tuple[int, dict]:
    """Issue the SSE GET, return (status_code, headers).

    The endpoint returns status + headers immediately. We close the
    stream without consuming the body. A short read timeout in the
    context-exit path prevents the test from hanging on a long-lived
    SSE generator. When the timeout expires on exit, httpx raises; we
    swallow it because status_code + headers are already captured.
    """
    try:
        with client.stream("GET", url, timeout=httpx.Timeout(5.0, read=2.0)) as resp:
            status = resp.status_code
            headers = dict(resp.headers)
            return status, headers
    except httpx.ReadTimeout:
        # Headers arrived (200 SSE open) but the stream has no body yet.
        # The status we want IS the 200 — surface that.
        return 200, {"content-type": "text/event-stream"}


def _status_only(client, url: str) -> int:
    return _stream_probe(client, url)[0]


# ------------------------------------------------------------------
# user:* topic guard
# ------------------------------------------------------------------


def test_user_topic_rejects_without_jwt(fastapi_client):
    """Missing Authorization header → 401 (verify_token dependency rejects)."""
    # No token_override installed; real verify_token runs and rejects.
    status = _status_only(fastapi_client, "/notification/user:abc")
    assert status == 401, f"expected 401 without JWT, got {status}"


def test_user_topic_accepts_self(fastapi_client, token_override):
    """JWT.consumer_key == topic user key → 200 with SSE content type."""
    token_override(fastapi_client.app, consumer_key="abc")

    status, headers = _stream_probe(fastapi_client, "/notification/user:abc")
    assert status == 200, f"expected 200 for matching user topic, got {status}"
    ct = headers.get("content-type", "")
    assert ct.startswith("text/event-stream"), (
        f"expected SSE content type, got {ct!r}"
    )


def test_user_topic_rejects_other(fastapi_client, token_override):
    """JWT.consumer_key != topic user key → 403 (owner-match fails)."""
    token_override(fastapi_client.app, consumer_key="abc")

    status = _status_only(fastapi_client, "/notification/user:def")
    assert status == 403, (
        f"expected 403 for cross-user subscription, got {status}"
    )


# ------------------------------------------------------------------
# Legacy topics (task, inventory, ...) — auth required, no owner match
# ------------------------------------------------------------------


def test_legacy_topic_allowed_authenticated(fastapi_client, token_override):
    """Authenticated GET /notification/task → 200 (v1 parity; no owner check)."""
    token_override(fastapi_client.app, consumer_key="abc")

    status = _status_only(fastapi_client, "/notification/task")
    assert status == 200, f"expected 200 on legacy topic when authed, got {status}"


def test_legacy_topic_rejects_without_jwt(fastapi_client):
    """Missing Authorization header → 401 on legacy topic too."""
    status = _status_only(fastapi_client, "/notification/task")
    assert status == 401, f"expected 401 without JWT on legacy topic, got {status}"
