"""Tests for the multiplexed SSE ticket + stream (one connection per tab).

POST /notification/ticket {"topics": [...]} — mint a ticket scoped to a SET.
GET  /notification/stream?topics=a,b,c&ticket=<jwt> — open ONE stream for many.

These exercise the multi-topic path end-to-end without a live ArangoDB or NATS,
mirroring test_sse_ticket.py. The `push_events_multi` generator is monkeypatched
to terminate immediately by the `fastapi_app` fixture in conftest.py.
"""
from __future__ import annotations

import pytest

from utils import auth


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
# Auth helpers — issue_sse_ticket_multi / verify_sse_ticket_multi
# ---------------------------------------------------------------------------

def test_multi_ticket_roundtrip_subset_ok():
    """A multi ticket validates for any subset of its granted topics."""
    ticket = auth.issue_sse_ticket_multi("userA", ["task", "message", "user:userA"])
    assert auth.verify_sse_ticket_multi(ticket, ["task", "message"]) == "userA"
    assert auth.verify_sse_ticket_multi(ticket, ["user:userA"]) == "userA"


def test_multi_ticket_rejects_ungranted_topic():
    """Requesting a topic outside the granted set raises (401)."""
    ticket = auth.issue_sse_ticket_multi("userA", ["task"])
    with pytest.raises(Exception):
        auth.verify_sse_ticket_multi(ticket, ["task", "message"])


def test_multi_verify_accepts_legacy_single_topic_ticket():
    """A legacy single-topic ticket interops as a one-element grant."""
    ticket = auth.issue_sse_ticket("userA", "task")
    assert auth.verify_sse_ticket_multi(ticket, ["task"]) == "userA"
    with pytest.raises(Exception):
        auth.verify_sse_ticket_multi(ticket, ["task", "message"])


# ---------------------------------------------------------------------------
# POST /notification/ticket — topic-set issuance
# ---------------------------------------------------------------------------

def test_ticket_topics_requires_auth(fastapi_client):
    resp = fastapi_client.post("/notification/ticket", json={"topics": ["task"]})
    assert resp.status_code == 401


def test_ticket_topics_rejects_foreign_user_topic_in_set(fastapi_client, token_override):
    """A user:<other> topic anywhere in the set is rejected → 403."""
    token_override(fastapi_client.app, consumer_key="userA")
    resp = fastapi_client.post(
        "/notification/ticket", json={"topics": ["task", "user:userB"]}
    )
    assert resp.status_code == 403


def test_ticket_topics_issues_for_own_and_shared(fastapi_client, token_override):
    token_override(fastapi_client.app, consumer_key="userA")
    resp = fastapi_client.post(
        "/notification/ticket", json={"topics": ["task", "message", "user:userA"]}
    )
    assert resp.status_code == 200, resp.text
    assert "ticket" in resp.json()
    assert resp.json()["expires_in"] == 90


def test_ticket_requires_exactly_one_of_topic_or_topics(fastapi_client, token_override):
    token_override(fastapi_client.app, consumer_key="userA")
    # Neither
    assert fastapi_client.post("/notification/ticket", json={}).status_code == 422
    # Both
    both = fastapi_client.post(
        "/notification/ticket", json={"topic": "task", "topics": ["message"]}
    )
    assert both.status_code == 422


def test_ticket_single_topic_still_works(fastapi_client, token_override):
    """Legacy single-topic issuance is untouched."""
    token_override(fastapi_client.app, consumer_key="userA")
    resp = fastapi_client.post("/notification/ticket", json={"topic": "task"})
    assert resp.status_code == 200
    assert "ticket" in resp.json()


# ---------------------------------------------------------------------------
# GET /notification/stream — multiplexed stream auth
# ---------------------------------------------------------------------------

def test_stream_opens_with_covering_ticket(fastapi_client, token_override):
    token_override(fastapi_client.app, consumer_key="userA")
    ticket = fastapi_client.post(
        "/notification/ticket", json={"topics": ["task", "message", "user:userA"]}
    ).json()["ticket"]

    url = f"/notification/stream?topics=task,message,user:userA&ticket={ticket}"
    assert _stream_status(fastapi_client, url) == 200


def test_stream_rejects_ticket_not_covering_topic(fastapi_client, token_override):
    """Ticket granted only `task`; requesting task,message → 401 (clean, not 500)."""
    token_override(fastapi_client.app, consumer_key="userA")
    ticket = fastapi_client.post(
        "/notification/ticket", json={"topics": ["task"]}
    ).json()["ticket"]

    url = f"/notification/stream?topics=task,message&ticket={ticket}"
    assert _stream_status(fastapi_client, url) == 401


def test_stream_requires_topics_param(fastapi_client, token_override):
    """Missing topics query param → 422 from FastAPI validation."""
    token_override(fastapi_client.app, consumer_key="userA")
    ticket = fastapi_client.post(
        "/notification/ticket", json={"topics": ["task"]}
    ).json()["ticket"]
    resp = fastapi_client.get(f"/notification/stream?ticket={ticket}")
    assert resp.status_code == 422


def test_stream_requires_auth(fastapi_client):
    """No ticket and no Authorization header → 401."""
    assert _stream_status(fastapi_client, "/notification/stream?topics=task") == 401
