"""
Feature: BatchCompletedEvent direct event instantiation
  Tests covering BATCH-01 to BATCH-14, BATCH-18 to BATCH-20 via event.save().

  Per D-01: Call event.save() (not event.apply()) — runs full lifecycle including post_processing.
  Per D-02: Seed preconditions via fixtures → instantiate event → call event.save() → assert DB state.
  Per D-05: For cascade children, assert Event collection has the expected child event type.
  Per D-06: Do NOT assert child event side effects in parent tests.
  Per D-07: Use assert_event_dispatched(db, "EVENT_TYPE_NAME") to verify child events.
"""
import pytest
from tests.helpers import assert_event_dispatched
from events.production.batch_completed import BatchCompletedEvent


def _set_last_work_session(db, job_key, ws_key):
    """Set last_work_session_started and activate the job so work_session_key is populated.

    Note: job.active must be True so _get_job_data() sets info.work_session_key
    from job.last_work_session_started (it returns None when active=False).
    WorkSessionClosedEvent requires work_session_key: str (not Optional).
    """
    db.collection("Job").update({
        "_key": job_key,
        "last_work_session_started": ws_key,
        "active": True,
    })


def _book_wip_to_job(db, wip_records, job_key):
    """Re-point WIP edges from Phase target to Job so WIPRemovedEvent can find them.

    WIPRemovedEvent queries wip edges with _to=Job/{job_key} (booked WIP).
    create_production_graph creates unbooked WIP (_to=Phase/{phase_key}).
    This helper simulates the WIPBookedEvent side-effect needed for test setup.
    """
    for wip in wip_records:
        db.collection("wip").update({
            "_key": wip["_key"],
            "_to": f"Job/{job_key}",
            "active": True,
        })


def _make_info(g, **overrides):
    return {
        "event_type": "BATCH_COMPLETED",
        "primary": True,
        "user_key": g["user"]["_key"],
        "active_batch_key": g["batch"]["_key"],
        "completed_batch_qt": g["batch"]["qt_total"],
        **overrides,
    }


class TestBatchCompletedDirect:

    # -----------------------------------------------------------------------
    # Parametrized matrix (BATCH-20)
    # Per D-08: curated pairwise set — not full 32 cartesian product
    # Per D-09: auto_new_batch=True + last_phase=True is excluded (no-op: last batch anyway)
    # Per D-11: each row exercises a distinct flag interaction
    #
    # Excluded combinations:
    #   - auto_new_batch=True + last_phase=True (no-op: last batch, no new batch created per D-09)
    #   - traceability="serial" + warehouse=True without BOM (inventory paths need component stock)
    #   - first_phase=False rows: WIP is booked to job via _book_wip_to_job before save()
    #
    # Matrix columns: first_phase, last_phase, traceability, warehouse, auto_new_batch
    # -----------------------------------------------------------------------
    @pytest.mark.parametrize("first_phase,last_phase,traceability,warehouse,auto_new_batch,expected_children", [
        # Row 1: simple middle-of-chain batch, no extras
        (False, False, "none",  False, False, ["WORK_SESSION_CLOSED", "WIP_REMOVED", "WIP_DECLARED"]),
        # Row 2: first phase, last phase — full release path
        (True,  True,  "none",  False, False, ["WORK_SESSION_CLOSED", "BATCH_RELEASED"]),
        # Row 3: first phase, not last — WIP declared only
        (True,  False, "none",  False, False, ["WORK_SESSION_CLOSED", "WIP_DECLARED"]),
        # Row 4: not first phase, last phase — WIP removed + release
        (False, True,  "none",  False, False, ["WORK_SESSION_CLOSED", "WIP_REMOVED", "BATCH_RELEASED"]),
        # Row 5: auto_new_batch=True, not last phase (first phase for simplicity, avoids WIP booking)
        (True,  False, "none",  False, True,  ["WORK_SESSION_CLOSED", "WIP_DECLARED", "BATCH_CREATED", "WORK_SESSION_CREATED"]),
        # Row 6: warehouse management enabled, last phase — production movement
        (True,  True,  "none",  True,  False, ["WORK_SESSION_CLOSED", "BATCH_RELEASED", "MOVEMENT_COMPLETED"]),
        # Row 7: batch traceability, last phase — serials released
        # Note: SerialUpdatedEvent only fires when serial_data > 0 OR serial_code generated.
        # Without step data, only SERIAL_RELEASED fires (unconditional loop on last_phase).
        (True,  True,  "batch", False, False, ["WORK_SESSION_CLOSED", "BATCH_RELEASED", "SERIAL_RELEASED"]),
        # Row 8: batch traceability, non-last — batch_serial edges exist but no step data → no SERIAL_UPDATED
        # Standalone test_traceability_serial_updated_per_serial covers BATCH-11 with step data.
        (True,  False, "batch", False, False, ["WORK_SESSION_CLOSED", "WIP_DECLARED"]),
        # Row 9: non-first + non-last + batch traceability — WIP chain only (no serial update without step data)
        (False, False, "batch", False, False, ["WORK_SESSION_CLOSED", "WIP_REMOVED", "WIP_DECLARED"]),
    ], ids=[
        "middle-no-extras",
        "first-and-last-release",
        "first-only-wip-declared",
        "last-only-wip-removed-release",
        "auto-new-batch",
        "warehouse-production-movement",
        "batch-traceability-released",
        "batch-traceability-updated-only",
        "non-first-non-last-batch-traceability",
    ])
    def test_parametrized_matrix(
        self,
        db,
        create_production_graph,
        first_phase,
        last_phase,
        traceability,
        warehouse,
        auto_new_batch,
        expected_children,
    ):
        batch_qty = 1
        g = create_production_graph(
            first_phase=first_phase,
            last_phase=last_phase,
            traceability_level=traceability,
            warehouse_management=warehouse,
            auto_new_batch=auto_new_batch,
            batch_qt=batch_qty,
        )

        # For auto_new_batch tests: keep job open AND enable next_batch_available
        # (BatchCompletedEvent checks is_next_batch_available = job.next_batch_available)
        if auto_new_batch:
            db.collection("Job").update({
                "_key": g["job"]["_key"],
                "qt_planned": 100.0,
                "next_batch_available": True,
            })

        # For non-last-phase non-auto_new_batch, keep job open
        if not last_phase and not auto_new_batch:
            db.collection("Job").update({"_key": g["job"]["_key"], "qt_planned": 100.0})

        # WIPRemovedEvent needs booked WIP (_to=Job/...) for non-first-phase rows
        if not first_phase and g["wip_records"]:
            _book_wip_to_job(db, g["wip_records"], g["job"]["_key"])

        _set_last_work_session(db, g["job"]["_key"], g["work_session"]["_key"])

        extra_info = {}
        if traceability in ("batch", "serial") and g["serials"]:
            extra_info["batch_serial_keys"] = [s["_key"] for s in g["serials"]]

        event = BatchCompletedEvent(info=_make_info(g, **extra_info))
        event.save()

        for child_type in expected_children:
            assert_event_dispatched(db, child_type)

    # -----------------------------------------------------------------------
    # BATCH-01: Direct event updates batch record and closes work session
    # -----------------------------------------------------------------------

    def test_batch_record_updated_and_work_session_closed(self, db, create_production_graph):
        """BATCH-01: Direct event.save() updates batch record and closes work session."""
        g = create_production_graph()
        _set_last_work_session(db, g["job"]["_key"], g["work_session"]["_key"])

        event = BatchCompletedEvent(info=_make_info(g))
        event.save()

        batch = db.collection("Batch").get(g["batch"]["_key"])
        assert batch["active"] is False, "Batch should be deactivated after completion"
        assert_event_dispatched(db, "WORK_SESSION_CLOSED")

    # -----------------------------------------------------------------------
    # BATCH-02: Last batch triggers JobClosedEvent child
    # -----------------------------------------------------------------------

    def test_last_batch_triggers_job_closed(self, db, create_production_graph):
        """BATCH-02: Last batch (new_job_qt_completed >= qt_planned) triggers JOB_CLOSED child."""
        g = create_production_graph(batch_qt=1)
        # Set qt_planned equal to batch_qt so this batch is the last one
        db.collection("Job").update({"_key": g["job"]["_key"], "qt_planned": 1.0})
        _set_last_work_session(db, g["job"]["_key"], g["work_session"]["_key"])

        event = BatchCompletedEvent(info=_make_info(g))
        event.save()

        assert_event_dispatched(db, "JOB_CLOSED")

    # -----------------------------------------------------------------------
    # BATCH-03: Non-last batch with auto_new_batch creates new Batch + WorkSession
    # -----------------------------------------------------------------------

    def test_auto_new_batch_creates_batch_and_work_session(self, db, create_production_graph):
        """BATCH-03: auto_new_batch=True creates BATCH_CREATED + WORK_SESSION_CREATED children."""
        g = create_production_graph(auto_new_batch=True)
        # Keep job open and set next_batch_available=True (required by BatchCompletedEvent)
        db.collection("Job").update({
            "_key": g["job"]["_key"],
            "qt_planned": 100.0,
            "next_batch_available": True,
        })
        _set_last_work_session(db, g["job"]["_key"], g["work_session"]["_key"])

        event = BatchCompletedEvent(info=_make_info(g))
        event.save()

        assert_event_dispatched(db, "BATCH_CREATED")
        assert_event_dispatched(db, "WORK_SESSION_CREATED")

    # -----------------------------------------------------------------------
    # BATCH-04: Non-last batch without auto_new_batch sets job inactive
    # -----------------------------------------------------------------------

    def test_no_auto_batch_sets_job_inactive(self, db, create_production_graph):
        """BATCH-04: Non-last batch without auto_new_batch sets job.active=False, active_batch_key=None."""
        g = create_production_graph(auto_new_batch=False, last_phase=False)
        # Keep job open
        db.collection("Job").update({"_key": g["job"]["_key"], "qt_planned": 100.0})
        _set_last_work_session(db, g["job"]["_key"], g["work_session"]["_key"])

        event = BatchCompletedEvent(info=_make_info(g))
        event.save()

        job = db.collection("Job").get(g["job"]["_key"])
        assert job["active"] is False
        assert job["active_batch_key"] is None

    # -----------------------------------------------------------------------
    # BATCH-05: First phase does not generate WIPRemovedEvent
    # -----------------------------------------------------------------------

    def test_first_phase_no_wip_removed(self, db, create_production_graph):
        """BATCH-05: First phase batch completion does not generate WIP_REMOVED event."""
        g = create_production_graph(first_phase=True)
        _set_last_work_session(db, g["job"]["_key"], g["work_session"]["_key"])

        event = BatchCompletedEvent(info=_make_info(g))
        event.save()

        results = list(db.collection("Event").find({"event_type": "WIP_REMOVED"}))
        assert len(results) == 0, "First phase must not generate WIP_REMOVED event"

    # -----------------------------------------------------------------------
    # BATCH-06: Non-first phase generates WIPRemovedEvent child
    # -----------------------------------------------------------------------

    def test_non_first_phase_wip_removed(self, db, create_production_graph):
        """BATCH-06: Non-first phase batch completion generates WIP_REMOVED child event."""
        g = create_production_graph(first_phase=False)
        # Book WIP to job so WIPRemovedEvent can find it
        _book_wip_to_job(db, g["wip_records"], g["job"]["_key"])
        _set_last_work_session(db, g["job"]["_key"], g["work_session"]["_key"])

        event = BatchCompletedEvent(info=_make_info(g))
        event.save()

        assert_event_dispatched(db, "WIP_REMOVED")

    # -----------------------------------------------------------------------
    # BATCH-07: Non-last phase generates WIPDeclaredEvent child
    # -----------------------------------------------------------------------

    def test_non_last_phase_wip_declared(self, db, create_production_graph):
        """BATCH-07: Non-last phase batch completion generates WIP_DECLARED child event."""
        g = create_production_graph(last_phase=False)
        # Keep job open
        db.collection("Job").update({"_key": g["job"]["_key"], "qt_planned": 100.0})
        _set_last_work_session(db, g["job"]["_key"], g["work_session"]["_key"])

        event = BatchCompletedEvent(info=_make_info(g))
        event.save()

        assert_event_dispatched(db, "WIP_DECLARED")

    # -----------------------------------------------------------------------
    # BATCH-08: Last phase triggers BatchReleasedEvent child
    # -----------------------------------------------------------------------

    def test_last_phase_batch_released(self, db, create_production_graph):
        """BATCH-08: Last phase batch completion triggers BATCH_RELEASED child event."""
        g = create_production_graph(last_phase=True)
        _set_last_work_session(db, g["job"]["_key"], g["work_session"]["_key"])

        event = BatchCompletedEvent(info=_make_info(g))
        event.save()

        assert_event_dispatched(db, "BATCH_RELEASED")

    # -----------------------------------------------------------------------
    # BATCH-09: Last phase + warehouse management generates production MovementCompletedEvent
    # -----------------------------------------------------------------------

    def test_warehouse_last_phase_production_movement(self, db, create_production_graph):
        """BATCH-09: Last phase + warehouse management generates MOVEMENT_COMPLETED (production) child."""
        g = create_production_graph(last_phase=True, warehouse_management=True)
        _set_last_work_session(db, g["job"]["_key"], g["work_session"]["_key"])

        event = BatchCompletedEvent(info=_make_info(g))
        event.save()

        assert_event_dispatched(db, "MOVEMENT_COMPLETED")

    # -----------------------------------------------------------------------
    # BATCH-10: Warehouse management generates consumption MovementCompletedEvent per BOM line
    # -----------------------------------------------------------------------

    def test_warehouse_consumption_movement_per_bom_line(
        self, db, create_production_graph, create_inventory_at_position
    ):
        """BATCH-10: BOM + warehouse management generates MOVEMENT_COMPLETED (consumption) per BOM line."""
        g = create_production_graph(
            last_phase=True,
            warehouse_management=True,
            with_bom=True,
        )
        # Seed component inventory at IN position so consumption movement can proceed
        component_product_key = g["bom_data"]["component_product"]["product_key"]
        create_inventory_at_position("IN", component_product_key, quantity=100.0)
        _set_last_work_session(db, g["job"]["_key"], g["work_session"]["_key"])

        event = BatchCompletedEvent(info=_make_info(g))
        event.save()

        assert_event_dispatched(db, "MOVEMENT_COMPLETED")

    # -----------------------------------------------------------------------
    # BATCH-11: Traceability enabled fetches serials and calls SerialUpdatedEvent per serial
    # -----------------------------------------------------------------------

    def test_traceability_serial_updated_per_serial(self, db, create_production_graph):
        """BATCH-11: Traceability enabled triggers SERIAL_UPDATED per serial.

        SerialUpdatedEvent fires when serial_data > 0 OR serial_code is not None.
        We use first_phase=True + a counter_key on the serial (no existing code)
        to trigger serial code generation, which satisfies the serial_code != None condition.
        """
        g = create_production_graph(traceability_level="batch", first_phase=True, last_phase=False)
        db.collection("Job").update({"_key": g["job"]["_key"], "qt_planned": 100.0})

        if not g["serials"]:
            pytest.skip("No serials — traceability_level='batch' required")

        serial_key = g["serials"][0]["_key"]
        counter_key = "test-counter-batch11"
        if not db.collection("Counter").get(counter_key):
            db.collection("Counter").insert({
                "_key": counter_key,
                "template": ["SN-", "#4"],
                "next_tick": 1,
            })
        # Remove code so _handle_serial_code triggers generation via counter
        db.collection("Serial").update({
            "_key": serial_key,
            "code": None,
            "counter_key": counter_key,
        })

        _set_last_work_session(db, g["job"]["_key"], g["work_session"]["_key"])

        event = BatchCompletedEvent(info=_make_info(g))
        event.save()

        assert_event_dispatched(db, "SERIAL_UPDATED")

    # -----------------------------------------------------------------------
    # BATCH-12: Traceability + last phase triggers SerialReleasedEvent per serial
    # -----------------------------------------------------------------------

    def test_traceability_last_phase_serial_released(self, db, create_production_graph):
        """BATCH-12: Traceability + last phase triggers SERIAL_RELEASED per serial."""
        g = create_production_graph(traceability_level="batch", last_phase=True)
        _set_last_work_session(db, g["job"]["_key"], g["work_session"]["_key"])

        extra_info = {}
        if g["serials"]:
            extra_info["batch_serial_keys"] = [s["_key"] for s in g["serials"]]

        event = BatchCompletedEvent(info=_make_info(g, **extra_info))
        event.save()

        assert_event_dispatched(db, "SERIAL_RELEASED")

    # -----------------------------------------------------------------------
    # BATCH-14: Step data without step_check stores batch execution data
    # -----------------------------------------------------------------------

    def test_step_data_stored_without_step_check(self, db, create_production_graph):
        """BATCH-14: step_data included without step_check stores StepExecutionData records."""
        g = create_production_graph(step_check=False, num_steps=1)
        _set_last_work_session(db, g["job"]["_key"], g["work_session"]["_key"])

        step_key = g["product"]["steps"][0]["_key"]
        step_data = [{"step_key": step_key, "form_data": []}]

        event = BatchCompletedEvent(info=_make_info(g, step_data=step_data))
        event.save()

        records = list(db.collection("StepExecutionData").find({"step_key": step_key}))
        assert len(records) >= 1, "StepExecutionData record must exist for completed step"

    # -----------------------------------------------------------------------
    # BATCH-18: Serial code generation via counter on first_phase serial with no code
    # -----------------------------------------------------------------------

    def test_serial_code_generation_first_phase(self, db, create_production_graph):
        """BATCH-18: First phase serial with no code and a counter_key gets code generated."""
        g = create_production_graph(traceability_level="batch", first_phase=True)

        if not g["serials"]:
            pytest.skip("No serials created — traceability_level='batch' required")

        serial_key = g["serials"][0]["_key"]

        # Ensure the Counter document exists with correct schema (template + next_tick)
        counter_key = "test-counter-batch18"
        existing = db.collection("Counter").get(counter_key)
        if not existing:
            db.collection("Counter").insert({
                "_key": counter_key,
                "template": ["SN-", "#4"],
                "next_tick": 1,
            })

        # Set serial to have no code but have counter_key (triggers _handle_serial_code)
        db.collection("Serial").update({
            "_key": serial_key,
            "code": None,
            "counter_key": counter_key,
        })

        _set_last_work_session(db, g["job"]["_key"], g["work_session"]["_key"])

        event = BatchCompletedEvent(info=_make_info(
            g, batch_serial_keys=[serial_key]
        ))
        event.save()

        updated_serial = db.collection("Serial").get(serial_key)
        assert updated_serial.get("code") is not None, (
            "Serial code should be generated from counter on first_phase completion"
        )

    # -----------------------------------------------------------------------
    # BATCH-19: Media file copy safely skipped in testcontainer
    # -----------------------------------------------------------------------

    def test_batch_media_files_not_required_for_event_completion(self, db, create_production_graph):
        """BATCH-19: Media file copy is skipped safely in testcontainer (no /media mount).
        The event must complete successfully regardless."""
        g = create_production_graph(traceability_level="batch")
        _set_last_work_session(db, g["job"]["_key"], g["work_session"]["_key"])

        extra_info = {}
        if g["serials"]:
            extra_info["batch_serial_keys"] = [s["_key"] for s in g["serials"]]

        event = BatchCompletedEvent(info=_make_info(g, **extra_info))
        event.save()  # Must not raise even though /media is not mounted
