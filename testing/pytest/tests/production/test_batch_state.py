"""
Feature: ActiveBatchChanged Event via HTTP API
  Tests covering the ACTIVE_BATCH_CHANGED event for batch state transitions.
  Migrated from Robot Framework production.robot 'Change active batch' test case.

  Per D-02: Does NOT duplicate v2.0 batch completion tests (see tests/batch/).
  Per D-03: HTTP API layer only — no direct event instantiation.
"""
from datetime import datetime, timezone


def _event_payload(event_type, g, **extra):
    """Build an event payload from a production graph dict."""
    return {
        "event_type": event_type,
        "user_key": g["user"]["_key"],
        "user_session_key": "test-session-key",
        "job_key": g["job"]["_key"],
        "product_key": g["product"]["_key"],
        "work_order_key": g["work_order"]["_key"],
        "phase_key": g["target_phase"]["_key"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **extra,
    }


def _batch_change_payload(g, new_active_batch_qt, **extra):
    """Build an ACTIVE_BATCH_CHANGED event payload.

    Mirrors Robot's ProductionEvents.py active_batch_changed_event structure.
    """
    return _event_payload("ACTIVE_BATCH_CHANGED", g,
        new_active_batch_qt=new_active_batch_qt,
        **extra,
    )


async def _start_job(client, g):
    """Send JOB_STARTED event to activate a job before batch operations."""
    payload = _event_payload("JOB_STARTED", g)
    resp = await client.post("/event", json=payload)
    assert resp.status_code == 200, f"JOB_STARTED failed: {resp.text}"
    return resp


class TestActiveBatchChanged:
    """HTTP API tests for ACTIVE_BATCH_CHANGED event via POST /event.

    Important boundary: these tests cover ACTIVE_BATCH_CHANGED only.
    Batch completion is covered by v2.0 in tests/batch/ — no overlap.
    """

    async def test_active_batch_changed_returns_200(
        self, client, auth_headers, create_production_graph
    ):
        """Given an active job with a current batch
        When POST /event is called with ACTIVE_BATCH_CHANGED and new_active_batch_qt=5
        Then the response status is 200.
        Migrated from: production.robot 'Change active batch' test case.
        """
        g = create_production_graph()
        auth_headers("operator production")

        await _start_job(client, g)

        payload = _batch_change_payload(g, new_active_batch_qt=5)
        response = await client.post("/event", json=payload)

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )

    async def test_active_batch_changed_inactive_job_returns_422(
        self, client, auth_headers, create_production_graph
    ):
        """Given a job that has not been started
        When POST /event is called with ACTIVE_BATCH_CHANGED
        Then the response status is 422 because the job has no active batch.
        """
        g = create_production_graph()
        auth_headers("operator production")

        payload = _batch_change_payload(g, new_active_batch_qt=5)
        response = await client.post("/event", json=payload)

        assert response.status_code == 422, (
            f"Expected 422 for inactive job, got {response.status_code}: {response.text}"
        )

    async def test_active_batch_changed_creates_new_batch(
        self, client, auth_headers, create_production_graph
    ):
        """Given an active job with an initial batch
        When POST /event is called with ACTIVE_BATCH_CHANGED and new_active_batch_qt=3
        Then the response status is 200
        And the job's active batch quantity reflects the new value.
        """
        g = create_production_graph()
        auth_headers("operator production")

        await _start_job(client, g)

        payload = _batch_change_payload(g, new_active_batch_qt=3)
        response = await client.post("/event", json=payload)

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )

        # Verify the job data reflects the updated batch quantity
        detail = response.json().get("detail", {})
        job_data = detail.get("job_data", {})
        assert job_data.get("active_batch_qt") == 3, (
            f"Expected active_batch_qt=3, got {job_data.get('active_batch_qt')}"
        )
