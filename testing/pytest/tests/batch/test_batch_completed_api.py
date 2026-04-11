"""
Feature: BatchCompletedEvent HTTP API
  Tests covering BATCH-15, BATCH-16, BATCH-17, BATCH-21 via the /event endpoint.

  Per D-03: Uses httpx.AsyncClient with auth_headers fixture.
  Per D-04: API tests assert on HTTP response shape only — no DB state assertions.
"""
import pytest


def _batch_event_payload(g, **overrides):
    """Build a BATCH_COMPLETED event payload from a production graph dict."""
    return {
        "event_type": "BATCH_COMPLETED",
        "primary": True,
        "user_key": g["user"]["_key"],
        "active_batch_key": g["batch"]["_key"],
        "completed_batch_qt": g["batch"]["qt_total"],
        "work_session_key": g["work_session"]["_key"],
        **overrides,
    }


def _set_job_active(db, job_key, work_session_key):
    """Set job active with the current work session so BatchCompleted can find it."""
    db.collection("Job").update({
        "_key": job_key,
        "active": True,
        "last_work_session_started": work_session_key,
    })


class TestBatchCompletedAPI:
    """HTTP API tests for BatchCompletedEvent via POST /event.

    Per D-04: API tests assert on HTTP response shape, not DB state.
    All tests call auth_headers() to set up the dependency override before requests.
    """

    async def test_step_check_active_returns_422(
        self, db, client, auth_headers, create_production_graph
    ):
        """BATCH-15: Step check conflict returns 422.

        Given a job with step_check=True and an active work session
        When POST /event is called with BATCH_COMPLETED including step_data
        Then the response status is 422
        And the error message references step check
        """
        g = create_production_graph(step_check=True, num_steps=1)
        job = g["job"]
        ws = g["work_session"]
        _set_job_active(db, job["_key"], ws["_key"])
        auth_headers("operator production")

        # Provide step_data to trigger the step_check validation branch
        step_key = g["product"]["steps"][0]["_key"]
        payload = _batch_event_payload(g, step_data=[{
            "step_key": step_key,
            "form_data": [],
        }])

        response = await client.post("/event", json=payload)

        assert response.status_code == 422, (
            f"Expected 422 for step_check conflict, got {response.status_code}: {response.text}"
        )
        detail = response.json().get("detail", {})
        message = detail.get("message", "") or ""
        assert "step check" in message.lower() or "stepcompletedEvent" in message or "step" in message.lower(), (
            f"Expected step_check error message, got: {message}"
        )

    async def test_quantity_mismatch_returns_422(
        self, db, client, auth_headers, create_production_graph
    ):
        """BATCH-16: Quantity mismatch returns 422.

        Given a batch with qt_total=5.0
        When POST /event is called with completed_batch_qt=3.0
        Then the response status is 422
        And the error message references quantity mismatch
        """
        g = create_production_graph(batch_qt=5)
        job = g["job"]
        ws = g["work_session"]
        _set_job_active(db, job["_key"], ws["_key"])
        auth_headers("operator production")

        # Send qt=3 when batch.qt_total=5 — quantity mismatch
        payload = _batch_event_payload(g, completed_batch_qt=3.0)

        response = await client.post("/event", json=payload)

        assert response.status_code == 422, (
            f"Expected 422 for quantity mismatch, got {response.status_code}: {response.text}"
        )
        detail = response.json().get("detail", {})
        message = detail.get("message", "") or ""
        assert any(
            keyword in message.lower()
            for keyword in ("quantity", "batch", "match", "mismatch")
        ), f"Expected quantity mismatch error message, got: {message}"

    async def test_closed_job_returns_422(
        self, db, client, auth_headers, create_production_graph
    ):
        """BATCH-17: Closed job returns 422.

        Given a job with stage='closed'
        When POST /event is called with BATCH_COMPLETED
        Then the response status is 422
        And the error message contains 'closed'
        """
        g = create_production_graph()
        job = g["job"]
        ws = g["work_session"]
        _set_job_active(db, job["_key"], ws["_key"])

        # Close the job
        db.collection("Job").update({"_key": job["_key"], "stage": "closed"})
        auth_headers("operator production")

        payload = _batch_event_payload(g)

        response = await client.post("/event", json=payload)

        assert response.status_code == 422, (
            f"Expected 422 for closed job, got {response.status_code}: {response.text}"
        )
        detail = response.json().get("detail", {})
        message = detail.get("message", "") or ""
        assert "closed" in message.lower(), (
            f"Expected 'closed' in error message, got: {message}"
        )

    async def test_happy_path_returns_200(
        self, db, client, auth_headers, create_production_graph
    ):
        """BATCH-21: Valid batch completion returns 200 with job_data.

        Given a single-phase job with no traceability or warehouse management
        And an active work session
        When POST /event is called with a valid BATCH_COMPLETED payload
        Then the response status is 200
        And the response detail contains job_data
        """
        g = create_production_graph(
            first_phase=True,
            last_phase=True,
            traceability_level="none",
            warehouse_management=False,
        )
        job = g["job"]
        ws = g["work_session"]
        _set_job_active(db, job["_key"], ws["_key"])
        auth_headers("operator production")

        payload = _batch_event_payload(g)

        response = await client.post("/event", json=payload)

        assert response.status_code == 200, (
            f"Expected 200 for happy path, got {response.status_code}: {response.text}"
        )
        detail = response.json().get("detail")
        assert detail is not None, "Response missing 'detail' key"
        assert "job_data" in detail, (
            f"Expected 'job_data' in detail, got keys: {list(detail.keys()) if isinstance(detail, dict) else detail}"
        )
