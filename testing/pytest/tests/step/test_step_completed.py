"""
Feature: StepCompletedEvent
  Tests covering all 8 STEP requirements via two layers:
  - TestStepCompletedDirect: direct event instantiation against ArangoDB testcontainer
  - TestStepCompletedAPI: HTTP API layer via httpx.AsyncClient

Covers: STEP-01, STEP-02, STEP-03, STEP-04, STEP-05, STEP-06, STEP-07, STEP-08
"""
import pytest

from events.production.step_completed import StepCompletedEvent
from tests.helpers import assert_event_dispatched


def _set_job_active(db, job_key, work_session_key, step_keys):
    """Helper: set job active with work session and step_sequence.

    step_sequence must be a list of objects with _key so that the
    ALL_BATCH_STEPS_DONE AQL query (step_sequence[*]._key) works correctly.
    """
    db.collection("Job").update({
        "_key": job_key,
        "active": True,
        "last_work_session_started": work_session_key,
        "step_sequence": [{"_key": sk, "type": "instruction"} for sk in step_keys],
    })


def _step_event_info(user_key, batch_key, step_key, form_data=None, **extra):
    """Build a STEP_COMPLETED event info dict with required defaults.

    form_data defaults to [] — StepExecutionData.form_data: list[FormFieldValue]
    requires a list; None is not coerced by Pydantic v2.
    """
    return dict(
        event_type="STEP_COMPLETED",
        primary=True,
        user_key=user_key,
        batch_key=batch_key,
        step_key=step_key,
        form_data=form_data if form_data is not None else [],
        **extra,
    )


class TestStepCompletedDirect:
    """Direct event instantiation tests — asserts on DB state.

    Per D-01: Tests call event.save() against real ArangoDB testcontainer.
    Per D-02: Seed preconditions via factory fixtures → instantiate event → assert DB state.
    """

    def test_happy_path_non_last_step(self, db, create_production_graph):
        """STEP-01: Non-last step completion sets status to done without triggering batch completion.

        Given a job with two steps in the target phase
        When the first step is completed
        Then the StepExecutionData record has status='done'
        And no BATCH_COMPLETED event is dispatched
        """
        g = create_production_graph(num_steps=2)
        job = g["job"]
        batch = g["batch"]
        user = g["user"]
        ws = g["work_session"]
        steps = [s for s in g["product"]["steps"]
                 if s["phase_key"] == g["target_phase"]["_key"]]
        assert len(steps) == 2, "Expected 2 steps for non-last-step test"

        first_step = steps[0]
        second_step = steps[1]

        _set_job_active(db, job["_key"], ws["_key"],
                        [first_step["_key"], second_step["_key"]])

        event = StepCompletedEvent(info=_step_event_info(
            user["_key"], batch["_key"], first_step["_key"],
        ))
        event.save()

        # Verify StepExecutionData created with status=done
        results = list(db.collection("StepExecutionData").find({
            "batch_key": batch["_key"],
            "step_key": first_step["_key"],
            "canceled": None,
        }))
        assert len(results) == 1, "Expected exactly one StepExecutionData record"
        assert results[0]["status"] == "done", (
            f"Expected status='done', got '{results[0]['status']}'"
        )

        # BatchCompleted should NOT be dispatched (first of two steps)
        batch_events = list(db.collection("Event").find({"event_type": "BATCH_COMPLETED"}))
        assert not batch_events, "BatchCompleted should not be dispatched for non-last step"

    def test_last_step_triggers_batch_completed(self, db, create_production_graph):
        """STEP-02: Last step completion dispatches BatchCompletedEvent.

        Given a job with a single step in the target phase
        When that step is completed
        Then a BATCH_COMPLETED event is recorded in the Event collection
        """
        g = create_production_graph(num_steps=1)
        job = g["job"]
        batch = g["batch"]
        user = g["user"]
        ws = g["work_session"]
        steps = [s for s in g["product"]["steps"]
                 if s["phase_key"] == g["target_phase"]["_key"]]
        assert len(steps) == 1

        _set_job_active(db, job["_key"], ws["_key"], [steps[0]["_key"]])

        event = StepCompletedEvent(info=_step_event_info(
            user["_key"], batch["_key"], steps[0]["_key"],
        ))
        event.save()

        # Per D-07: verify child event was recorded in Event collection
        assert_event_dispatched(db, "BATCH_COMPLETED")

    def test_form_data_stored(self, db, create_production_graph):
        """STEP-03: Form data is persisted in StepExecutionData.

        Given a job with steps and a CustomField document
        When a step is completed with form_data referencing that field
        Then the StepExecutionData record contains the submitted form_data values
        """
        # CustomField must exist before inserting form_data referencing it
        cf_key = "cf-weight-test"
        if not db.collection("CustomField").has(cf_key):
            db.collection("CustomField").insert({
                "_key": cf_key,
                "name": "Weight",
                "type": "number",
                "mandatory": False,
            })

        g = create_production_graph(num_steps=2)
        job = g["job"]
        batch = g["batch"]
        user = g["user"]
        ws = g["work_session"]
        steps = [s for s in g["product"]["steps"]
                 if s["phase_key"] == g["target_phase"]["_key"]]

        _set_job_active(db, job["_key"], ws["_key"], [s["_key"] for s in steps])

        event = StepCompletedEvent(info=_step_event_info(
            user["_key"], batch["_key"], steps[0]["_key"],
            # FormFieldValue requires form_field_key (not field_key)
            # custom_field_key links to the CustomField document _key
            form_data=[{"form_field_key": cf_key, "custom_field_key": cf_key, "value": "42.5"}],
        ))
        event.save()

        results = list(db.collection("StepExecutionData").find({
            "batch_key": batch["_key"],
            "step_key": steps[0]["_key"],
            "canceled": None,
        }))
        assert len(results) == 1
        stored_form_data = results[0].get("form_data") or []
        assert any(
            fd.get("form_field_key") == cf_key and fd.get("value") == "42.5"
            for fd in stored_form_data
        ), f"Expected form_data with form_field_key={cf_key} value='42.5', got: {stored_form_data}"

    def test_work_session_key_set(self, db, create_production_graph):
        """STEP-04: Work session key is resolved from the active session.

        Given a job with an active work session
        When a step is completed
        Then the event's work_session_key matches the active session
        And the StepExecutionData record stores the same work_session_key
        """
        g = create_production_graph(num_steps=2)
        job = g["job"]
        batch = g["batch"]
        user = g["user"]
        ws = g["work_session"]
        steps = [s for s in g["product"]["steps"]
                 if s["phase_key"] == g["target_phase"]["_key"]]

        _set_job_active(db, job["_key"], ws["_key"], [s["_key"] for s in steps])

        event = StepCompletedEvent(info=_step_event_info(
            user["_key"], batch["_key"], steps[0]["_key"],
        ))
        event.save()

        # get_current_work_session() sets info.work_session_key during apply()
        assert event.info.work_session_key == ws["_key"], (
            f"Expected work_session_key={ws['_key']}, got {event.info.work_session_key}"
        )

        results = list(db.collection("StepExecutionData").find({
            "batch_key": batch["_key"],
            "step_key": steps[0]["_key"],
            "canceled": None,
        }))
        assert results[0]["work_session_key"] == ws["_key"]

    def test_temp_step_data_overwritten(self, db, create_production_graph):
        """STEP-05: Temporary StepExecutionData is overwritten on completion.

        Given a batch with a pre-existing temp StepExecutionData record (status=None)
        When the step is completed
        Then exactly one StepExecutionData record exists for that step
        And its status is 'done'
        """
        g = create_production_graph(num_steps=2)
        job = g["job"]
        batch = g["batch"]
        user = g["user"]
        ws = g["work_session"]
        steps = [s for s in g["product"]["steps"]
                 if s["phase_key"] == g["target_phase"]["_key"]]

        _set_job_active(db, job["_key"], ws["_key"], [s["_key"] for s in steps])

        step = steps[0]

        # Remove any factory-created SXD for this step so we start with exactly one
        # temp record (the one we insert below), giving the event a clean overwrite target.
        for doc in list(db.collection("StepExecutionData").find({
            "batch_key": batch["_key"],
            "step_key": step["_key"],
        })):
            db.collection("StepExecutionData").delete(doc["_key"])

        # Pre-insert a temp SXD record (status=None, canceled=None)
        # The event's apply() will find this via find(..., canceled=None) and overwrite it
        db.collection("StepExecutionData").insert({
            "batch_key": batch["_key"],
            "step_key": step["_key"],
            "job_key": job["_key"],
            "user_key": user["_key"],
            "work_session_key": ws["_key"],
            "status": None,
            "form_data": [],
            "completed": None,
            "modified": None,
            "canceled": None,
        })

        event = StepCompletedEvent(info=_step_event_info(
            user["_key"], batch["_key"], step["_key"],
        ))
        event.save()

        results = list(db.collection("StepExecutionData").find({
            "batch_key": batch["_key"],
            "step_key": step["_key"],
            "canceled": None,
        }))
        assert len(results) == 1, (
            f"Expected 1 SXD record after overwrite, got {len(results)}"
        )
        assert results[0]["status"] == "done", (
            f"Expected status='done' after overwrite, got '{results[0]['status']}'"
        )

    def test_missing_batch_raises_value_error(self, db, create_production_graph):
        """STEP-06: Non-existent batch raises ValueError.

        Given a non-existent batch_key
        When a StepCompletedEvent is saved
        Then a ValueError is raised with 'not found' in the message
        """
        g = create_production_graph()
        user = g["user"]

        event = StepCompletedEvent(info=dict(
            event_type="STEP_COMPLETED",
            primary=True,
            user_key=user["_key"],
            batch_key="nonexistent-batch-key",
            step_key="nonexistent-step-key",
            form_data=[],
        ))

        with pytest.raises(ValueError, match="not found"):
            event.save()


class TestStepCompletedAPI:
    """HTTP API layer tests — asserts on HTTP response shape.

    Per D-03: Uses httpx.AsyncClient with auth_headers fixture.
    Per D-04: API tests assert on HTTP response shape, not DB state.
    """

    async def test_http_endpoint_success(self, db, client, auth_headers, create_production_graph):
        """STEP-07, STEP-08: Successful step completion returns 200 with job_data.

        Given an active job with a single step
        When POST /event is called with a valid STEP_COMPLETED payload
        Then the response status is 200
        And the response detail contains job_data
        """
        g = create_production_graph(num_steps=1)
        job = g["job"]
        batch = g["batch"]
        user = g["user"]
        ws = g["work_session"]
        steps = [s for s in g["product"]["steps"]
                 if s["phase_key"] == g["target_phase"]["_key"]]

        _set_job_active(db, job["_key"], ws["_key"], [steps[0]["_key"]])

        auth_headers("operator production")

        response = await client.post("/event", json={
            "event_type": "STEP_COMPLETED",
            "primary": True,
            "user_key": user["_key"],
            "batch_key": batch["_key"],
            "step_key": steps[0]["_key"],
            "form_data": [],
        })

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        detail = response.json().get("detail")
        assert detail is not None, "Response missing 'detail' key"
        assert "job_data" in detail, (
            f"Expected 'job_data' in detail, got keys: {list(detail.keys())}"
        )

    async def test_http_missing_batch_returns_422(self, db, client, auth_headers, create_production_graph):
        """STEP-06 (HTTP): Non-existent batch returns 422.

        Given a non-existent batch_key in the payload
        When POST /event is called with STEP_COMPLETED
        Then the response status is 422
        """
        g = create_production_graph()
        user = g["user"]

        auth_headers("operator production")

        response = await client.post("/event", json={
            "event_type": "STEP_COMPLETED",
            "primary": True,
            "user_key": user["_key"],
            "batch_key": "nonexistent-batch-key",
            "step_key": "nonexistent-step-key",
        })

        assert response.status_code == 422, (
            f"Expected 422, got {response.status_code}: {response.text}"
        )
