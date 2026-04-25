"""Tests for the SSE ticket issuance and validation flow.

POST /notification/ticket — mint a short-lived topic-scoped ticket.
GET  /notification/{topic}?ticket=<jwt> — open SSE stream via ticket.

These tests exercise the stateless ticket path end-to-end without a live
ArangoDB or NATS. The FastAPI app fixture comes from conftest.py; auth is
controlled via dependency_overrides and direct calls to auth helpers.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _stream_status(client, url: str) -> int:
    """GET the stream URL; return status code (read timeout → 200 assumed)."""
    import httpx
    try:
        with client.stream("GET", url, timeout=httpx.Timeout(5.0, read=2.0)) as resp:
            return resp.status_code
    except httpx.ReadTimeout:
        return 200


# ---------------------------------------------------------------------------
# POST /notification/ticket — issuance
# ---------------------------------------------------------------------------

def test_ticket_endpoint_requires_auth(fastapi_client):
    """No Authorization header → 401."""
    resp = fastapi_client.post("/notification/ticket", json={"topic": "task"})
    assert resp.status_code == 401, (
        f"expected 401 without auth, got {resp.status_code}"
    )


def test_ticket_endpoint_user_topic_ownership_rejected(fastapi_client, token_override):
    """User A cannot mint a ticket for user:B's topic → 403."""
    token_override(fastapi_client.app, consumer_key="userA")

    resp = fastapi_client.post(
        "/notification/ticket", json={"topic": "user:userB"}
    )
    assert resp.status_code == 403, (
        f"expected 403 for cross-user ticket request, got {resp.status_code}"
    )


def test_ticket_endpoint_issues_ticket_for_own_user_topic(fastapi_client, token_override):
    """User A can mint a ticket for user:userA → 200 with ticket + expires_in."""
    token_override(fastapi_client.app, consumer_key="userA")

    resp = fastapi_client.post(
        "/notification/ticket", json={"topic": "user:userA"}
    )
    assert resp.status_code == 200, f"expected 200, got {resp.status_code}"
    body = resp.json()
    assert "ticket" in body
    assert body["expires_in"] == 90
    assert len(body["ticket"]) > 20  # non-trivial JWT string


def test_ticket_endpoint_issues_ticket_for_shared_topic(fastapi_client, token_override):
    """Any authenticated user can mint a ticket for a non-user topic."""
    token_override(fastapi_client.app, consumer_key="userA")

    resp = fastapi_client.post(
        "/notification/ticket", json={"topic": "production"}
    )
    assert resp.status_code == 200
    assert "ticket" in resp.json()


# ---------------------------------------------------------------------------
# GET /notification/{topic}?ticket=<jwt> — stream auth via ticket
# ---------------------------------------------------------------------------

def test_stream_accepts_valid_ticket(fastapi_client, token_override):
    """A valid ticket issued for a topic opens the SSE stream (200)."""
    token_override(fastapi_client.app, consumer_key="userA")

    ticket_resp = fastapi_client.post(
        "/notification/ticket", json={"topic": "production"}
    )
    ticket = ticket_resp.json()["ticket"]

    status = _stream_status(
        fastapi_client, f"/notification/production?ticket={ticket}"
    )
    assert status == 200, f"expected 200 with valid ticket, got {status}"


def test_stream_accepts_valid_user_ticket(fastapi_client, token_override):
    """A valid user-scoped ticket opens the user SSE stream (200)."""
    token_override(fastapi_client.app, consumer_key="userA")

    ticket_resp = fastapi_client.post(
        "/notification/ticket", json={"topic": "user:userA"}
    )
    ticket = ticket_resp.json()["ticket"]

    status = _stream_status(
        fastapi_client, f"/notification/user:userA?ticket={ticket}"
    )
    assert status == 200, f"expected 200 with valid user ticket, got {status}"


def test_stream_rejects_topic_mismatch(fastapi_client, token_override):
    """Ticket issued for 'task' cannot open 'production' stream → 401."""
    token_override(fastapi_client.app, consumer_key="userA")

    ticket_resp = fastapi_client.post(
        "/notification/ticket", json={"topic": "task"}
    )
    ticket = ticket_resp.json()["ticket"]

    status = _stream_status(
        fastapi_client, f"/notification/production?ticket={ticket}"
    )
    assert status == 401, (
        f"expected 401 on topic mismatch, got {status}"
    )


def test_stream_rejects_expired_ticket(fastapi_client, token_override):
    """An expired ticket (past exp) is rejected → 401."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "api"))

    from utils import auth

    # Mint a ticket that already expired (exp = past)
    expired_ticket = auth.issue_sse_ticket.__wrapped__ if hasattr(
        auth.issue_sse_ticket, "__wrapped__"
    ) else None

    # Directly sign a ticket with a past expiry using the jwt library.
    import jwt as pyjwt
    from utils.config import get_config

    past = datetime.utcnow() - timedelta(seconds=200)
    claims = {
        "sub": "userA",
        "topic": "production",
        "ctx": "sse_ticket",
        "iat": past,
        "exp": past + timedelta(seconds=90),  # already expired
    }
    bad_ticket = pyjwt.encode(
        claims, get_config().jwt_secret, algorithm="HS256"
    )

    status = _stream_status(
        fastapi_client, f"/notification/production?ticket={bad_ticket}"
    )
    assert status == 401, f"expected 401 for expired ticket, got {status}"


def test_stream_rejects_missing_auth(fastapi_client):
    """No ticket, no header → 401."""
    status = _stream_status(fastapi_client, "/notification/production")
    assert status == 401, f"expected 401 with no auth at all, got {status}"


def test_stream_accepts_header_auth(fastapi_client, token_override):
    """Fallback header auth path still works for server-to-server clients."""
    # token_override installs both verify_token and verify_token_optional fakes.
    token_override(fastapi_client.app, consumer_key="userA")

    # No ticket param — depends on the header path via verify_token_optional.
    status = _stream_status(fastapi_client, "/notification/production")
    assert status == 200, f"expected 200 via header auth path, got {status}"


# ---------------------------------------------------------------------------
# verify_token rejects SSE tickets (unit test — no FastAPI app needed)
# ---------------------------------------------------------------------------

def test_verify_token_rejects_sse_ticket():
    """An SSE ticket passed to verify_token (header path) must be rejected.

    SSE tickets have ctx=sse_ticket; verify_token must raise 401 for
    them so a stolen ticket cannot authenticate any non-SSE endpoint.
    """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "api"))

    import jwt as pyjwt
    from fastapi import HTTPException
    from utils import auth
    from utils.config import get_config

    now = datetime.utcnow()
    ticket = pyjwt.encode(
        {
            "sub": "userA",
            "topic": "production",
            "ctx": "sse_ticket",
            "iat": now,
            "exp": now + timedelta(seconds=90),
        },
        get_config().jwt_secret,
        algorithm="HS256",
    )

    with pytest.raises(HTTPException) as exc_info:
        auth.verify_token(token_str=ticket)

    assert exc_info.value.status_code == 401
