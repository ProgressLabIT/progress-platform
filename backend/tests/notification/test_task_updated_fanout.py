"""RED-phase tests for TaskUpdatedEvent assignee-delta fan-out (NOTIF-01).

These tests are authored BEFORE the implementation in Plan 02-02 Task 2
lands. They verify:

  * delta detection: only newly-added assignees receive a user-scoped payload
  * multi-assignee fan-out (D-03, SP-3) with OWNER + PARTICIPANT treated uniformly
  * no-op branches: no assignee change, no assigned_to in info
  * transaction abort (Pitfall P2): publish_sync is NEVER called if the
    transaction never commits
  * minimal payload projection (A3 / D-07)

They use `fake_tx` + `task_updated_event_factory` from conftest.py; no
live ArangoDB or NATS is required.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest


def _simulate_save_collect(event) -> None:
    """Stand-in for BaseEvent.save(): call apply() then run the
    append-or-extend collection logic the production save() performs
    (the code under test for base_event.py).

    After Task 2 this replicates the widened payload contract
    (dict | list[dict] | None). In the RED phase, the
    TaskUpdatedEvent._build_event_payload returns a single dict (inherited)
    so the list branch stays unexercised — tests fail for the expected
    reason (no user-scoped payloads produced).
    """
    event.apply()
    payload = event._build_event_payload()
    if not payload:
        return
    if isinstance(payload, list):
        event.tx._pending_events.extend(payload)
    else:
        event.tx._pending_events.append(payload)


def _assignment(user_key: str, role: str = "participant") -> dict:
    return {"user_key": user_key, "role": role}


# ------------------------------------------------------------------
# Delta detection: single new assignee
# ------------------------------------------------------------------


def test_delta_single_new_assignee_emits_one_user_payload_plus_base(
    task_updated_event_factory,
):
    """NOTIF-01, Pitfall P4 — prior [A], new [A, B] → 2 payloads (base + userB)."""
    event = task_updated_event_factory(
        prior_assigned_to=[_assignment("keyA", "owner")],
        assigned_to=[
            _assignment("keyA", "owner"),
            _assignment("keyB", "participant"),
        ],
    )

    _simulate_save_collect(event)

    payloads = event.tx._pending_events
    assert len(payloads) == 2, f"expected 2 payloads, got {len(payloads)}: {payloads}"
    subtopics = {p["subtopic"] for p in payloads}
    assert subtopics == {"task", "user:keyB"}

    user_payload = next(p for p in payloads if p["subtopic"] == "user:keyB")
    assert user_payload["recipient_key"] == "keyB"


# ------------------------------------------------------------------
# Delta detection: two new assignees
# ------------------------------------------------------------------


def test_delta_two_new_assignees_emits_two_user_payloads(task_updated_event_factory):
    """NOTIF-01, D-03 — prior [A], new [A, B, C] → 3 payloads (base + B + C)."""
    event = task_updated_event_factory(
        prior_assigned_to=[_assignment("keyA", "owner")],
        assigned_to=[
            _assignment("keyA", "owner"),
            _assignment("keyB", "participant"),
            _assignment("keyC", "participant"),
        ],
    )

    _simulate_save_collect(event)

    payloads = event.tx._pending_events
    assert len(payloads) == 3
    subtopics = [p["subtopic"] for p in payloads]
    assert subtopics.count("task") == 1
    user_scoped = {p["subtopic"] for p in payloads if p["subtopic"].startswith("user:")}
    assert user_scoped == {"user:keyB", "user:keyC"}

    recipient_keys = {
        p["recipient_key"] for p in payloads if p["subtopic"].startswith("user:")
    }
    assert recipient_keys == {"keyB", "keyC"}


# ------------------------------------------------------------------
# SP-3 — owner and participant uniformly
# ------------------------------------------------------------------


def test_owner_and_participant_treated_uniformly(task_updated_event_factory):
    """NOTIF-01, SP-3 — prior [], new [A=owner, B=participant] → 3 payloads
    (base + A + B). Role is IRRELEVANT to fan-out scope.
    """
    event = task_updated_event_factory(
        prior_assigned_to=[],
        assigned_to=[
            _assignment("keyA", "owner"),
            _assignment("keyB", "participant"),
        ],
    )

    _simulate_save_collect(event)

    payloads = event.tx._pending_events
    assert len(payloads) == 3
    user_scoped = {p["subtopic"] for p in payloads if p["subtopic"].startswith("user:")}
    assert user_scoped == {"user:keyA", "user:keyB"}


# ------------------------------------------------------------------
# No-op branches
# ------------------------------------------------------------------


def test_no_assignee_change_emits_base_only(task_updated_event_factory):
    """NOTIF-01 — prior [A], new [A] (no change) → 1 base payload only."""
    event = task_updated_event_factory(
        prior_assigned_to=[_assignment("keyA", "owner")],
        assigned_to=[_assignment("keyA", "owner")],
    )

    _simulate_save_collect(event)

    payloads = event.tx._pending_events
    assert len(payloads) == 1
    assert payloads[0]["subtopic"] == "task"


def test_non_assignee_update_emits_base_only(task_updated_event_factory):
    """NOTIF-01, Pitfall P5 — info.assigned_to is None (title-only change) → base only."""
    event = task_updated_event_factory(
        prior_assigned_to=[_assignment("keyA", "owner")],
        assigned_to=None,
        title="A new title",
    )

    _simulate_save_collect(event)

    payloads = event.tx._pending_events
    assert len(payloads) == 1
    assert payloads[0]["subtopic"] == "task"


# ------------------------------------------------------------------
# Transaction abort: Pitfall P2
# ------------------------------------------------------------------


def test_aborted_transaction_publishes_nothing(task_updated_event_factory, monkeypatch):
    """NOTIF-01, Pitfall P2 — if apply() raises, publish_sync is NEVER invoked."""
    from events import base_event as base_event_mod

    calls: list = []

    def _spy_publish(subject, data):  # pragma: no cover - spy
        calls.append((subject, data))

    monkeypatch.setattr(base_event_mod, "publish_sync", _spy_publish)

    event = task_updated_event_factory(
        prior_assigned_to=[_assignment("keyA", "owner")],
        assigned_to=[
            _assignment("keyA", "owner"),
            _assignment("keyB", "participant"),
        ],
    )

    # Force apply() to raise mid-flight by making .update() raise.
    class _ExplodingCollection:
        def get(self, _k):
            return {"_key": "TASK1", "assigned_to": [_assignment("keyA", "owner")]}

        def update(self, *args, **kwargs):
            raise RuntimeError("transactional rollback simulated")

    event.tx._collections["Task"] = _ExplodingCollection()

    with pytest.raises(RuntimeError):
        event.apply()

    # _publish_collected_events is only called post-commit; we never committed.
    assert calls == [], f"publish_sync must not be called when tx aborts, got: {calls}"


# ------------------------------------------------------------------
# Payload projection shape (A3 / D-07)
# ------------------------------------------------------------------


def test_user_payload_minimal_projection_fields(task_updated_event_factory):
    """NOTIF-01, A3 — user-scoped payload has exactly the documented projection."""
    event = task_updated_event_factory(
        prior_assigned_to=[_assignment("keyA", "owner")],
        assigned_to=[
            _assignment("keyA", "owner"),
            _assignment("keyB", "participant"),
        ],
        title="Fix the widget",
        user_key="keyA",
    )

    _simulate_save_collect(event)

    user_payload = next(
        p for p in event.tx._pending_events if p["subtopic"] == "user:keyB"
    )
    expected_keys = {
        "notification",
        "task_key",
        "task_title",
        "assigned_by",
        "timestamp",
        "subtopic",
        "recipient_key",
    }
    assert set(user_payload.keys()) == expected_keys, (
        f"user payload keys mismatch: {set(user_payload.keys())} vs {expected_keys}"
    )
    assert user_payload["task_key"] == "TASK1"
    assert user_payload["task_title"] == "Fix the widget"
    assert user_payload["assigned_by"] == "keyA"
    assert user_payload["recipient_key"] == "keyB"
    # notification mirrors the base payload's notification string (which is
    # str(EventType.TASK_UPDATED); whatever base produces, the projection uses).
    assert user_payload["notification"] == "TASK_UPDATED" or user_payload[
        "notification"
    ] == "EventType.TASK_UPDATED"
