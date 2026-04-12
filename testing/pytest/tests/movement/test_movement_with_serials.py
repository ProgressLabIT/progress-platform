"""
Feature: Movement with serial traceability — gap analysis complement tests
  Fills coverage gaps between Robot Framework's single movement test and the
  v2.0 MovementCompleted 18-test suite (test_movement_completed.py).

  Gap Analysis (Robot movement test vs v2.0 suite):
  -----------------------------------------------------------------
  Robot's test: MOVEMENT_CREATED event (receipt, serial_code, position_from, position_to)
  Robot's helper sends event_type "MOVEMENT_CREATED" — but the backend handler is
  MovementCompletedEvent (event_type MOVEMENT_COMPLETED). Robot's position_from is
  overridden by the model validator anyway (receipt always sets position_from='OUT').

  v2.0 MOVE-01: Receipt without serial — covered
  v2.0 MOVE-02 (success): Receipt with serial_code — covered (creates Serial doc)
  v2.0 MOVE-02 (error): Traceable receipt without serial — covered
  v2.0 MOVE-03: Duplicate serial receipt — covered
  v2.0 MOVE-16: HTTP receipt — covered (no serial_code)

  Gaps identified:
  1. v2.0 MOVE-02 does NOT verify serial_key is set on the is_in_position edge
     (only checks Serial doc creation). This is the key link between inventory
     tracking and serial traceability.
  2. v2.0 MOVE-16 HTTP test sends receipt without serial_code — no HTTP test
     exercises the serial+receipt path.

  These tests add ONLY the gap scenarios — they do NOT duplicate MOVE-01 through
  MOVE-16 from the v2.0 suite.
"""
import pytest
from events.inventory.movement_completed import MovementCompletedEvent


def _make_info(user_key, movement_type, product_key=None, position_from=None,
               position_to=None, qt_planned=1.0, qt_confirmed=1.0, **overrides):
    info = {
        "event_type": "MOVEMENT_COMPLETED",
        "primary": True,
        "user_key": user_key,
        "movement_type": movement_type,
        "qt_planned": qt_planned,
        "qt_confirmed": qt_confirmed,
    }
    if product_key is not None:
        info["product_key"] = product_key
    if position_from is not None:
        info["position_from"] = position_from
    if position_to is not None:
        info["position_to"] = position_to
    info.update(overrides)
    return info


def _inv(db, product_key, position_key):
    """Return is_in_position records for product at position."""
    return list(db.collection("is_in_position").find({
        "_from": f"Product/{product_key}",
        "_to": f"Position/{position_key}",
    }))


class TestMovementSerialPositionDirect:
    """Direct event.save() tests for movement+serial gap scenarios."""

    def test_receipt_with_serial_tracks_serial_in_inventory(
        self, db, create_user, create_product, create_position
    ):
        """Robot migration: Receipt with serial_code sets serial_key on is_in_position edge.

        Given a product with traceability_level='complete' and a destination position
        When MovementCompletedEvent is saved with serial_code='SN-TRACK-001'
        Then the is_in_position edge has serial_key set to the created serial's key
        """
        user = create_user()
        prod = create_product(traceability_level="complete")
        dest = create_position()
        event = MovementCompletedEvent(info=_make_info(
            user["_key"], "receipt",
            product_key=prod["product_key"],
            position_to=dest["_key"],
            serial_code="SN-TRACK-001",
        ))
        event.save()
        records = _inv(db, prod["product_key"], dest["_key"])
        assert len(records) >= 1
        assert records[0].get("serial_key") is not None
        # Verify the serial_key matches the created serial
        serial = list(db.collection("Serial").find({"code": "SN-TRACK-001"}))
        assert len(serial) == 1
        assert records[0]["serial_key"] == serial[0]["_key"]


class TestMovementSerialPositionAPI:
    """HTTP API tests for movement+serial gap scenarios."""

    @pytest.mark.anyio
    async def test_http_receipt_with_serial_and_positions(
        self, db, client, auth_headers, create_user, create_product, create_position
    ):
        """Robot migration: HTTP receipt with serial_code returns 200.

        Given a traceable product and a destination position
        When POST /event with MOVEMENT_COMPLETED receipt including serial_code
        Then response status is 200
        """
        user = create_user()
        prod = create_product(traceability_level="complete")
        dest = create_position()
        auth_headers("operator warehouse")
        response = await client.post("/event", json={
            "event_type": "MOVEMENT_COMPLETED",
            "primary": True,
            "user_key": user["_key"],
            "movement_type": "receipt",
            "serial_code": "SN-API-MOVE-001",
            "product_key": prod["product_key"],
            "position_to": dest["_key"],
            "qt_planned": 1.0,
            "qt_confirmed": 1.0,
        })
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
