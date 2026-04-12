"""Collaboration issue lifecycle tests.

Migrated from: testing/robot-test/tests/events/collaborations.robot
Requirement: ROBOT-05
"""
from datetime import datetime, timezone

import pytest


def _issue_event(event_type, issue_data):
    """Build a collaboration issue event payload matching CollaborationsEvents.py shape."""
    return {
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "issue_data": issue_data,
        "user_key": "test-user-key",
        "user_session_key": "test-session-key",
    }


class TestIssueLifecycle:
    """HTTP API tests for issue lifecycle events via POST /event.

    Sequential tests within a single class, mirroring the Robot Framework
    collaborations.robot suite flow. Per D-03, D-07.
    """

    issue_key: str = ""

    @pytest.mark.asyncio
    async def test_01_create_critical_issue(self, client, auth_headers):
        """Given a product context,
        when an ISSUE_CREATED event is sent with critical=True,
        then the issue is persisted with critical flag and returns issue_key.
        migrated from: collaborations.robot 'Send critical product issue created event'.
        """
        auth_headers()
        payload = _issue_event("ISSUE_CREATED", {
            "issue_type_key": "3142793",
            "critical": True,
            "data": [],
            "created_by": "User/test-user-key",
            "close_within": 0,
            "linked_to": [
                {"type": "product", "key": "10090138"},
                {"type": "operation", "key": "11513"},
                {"type": "phase", "key": "10090140"},
            ],
        })
        response = await client.post("/event", json=payload)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        detail = response.json().get("detail", {})
        assert "issue_key" in detail, (
            f"Expected 'issue_key' in detail, got keys: {list(detail.keys())}"
        )
        TestIssueLifecycle.issue_key = detail["issue_key"]

    @pytest.mark.asyncio
    async def test_02_update_issue(self, client, auth_headers):
        """Given an existing issue,
        when an ISSUE_UPDATED event is sent with data=[],
        then the issue is updated successfully.
        migrated from: collaborations.robot 'Send issue updated event'.
        """
        auth_headers()
        payload = _issue_event("ISSUE_UPDATED", {
            "_key": TestIssueLifecycle.issue_key,
            "data": [],
        })
        response = await client.post("/event", json=payload)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )

    @pytest.mark.asyncio
    async def test_03_mark_issue_critical(self, client, auth_headers):
        """Given an existing issue,
        when an ISSUE_UPDATED event is sent with critical=True,
        then the issue is marked as critical.
        migrated from: collaborations.robot 'Mark issue as critical'.
        """
        auth_headers()
        payload = _issue_event("ISSUE_UPDATED", {
            "_key": TestIssueLifecycle.issue_key,
            "critical": True,
        })
        response = await client.post("/event", json=payload)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )

    @pytest.mark.asyncio
    async def test_04_mark_issue_not_critical(self, client, auth_headers):
        """Given an issue marked as critical,
        when an ISSUE_UPDATED event is sent with critical=False,
        then the issue is marked as not critical.
        migrated from: collaborations.robot 'Mark issue as not critical'.
        """
        auth_headers()
        payload = _issue_event("ISSUE_UPDATED", {
            "_key": TestIssueLifecycle.issue_key,
            "critical": False,
        })
        response = await client.post("/event", json=payload)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )

    @pytest.mark.asyncio
    async def test_05_close_issue(self, client, auth_headers):
        """Given an open issue,
        when an ISSUE_CLOSED event is sent,
        then the issue is closed.
        migrated from: collaborations.robot 'Send issue closed event'.
        """
        auth_headers()
        payload = _issue_event("ISSUE_CLOSED", {
            "_key": TestIssueLifecycle.issue_key,
        })
        response = await client.post("/event", json=payload)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )

    @pytest.mark.asyncio
    async def test_06_reopen_issue_critical(self, client, auth_headers):
        """Given a closed issue,
        when an ISSUE_REOPENED event is sent with critical=True,
        then the issue is reopened and marked critical.
        migrated from: collaborations.robot 'Reopen issue as critical'.
        """
        auth_headers()
        payload = _issue_event("ISSUE_REOPENED", {
            "_key": TestIssueLifecycle.issue_key,
            "critical": True,
        })
        response = await client.post("/event", json=payload)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )

    @pytest.mark.asyncio
    async def test_07_close_issue_again(self, client, auth_headers):
        """Given a reopened issue,
        when an ISSUE_CLOSED event is sent again,
        then the issue is closed for a second time.
        migrated from: collaborations.robot 'ReSend issue closed event'.
        """
        auth_headers()
        payload = _issue_event("ISSUE_CLOSED", {
            "_key": TestIssueLifecycle.issue_key,
        })
        response = await client.post("/event", json=payload)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )

    @pytest.mark.asyncio
    async def test_08_reopen_issue_not_critical(self, client, auth_headers):
        """Given a closed issue,
        when an ISSUE_REOPENED event is sent with critical=False,
        then the issue is reopened and marked not critical.
        migrated from: collaborations.robot 'Reopen issue as not critical'.
        """
        auth_headers()
        payload = _issue_event("ISSUE_REOPENED", {
            "_key": TestIssueLifecycle.issue_key,
            "critical": False,
        })
        response = await client.post("/event", json=payload)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )

    @pytest.mark.asyncio
    async def test_09_delete_issue(self, client, auth_headers):
        """Given an existing issue,
        when an ISSUE_DELETED event is sent,
        then the issue is permanently removed.
        migrated from: collaborations.robot 'Send issue deleted event'.
        """
        auth_headers()
        payload = _issue_event("ISSUE_DELETED", {
            "_key": TestIssueLifecycle.issue_key,
        })
        response = await client.post("/event", json=payload)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
