"""Collaboration message CRUD tests.

Migrated from: testing/robot-test/tests/events/collaborations.robot
Requirement: ROBOT-05
"""
from datetime import datetime, timezone

import pytest


def _event_payload(event_type, **data_kwargs):
    """Build a collaboration event payload matching CollaborationsEvents.py shape."""
    # Determine the data key based on event type
    if event_type.startswith("MESSAGE_"):
        data_key = "message_data"
    else:
        data_key = "issue_data"
    return {
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        data_key: data_kwargs,
        "user_key": "test-user-key",
        "user_session_key": "test-session-key",
    }


class TestMessageLifecycle:
    """HTTP API tests for message CRUD events via POST /event.

    Messages require an existing issue, so test_01 creates an issue first
    before posting a message. Sequential within class per D-04, D-07.
    """

    issue_key: str = ""
    message_key: str = ""

    @pytest.mark.asyncio
    async def test_01_post_message(self, client, auth_headers):
        """Given an open issue,
        when a MESSAGE_POSTED event is sent,
        then the message is persisted linked to the issue.
        migrated from: collaborations.robot 'Send message posted event'.
        """
        auth_headers()

        # First create an issue as setup dependency
        issue_payload = {
            "event_type": "ISSUE_CREATED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "issue_data": {
                "issue_type_key": "3142793",
                "critical": False,
                "data": [],
                "created_by": "User/test-user-key",
                "close_within": 0,
                "linked_to": [
                    {"type": "product", "key": "10090138"},
                    {"type": "operation", "key": "11513"},
                    {"type": "phase", "key": "10090140"},
                ],
            },
            "user_key": "test-user-key",
            "user_session_key": "test-session-key",
        }
        issue_resp = await client.post("/event", json=issue_payload)
        assert issue_resp.status_code == 200, (
            f"Issue setup failed: {issue_resp.status_code}: {issue_resp.text}"
        )
        TestMessageLifecycle.issue_key = issue_resp.json()["detail"]["issue_key"]

        # Now post the message
        payload = _event_payload(
            "MESSAGE_POSTED",
            sender=f"User/test-user-key",
            recipient=f"Issue/{TestMessageLifecycle.issue_key}",
            content="Hello",
        )
        response = await client.post("/event", json=payload)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        detail = response.json().get("detail", {})
        assert "message_key" in detail, (
            f"Expected 'message_key' in detail, got keys: {list(detail.keys())}"
        )
        TestMessageLifecycle.message_key = detail["message_key"]

    @pytest.mark.asyncio
    async def test_02_update_message(self, client, auth_headers):
        """Given an existing message on an issue,
        when a MESSAGE_UPDATED event is sent with updated content,
        then the message is updated.
        migrated from: collaborations.robot 'Send message updated event'.
        """
        auth_headers()
        payload = _event_payload(
            "MESSAGE_UPDATED",
            _key=TestMessageLifecycle.message_key,
            _id=f"message/{TestMessageLifecycle.message_key}",
            _from="User/test-user-key",
            _to=f"Issue/{TestMessageLifecycle.issue_key}",
            content="Hello Updated",
            updated=datetime.now(timezone.utc).isoformat(),
        )
        response = await client.post("/event", json=payload)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )

    @pytest.mark.asyncio
    async def test_03_delete_message(self, client, auth_headers):
        """Given an existing message on an issue,
        when a MESSAGE_DELETED event is sent,
        then the message is removed.
        migrated from: collaborations.robot 'Send message deleted event'.
        """
        auth_headers()
        payload = _event_payload(
            "MESSAGE_DELETED",
            _key=TestMessageLifecycle.message_key,
            _id=f"message/{TestMessageLifecycle.message_key}",
            _from="User/test-user-key",
            _to=f"Issue/{TestMessageLifecycle.issue_key}",
        )
        response = await client.post("/event", json=payload)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
