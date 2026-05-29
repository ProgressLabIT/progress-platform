"""Shared fixtures for notification pytest suite.

These tests exercise the TaskUpdatedEvent assignee-delta fan-out and the
/notification/{topic} authorization guard WITHOUT requiring a live
ArangoDB or NATS. A `fake_tx` stand-in provides the `collection()`,
`_pending_events` and `transaction_status()` surface the production
code uses; auth tests swap in a TokenData override via
`app.dependency_overrides`.
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

logger = logging.getLogger(__name__)

# Ensure `api/` is on sys.path for test-time imports. pytest.ini sets
# pythonpath=api for the collector, but explicit setup here keeps the
# conftest robust when pytest is invoked from a different cwd.
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_API_PATH = _BACKEND_ROOT / "api"
if str(_API_PATH) not in sys.path:
    sys.path.insert(0, str(_API_PATH))


# ------------------------------------------------------------------
# Fake transaction: mirrors the surface that BaseEvent / TaskUpdatedEvent
# touch — collection('Task').get / .update, plus the _pending_events list
# and transaction_status().
# ------------------------------------------------------------------

class _FakeCollection:
    def __init__(self, doc: dict[str, Any] | None = None):
        self._doc = doc
        self.updates: list[dict[str, Any]] = []

    def get(self, _key: str) -> dict[str, Any] | None:
        return self._doc

    def update(self, updates: dict[str, Any], return_new: bool = False, **_: Any) -> Any:
        self.updates.append(updates)
        if return_new:
            merged = dict(self._doc or {})
            merged.update(updates)
            return {"new": merged}
        return None

    def insert(self, *_args: Any, **_kwargs: Any) -> None:
        # Event/event_source inserts are no-ops in these unit tests.
        return None


class _FakeTx:
    def __init__(self) -> None:
        self._collections: dict[str, _FakeCollection] = {}
        self._pending_events: list[dict[str, Any]] = []
        self._status = "running"

    def set_collection(self, name: str, collection: _FakeCollection) -> None:
        self._collections[name] = collection

    def collection(self, name: str) -> _FakeCollection:
        if name not in self._collections:
            self._collections[name] = _FakeCollection()
        return self._collections[name]

    def transaction_status(self) -> str:
        return self._status

    def commit_transaction(self) -> None:
        self._status = "committed"

    def abort_transaction(self) -> None:
        self._status = "aborted"


@pytest.fixture
def fake_tx() -> _FakeTx:
    tx = _FakeTx()
    tx.set_collection("Task", _FakeCollection(doc={}))
    tx.set_collection("Event", _FakeCollection())
    tx.set_collection("event_source", _FakeCollection())
    return tx


# ------------------------------------------------------------------
# TaskUpdatedEvent factory: wires an InfoModel instance onto a
# TaskUpdatedEvent without going through .save() so the tests can invoke
# apply() and _build_event_payload() surgically.
# ------------------------------------------------------------------


@pytest.fixture
def task_updated_event_factory(fake_tx: _FakeTx):
    from events.collaboration.task_updated import TaskUpdatedEvent
    from models.event import EventType

    def _factory(
        *,
        task_key: str = "TASK1",
        prior_assigned_to: list[dict[str, Any]] | None = None,
        assigned_to: list[dict[str, Any]] | None = None,
        title: str | None = None,
        description: str | None = None,
        user_key: str = "userA",
        primary: bool = True,
        event_key: str = "EVT1",
    ) -> TaskUpdatedEvent:
        fake_tx.set_collection(
            "Task",
            _FakeCollection(doc={"_key": task_key, "assigned_to": prior_assigned_to or []}),
        )

        info_data: dict[str, Any] = {
            "event_type": EventType.TASK_UPDATED,
            "primary": primary,
            "user_key": user_key,
            "task_key": task_key,
            "title": title,
            "description": description,
            "assigned_to": assigned_to,
            "timestamp": datetime.utcnow(),
        }
        event = TaskUpdatedEvent(info=info_data, tx=fake_tx)
        event.event_key = event_key
        return event

    return _factory


# ------------------------------------------------------------------
# FastAPI TestClient for authz tests
# ------------------------------------------------------------------


@pytest.fixture
def fastapi_app(monkeypatch):
    """Import a minimal FastAPI app mounting ONLY the notification router.

    We avoid importing `api.main` (which runs @on_event("startup") and
    connects to NATS) AND `endpoints/__init__.py` (which eagerly imports
    every endpoint module including `serial` → pypdf, not available in
    the standard test venv). We load the notification endpoint module
    directly by path.

    We also monkeypatch `ServerEventManager.push_events` to yield ZERO
    events and return immediately, so the SSE stream closes as soon as
    the 200 status + headers are sent. Without this, the pre-guard
    endpoint (and the post-guard 200 branch) would hang indefinitely
    waiting on an asyncio.Queue that never receives anything under
    TestClient.
    """
    import importlib.util

    from fastapi import FastAPI

    from managers.server_event_manager import ServerEventManager

    async def _empty_push_events(self, request, topic):
        # Immediately-terminating async iterator: no events, no wait.
        if False:
            yield  # pragma: no cover - makes this an async generator
        return

    async def _empty_push_events_multi(self, request, topics):
        # Same immediate-terminate stand-in for the multiplexed stream.
        if False:
            yield  # pragma: no cover - makes this an async generator
        return

    monkeypatch.setattr(
        ServerEventManager, "push_events", _empty_push_events, raising=True
    )
    monkeypatch.setattr(
        ServerEventManager, "push_events_multi", _empty_push_events_multi, raising=True
    )

    module_path = _API_PATH / "endpoints" / "notification.py"
    spec = importlib.util.spec_from_file_location(
        "endpoints_notification_under_test", module_path
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    app = FastAPI()
    app.include_router(module.router)
    return app


@pytest.fixture
def fastapi_client(fastapi_app):
    from fastapi.testclient import TestClient

    client = TestClient(fastapi_app)
    client.app = fastapi_app  # convenience alias for tests
    yield client


@pytest.fixture
def token_override():
    """Helper that installs / removes a TokenData override on the app.

    Overrides `verify_token` (used by `mint_ticket` and other protected
    endpoints) AND `verify_token_optional` (used by the stream's header
    auth path). Both are patched so a single fixture covers all auth
    surfaces.
    """
    from models.auth import ConsumerType, TokenContext, TokenData
    from utils import auth

    installed: list = []

    def _install(app, consumer_key: str) -> None:
        def _fake_token() -> TokenData:
            return TokenData(
                jti="tkn1",
                sub=consumer_key,
                ctyp=ConsumerType.USER,
                iat=datetime.utcnow(),
                exp=datetime.utcnow(),
                ctx=TokenContext.USER_SESSION,
            )

        app.dependency_overrides[auth.verify_token] = _fake_token
        app.dependency_overrides[auth.verify_token_optional] = _fake_token
        installed.append((app, auth.verify_token))
        installed.append((app, auth.verify_token_optional))

    yield _install

    for app, dep in installed:
        app.dependency_overrides.pop(dep, None)
