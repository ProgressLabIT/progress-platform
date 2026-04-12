"""
Feature: Job Lifecycle Events via HTTP API
  Tests covering JOB_STARTED, JOB_PAUSED, and JOB_RESUMED events.
  Migrated from Robot Framework production.robot test cases.

  Per D-03: HTTP API layer only — no direct event instantiation.
  Per D-06: BDD-style docstrings noting Robot provenance.
"""
from datetime import datetime, timezone


def _event_payload(event_type, g, **extra):
    """Build an event payload from a production graph dict.

    Mirrors the structure in Robot's ProductionEvents.py.
    """
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


class TestJobLifecycle:
    """HTTP API tests for job lifecycle events via POST /event.

    All tests use create_production_graph to set up a complete domain graph
    with a job in 'created' stage, ready to be started.
    """

    async def test_job_started_returns_200(
        self, client, auth_headers, create_production_graph
    ):
        """Given a job in 'created' stage with an assigned operator
        When POST /event is called with JOB_STARTED
        Then the response status is 200 and contains job_data.
        Migrated from: production.robot 'Start job' test case.
        """
        g = create_production_graph()
        auth_headers("operator production")

        payload = _event_payload("JOB_STARTED", g)
        response = await client.post("/event", json=payload)

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        detail = response.json().get("detail", {})
        assert "job_data" in detail, (
            f"Expected 'job_data' in detail, got keys: {list(detail.keys())}"
        )

    async def test_job_started_already_active_returns_422(
        self, client, auth_headers, create_production_graph
    ):
        """Given a job that has already been started
        When POST /event is called with JOB_STARTED again
        Then the response status is 422 indicating the job is already started.
        """
        g = create_production_graph()
        auth_headers("operator production")

        payload = _event_payload("JOB_STARTED", g)
        first = await client.post("/event", json=payload)
        assert first.status_code == 200, (
            f"First JOB_STARTED failed: {first.status_code}: {first.text}"
        )

        second = await client.post("/event", json=payload)
        assert second.status_code == 422, (
            f"Expected 422 for already-started job, got {second.status_code}: {second.text}"
        )

    async def test_job_paused_returns_200(
        self, client, auth_headers, create_production_graph
    ):
        """Given a job that is currently active (started)
        When POST /event is called with JOB_PAUSED
        Then the response status is 200.
        Migrated from: production.robot 'Pause job' test case.
        """
        g = create_production_graph()
        auth_headers("operator production")

        # Start the job first
        start_payload = _event_payload("JOB_STARTED", g)
        start_resp = await client.post("/event", json=start_payload)
        assert start_resp.status_code == 200, (
            f"JOB_STARTED failed: {start_resp.status_code}: {start_resp.text}"
        )

        # Now pause it
        pause_payload = _event_payload("JOB_PAUSED", g)
        response = await client.post("/event", json=pause_payload)

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )

    async def test_job_paused_inactive_job_returns_422(
        self, client, auth_headers, create_production_graph
    ):
        """Given a job that has not been started
        When POST /event is called with JOB_PAUSED
        Then the response status is 422 because the job is not active.
        """
        g = create_production_graph()
        auth_headers("operator production")

        payload = _event_payload("JOB_PAUSED", g)
        response = await client.post("/event", json=payload)

        assert response.status_code == 422, (
            f"Expected 422 for inactive job, got {response.status_code}: {response.text}"
        )

    async def test_job_resumed_returns_200(
        self, client, auth_headers, create_production_graph
    ):
        """Given a job that was started and then paused
        When POST /event is called with JOB_RESUMED
        Then the response status is 200.
        Migrated from: production.robot 'Resume job' test case.
        """
        g = create_production_graph()
        auth_headers("operator production")

        # Start then pause the job
        start_resp = await client.post(
            "/event", json=_event_payload("JOB_STARTED", g)
        )
        assert start_resp.status_code == 200, (
            f"JOB_STARTED failed: {start_resp.status_code}: {start_resp.text}"
        )
        pause_resp = await client.post(
            "/event", json=_event_payload("JOB_PAUSED", g)
        )
        assert pause_resp.status_code == 200, (
            f"JOB_PAUSED failed: {pause_resp.status_code}: {pause_resp.text}"
        )

        # Now resume it
        resume_payload = _event_payload("JOB_RESUMED", g)
        response = await client.post("/event", json=resume_payload)

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )

    async def test_job_lifecycle_sequential_flow(
        self, client, auth_headers, create_production_graph
    ):
        """Given a complete production graph
        When the full lifecycle JOB_STARTED -> JOB_PAUSED -> JOB_RESUMED is executed
        Then all three events return 200.
        Migrated from: production.robot sequential test suite execution order.
        """
        g = create_production_graph()
        auth_headers("operator production")

        # JOB_STARTED
        resp_start = await client.post(
            "/event", json=_event_payload("JOB_STARTED", g)
        )
        assert resp_start.status_code == 200, (
            f"JOB_STARTED failed: {resp_start.status_code}: {resp_start.text}"
        )

        # JOB_PAUSED
        resp_pause = await client.post(
            "/event", json=_event_payload("JOB_PAUSED", g)
        )
        assert resp_pause.status_code == 200, (
            f"JOB_PAUSED failed: {resp_pause.status_code}: {resp_pause.text}"
        )

        # JOB_RESUMED
        resp_resume = await client.post(
            "/event", json=_event_payload("JOB_RESUMED", g)
        )
        assert resp_resume.status_code == 200, (
            f"JOB_RESUMED failed: {resp_resume.status_code}: {resp_resume.text}"
        )
