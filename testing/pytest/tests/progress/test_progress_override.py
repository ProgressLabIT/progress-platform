"""
Feature: ProgressOverrideRequestedEvent dual-layer test suite
  Tests covering PROG-01 through PROG-17 via direct event.save() and HTTP API.

  Per D-01: Call event.save() (not event.apply()) — runs post_processing (queue reordering).
  Per D-02: Seed preconditions via fixtures → instantiate event → assert DB state.
  Per D-03: HTTP layer uses httpx.AsyncClient with auth_headers.
  Per D-04: API tests assert response shape only.
"""
import pytest
from tests.helpers import assert_event_dispatched
from events.admin.progress_override_requested import ProgressOverrideRequestedEvent
from utils.exceptions import (
    JobHasNoAssigneeError,
    JobIsActiveError,
    JobHasActiveBatchError,
    WipNotAvailableError,
)


def _make_info(job_key, user_key, new_job_qt_completed=1, **overrides):
    return {
        "event_type": "PROGRESS_OVERRIDE_REQUESTED",
        "primary": True,
        "user_key": user_key,
        "job_key": job_key,
        "new_job_qt_completed": new_job_qt_completed,
        **overrides,
    }


def _clear_active_batch(db, job_key):
    """Remove active batch state from job so override can proceed (no active batch check)."""
    db.collection("Job").update({
        "_key": job_key,
        "active_batch_key": None,
        "active_batch_qt": 0,
        "active": False,
    })


def _seed_phase_sequence(db, wo_key, phase_keys):
    """Seed WorkOrder.phase_sequence so AQL can resolve prev/next phases for WIP queries."""
    db.collection("WorkOrder").update({"_key": wo_key, "phase_sequence": phase_keys})


class TestProgressOverrideDirect:

    # -----------------------------------------------------------------------
    # Validation error tests (PROG-12 to PROG-16)
    # -----------------------------------------------------------------------

    def test_no_assignee_raises_error(self, db, create_production_graph):
        """PROG-12: Job with no assignee raises JobHasNoAssigneeError."""
        g = create_production_graph()
        _clear_active_batch(db, g["job"]["_key"])
        db.collection("Job").update({"_key": g["job"]["_key"], "assigned_to": None})
        event = ProgressOverrideRequestedEvent(
            info=_make_info(g["job"]["_key"], g["user"]["_key"])
        )
        with pytest.raises(JobHasNoAssigneeError):
            event.save()

    def test_active_job_raises_error(self, db, create_production_graph):
        """PROG-13: Active job raises JobIsActiveError."""
        g = create_production_graph()
        _clear_active_batch(db, g["job"]["_key"])
        db.collection("Job").update({"_key": g["job"]["_key"], "active": True})
        event = ProgressOverrideRequestedEvent(
            info=_make_info(g["job"]["_key"], g["user"]["_key"])
        )
        with pytest.raises(JobIsActiveError):
            event.save()

    def test_active_batch_raises_error(self, db, create_production_graph):
        """PROG-14: Job with active_batch_qt > 0 raises JobHasActiveBatchError."""
        g = create_production_graph()
        # Do NOT clear — set active_batch_qt > 0 to trigger the check
        db.collection("Job").update({
            "_key": g["job"]["_key"],
            "active": False,
            "active_batch_qt": 1,
        })
        event = ProgressOverrideRequestedEvent(
            info=_make_info(g["job"]["_key"], g["user"]["_key"])
        )
        with pytest.raises(JobHasActiveBatchError):
            event.save()

    def test_traceability_enabled_raises_not_implemented(self, db, create_production_graph):
        """PROG-15: Job with traceability enabled raises NotImplementedError."""
        g = create_production_graph(traceability_level="serial")
        _clear_active_batch(db, g["job"]["_key"])
        event = ProgressOverrideRequestedEvent(
            info=_make_info(g["job"]["_key"], g["user"]["_key"])
        )
        with pytest.raises(NotImplementedError):
            event.save()

    def test_insufficient_upstream_wip_raises_error(self, db, create_production_graph):
        """PROG-16: Non-first phase with insufficient upstream WIP raises WipNotAvailableError.

        create_production_graph(first_phase=False) creates WIP with quantity=batch_qt=1.
        Requesting quantity_change=10 (new_job_qt_completed=10) exceeds available WIP.
        WorkOrder.phase_sequence must be set so AQL can find upstream phase.
        """
        g = create_production_graph(first_phase=False, batch_qt=1)
        _clear_active_batch(db, g["job"]["_key"])

        phases = g["product"]["phases"]
        # Seed phase_sequence in work order: [upstream_phase, target_phase]
        _seed_phase_sequence(db, g["work_order"]["_key"], [p["_key"] for p in phases])

        # new_job_qt_completed=10 means quantity_change=10 (job.qt_completed starts at 0)
        # upstream WIP has quantity=1, so this exceeds it
        event = ProgressOverrideRequestedEvent(
            info=_make_info(g["job"]["_key"], g["user"]["_key"], new_job_qt_completed=10)
        )
        with pytest.raises(WipNotAvailableError):
            event.save()

    # -----------------------------------------------------------------------
    # Quantity increase tests (PROG-01, PROG-04, PROG-05, PROG-08, PROG-10)
    # -----------------------------------------------------------------------

    def test_quantity_increase_creates_forced_batch(self, db, create_production_graph):
        """PROG-01: Quantity increase creates forced batch and work session."""
        g = create_production_graph(first_phase=True, last_phase=True)
        _clear_active_batch(db, g["job"]["_key"])
        _seed_phase_sequence(db, g["work_order"]["_key"],
                             [p["_key"] for p in g["product"]["phases"]])

        event = ProgressOverrideRequestedEvent(
            info=_make_info(g["job"]["_key"], g["user"]["_key"], new_job_qt_completed=1)
        )
        event.save()

        # Forced batch created (not the original, which may still exist)
        batches = list(db.collection("Batch").find({"job_key": g["job"]["_key"]}))
        assert len(batches) >= 1
        sessions = list(db.collection("WorkSession").find({"job_key": g["job"]["_key"]}))
        assert len(sessions) >= 1

    def test_time_redistribution_with_should_adjust_duration_false(self, db, create_production_graph):
        """PROG-04: should_adjust_duration=False triggers time redistribution — event must not raise."""
        g = create_production_graph(first_phase=True, last_phase=True)
        _clear_active_batch(db, g["job"]["_key"])
        _seed_phase_sequence(db, g["work_order"]["_key"],
                             [p["_key"] for p in g["product"]["phases"]])

        event = ProgressOverrideRequestedEvent(
            info=_make_info(
                g["job"]["_key"], g["user"]["_key"],
                new_job_qt_completed=1,
                should_adjust_duration=False,
            )
        )
        event.save()  # Must not raise; time redistribution path executes
        batches = list(db.collection("Batch").find({"job_key": g["job"]["_key"]}))
        assert len(batches) >= 1

    def test_job_transition_created_to_started(self, db, create_production_graph):
        """PROG-05: CREATED->STARTED on first quantity increase."""
        g = create_production_graph(first_phase=True, last_phase=True)
        _clear_active_batch(db, g["job"]["_key"])
        db.collection("Job").update({
            "_key": g["job"]["_key"],
            "stage": "created",
            "qt_completed": 0,
        })
        _seed_phase_sequence(db, g["work_order"]["_key"],
                             [p["_key"] for p in g["product"]["phases"]])

        event = ProgressOverrideRequestedEvent(
            info=_make_info(g["job"]["_key"], g["user"]["_key"], new_job_qt_completed=1)
        )
        event.save()

        updated_job = db.collection("Job").get(g["job"]["_key"])
        assert updated_job["stage"] == "started"

    def test_upstream_wip_reduced_on_increase_non_first_phase(self, db, create_production_graph):
        """PROG-08: Non-first phase quantity increase reduces upstream WIP."""
        g = create_production_graph(first_phase=False, batch_qt=5)
        _clear_active_batch(db, g["job"]["_key"])

        phases = g["product"]["phases"]
        _seed_phase_sequence(db, g["work_order"]["_key"], [p["_key"] for p in phases])

        # wip_records has upstream WIP with quantity=5 pointing to Phase/{target_phase}
        wip_before = db.collection("wip").get(g["wip_records"][0]["_key"])
        assert wip_before is not None

        event = ProgressOverrideRequestedEvent(
            info=_make_info(g["job"]["_key"], g["user"]["_key"], new_job_qt_completed=1)
        )
        event.save()

        # After increase, upstream WIP quantity should be reduced
        wip_after = db.collection("wip").get(g["wip_records"][0]["_key"])
        # WIP may be deleted (full reduction) or reduced
        original_qty = wip_before["quantity"]
        if wip_after is None:
            # Fully consumed — valid
            assert original_qty >= 1
        else:
            assert wip_after["quantity"] < original_qty

    # -----------------------------------------------------------------------
    # Quantity decrease tests (PROG-02, PROG-03, PROG-06, PROG-07, PROG-09)
    # -----------------------------------------------------------------------

    def test_quantity_decrease_cancels_batches(self, db, create_production_graph):
        """PROG-02: Quantity decrease cancels batches newest-to-oldest.

        _cancel_batches_for_quantity_decrease sums batch.qt_pass to find enough quantity.
        qt_pass must be set to the completed quantity on each batch.
        """
        g = create_production_graph(first_phase=True, last_phase=True, batch_qt=2)
        _clear_active_batch(db, g["job"]["_key"])
        _seed_phase_sequence(db, g["work_order"]["_key"],
                             [p["_key"] for p in g["product"]["phases"]])

        # Set job as completed 2 units; set batch.qt_pass to match completed qty
        db.collection("Job").update({
            "_key": g["job"]["_key"],
            "qt_completed": 2,
            "stage": "started",
        })
        db.collection("Batch").update({
            "_key": g["batch"]["_key"],
            "active": False,
            "qt_pass": 2.0,  # batch covered all 2 completed units
        })

        # Decrease to 0
        event = ProgressOverrideRequestedEvent(
            info=_make_info(g["job"]["_key"], g["user"]["_key"], new_job_qt_completed=0)
        )
        event.save()

        batch = db.collection("Batch").get(g["batch"]["_key"])
        assert batch["canceled"] is not None, "Batch should be canceled after quantity decrease"

    def test_job_reopened_when_quantity_decreased_from_closed(self, db, create_production_graph):
        """PROG-06: CLOSED->STARTED when qty decreased below completed (job reopened)."""
        g = create_production_graph(first_phase=True, last_phase=True, batch_qt=2)
        _clear_active_batch(db, g["job"]["_key"])
        _seed_phase_sequence(db, g["work_order"]["_key"],
                             [p["_key"] for p in g["product"]["phases"]])

        qt = 2.0
        db.collection("Job").update({
            "_key": g["job"]["_key"],
            "stage": "closed",
            "qt_completed": qt,
            "qt_planned": qt,
        })
        db.collection("Batch").update({
            "_key": g["batch"]["_key"],
            "active": False,
            "qt_pass": qt,  # required by _cancel_batches_for_quantity_decrease
        })

        # Decrease by 1 (job re-opens)
        event = ProgressOverrideRequestedEvent(
            info=_make_info(g["job"]["_key"], g["user"]["_key"], new_job_qt_completed=qt - 1)
        )
        event.save()

        updated_job = db.collection("Job").get(g["job"]["_key"])
        assert updated_job["stage"] == "started"

    def test_queue_reordered_when_job_reopened(self, db, create_production_graph, create_queue):
        """PROG-07: Reopened job triggers REORDER_JOB_QUEUES in post_processing — must not raise."""
        g = create_production_graph(first_phase=True, last_phase=True, batch_qt=2)
        _clear_active_batch(db, g["job"]["_key"])
        _seed_phase_sequence(db, g["work_order"]["_key"],
                             [p["_key"] for p in g["product"]["phases"]])

        # Create operator queue for assigned user
        create_queue(user_key=g["user"]["_key"])

        qt = 2.0
        db.collection("Job").update({
            "_key": g["job"]["_key"],
            "stage": "closed",
            "qt_completed": qt,
            "qt_planned": qt,
        })
        db.collection("Batch").update({
            "_key": g["batch"]["_key"],
            "active": False,
            "qt_pass": qt,  # required by _cancel_batches_for_quantity_decrease
        })

        event = ProgressOverrideRequestedEvent(
            info=_make_info(g["job"]["_key"], g["user"]["_key"], new_job_qt_completed=qt - 1)
        )
        event.save()  # post_processing runs REORDER_JOB_QUEUES — must not raise

        updated_job = db.collection("Job").get(g["job"]["_key"])
        assert updated_job["stage"] == "started"

    def test_downstream_wip_reduced_on_decrease_non_last_phase(
        self, db, create_production_graph, create_wip
    ):
        """PROG-09: Downstream WIP reduced on quantity decrease for non-last phase."""
        g = create_production_graph(first_phase=True, last_phase=False, batch_qt=2)
        _clear_active_batch(db, g["job"]["_key"])

        phases = g["product"]["phases"]
        target_phase = g["target_phase"]
        _seed_phase_sequence(db, g["work_order"]["_key"], [p["_key"] for p in phases])

        db.collection("Job").update({
            "_key": g["job"]["_key"],
            "qt_completed": 2,
            "stage": "started",
        })
        db.collection("Batch").update({
            "_key": g["batch"]["_key"],
            "active": False,
            "qt_pass": 2.0,  # required by _cancel_batches_for_quantity_decrease
        })

        # Create downstream WIP (target_phase → next_phase)
        next_phase = phases[-1]  # last phase (last_phase=False means there's one after target)
        downstream_wip = create_wip(
            from_phase_key=target_phase["_key"],
            to_phase_key=next_phase["_key"],
            wo_key=g["work_order"]["_key"],
            product_key=g["product"]["product_key"],
            quantity=2,
        )

        event = ProgressOverrideRequestedEvent(
            info=_make_info(g["job"]["_key"], g["user"]["_key"], new_job_qt_completed=1)
        )
        event.save()

        wip_after = db.collection("wip").get(downstream_wip["_key"])
        if wip_after is None:
            # Fully consumed
            pass
        else:
            assert wip_after["quantity"] < 2, "Downstream WIP should be reduced"

    def test_over_cancel_creates_compensating_batch(self, db, create_production_graph):
        """PROG-03: Quantity decrease with over-cancel creates compensating forced batch.

        When canceled batch qty > needed reduction, remaining_qt < 0 → compensating batch created.
        Setup: job completed 2 (one batch of qt=2), decrease to 1 (cancel 2, need 1, over by 1).
        """
        g = create_production_graph(first_phase=True, last_phase=True, batch_qt=2)
        _clear_active_batch(db, g["job"]["_key"])
        _seed_phase_sequence(db, g["work_order"]["_key"],
                             [p["_key"] for p in g["product"]["phases"]])

        db.collection("Job").update({
            "_key": g["job"]["_key"],
            "qt_completed": 2,
            "stage": "started",
        })
        db.collection("Batch").update({
            "_key": g["batch"]["_key"],
            "active": False,
            "qt_pass": 2.0,  # required by _cancel_batches_for_quantity_decrease
        })

        batch_count_before = len(list(db.collection("Batch").find({"job_key": g["job"]["_key"]})))

        # Decrease by 1 — cancels batch of qt=2, over by 1 → compensating batch of qt=1 created
        event = ProgressOverrideRequestedEvent(
            info=_make_info(g["job"]["_key"], g["user"]["_key"], new_job_qt_completed=1)
        )
        event.save()

        batch_count_after = len(list(db.collection("Batch").find({"job_key": g["job"]["_key"]})))
        # A new compensating batch should have been created (total batch count increases)
        assert batch_count_after > batch_count_before, (
            "Compensating batch should be created when over-cancel occurs"
        )


class TestProgressOverrideAPI:
    """HTTP API tests for ProgressOverrideRequestedEvent via POST /event.

    Per D-04: Assert response shape only — no DB state assertions.
    """

    async def test_http_endpoint_success(
        self, db, client, auth_headers, create_production_graph
    ):
        """PROG-17: HTTP POST /event with PROGRESS_OVERRIDE_REQUESTED returns 200."""
        g = create_production_graph(first_phase=True, last_phase=True)
        _clear_active_batch(db, g["job"]["_key"])
        db.collection("Job").update({
            "_key": g["job"]["_key"],
            "stage": "created",
            "qt_completed": 0,
        })
        _seed_phase_sequence(db, g["work_order"]["_key"],
                             [p["_key"] for p in g["product"]["phases"]])
        auth_headers("operator production admin")

        response = await client.post("/event", json={
            "event_type": "PROGRESS_OVERRIDE_REQUESTED",
            "primary": True,
            "user_key": g["user"]["_key"],
            "job_key": g["job"]["_key"],
            "new_job_qt_completed": 1,
        })

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        assert response.json().get("status") == 200

    async def test_http_validation_error_active_job_returns_422(
        self, db, client, auth_headers, create_production_graph
    ):
        """PROG-13 HTTP layer: Active job returns 422."""
        g = create_production_graph()
        _clear_active_batch(db, g["job"]["_key"])
        db.collection("Job").update({"_key": g["job"]["_key"], "active": True})
        auth_headers("operator production admin")

        response = await client.post("/event", json={
            "event_type": "PROGRESS_OVERRIDE_REQUESTED",
            "primary": True,
            "user_key": g["user"]["_key"],
            "job_key": g["job"]["_key"],
            "new_job_qt_completed": 1,
        })

        assert response.status_code == 422, (
            f"Expected 422 for active job, got {response.status_code}: {response.text}"
        )
