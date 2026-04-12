"""
Feature: SerialUpdatedEvent dual-layer test suite
  Migrates Robot Framework serial update test (ROBOT-03) and adds new territory
  coverage for code changes, data merging, nonexistent serial, duplicate code,
  unreleasing, and config-blocked code edits.

  Per D-01: Call event.save() — runs full lifecycle.
  Per D-02: Seed preconditions via fixtures -> instantiate event -> assert DB state.
  Per D-04: HTTP layer asserts response shape only.

  Note: Robot's "serial updated event" actually sends event_type "SERIAL_DELETED"
  (bug in Robot helper — see SerialsEvents.py line 39). The pytest migration tests
  the correct SERIAL_UPDATED behavior.
"""
import pytest
from datetime import datetime, timezone
from events.serial.serial_updated import SerialUpdatedEvent
from utils.exceptions import SerialNotUpdatedError, SerialCodeAlreadyPresent


def _make_info(user_key, serial_key, **overrides):
    info = {
        "event_type": "SERIAL_UPDATED",
        "primary": True,
        "user_key": user_key,
        "serial_key": serial_key,
    }
    info.update(overrides)
    return info


class TestSerialUpdatedDirect:
    """Direct event.save() tests for SerialUpdatedEvent."""

    def test_serial_updated_change_code(
        self, db, create_user, create_product, create_serial
    ):
        """New territory: Changing serial code persists the new code.

        Given an existing serial with code 'SN-OLD'
        When SerialUpdatedEvent is saved with serial_code='SN-NEW'
        Then the Serial document code is 'SN-NEW'
        """
        user = create_user()
        prod = create_product(traceability_level="complete")
        serial = create_serial(product_key=prod["product_key"], code="SN-OLD")
        event = SerialUpdatedEvent(info=_make_info(
            user["_key"], serial["_key"],
            serial_code="SN-NEW",
        ))
        event.save()
        updated = db.collection("Serial").get(serial["_key"])
        assert updated["code"] == "SN-NEW"

    def test_serial_updated_data_merge(
        self, db, create_user, create_product, create_serial
    ):
        """Robot migration: Updating serial data merges with existing data fields.

        Given an existing serial with data containing form_field_key='ff1' value='old'
        When SerialUpdatedEvent is saved with serial_data containing ff1 value='new'
        Then the Serial document data has ff1 with value='new' and last_updated set
        """
        user = create_user()
        prod = create_product(traceability_level="complete")
        serial = create_serial(
            product_key=prod["product_key"],
            code="SN-MERGE",
            data=[{"form_field_key": "ff1", "value": "old", "step_key": "s1", "custom_field_key": "c1"}],
        )
        event = SerialUpdatedEvent(info=_make_info(
            user["_key"], serial["_key"],
            serial_data=[{
                "form_field_key": "ff1",
                "value": "new",
                "step_key": "s1",
                "custom_field_key": "c1",
            }],
        ))
        event.save()
        updated = db.collection("Serial").get(serial["_key"])
        assert len(updated["data"]) == 1
        assert updated["data"][0]["form_field_key"] == "ff1"
        assert updated["data"][0]["value"] == "new"
        assert updated["data"][0].get("last_updated") is not None

    def test_serial_updated_nonexistent_raises(
        self, db, create_user
    ):
        """New territory: Updating a nonexistent serial raises SerialNotUpdatedError.

        Given no serial exists with key 'nonexistent-key'
        When SerialUpdatedEvent is saved with serial_key='nonexistent-key'
        Then SerialNotUpdatedError is raised
        """
        user = create_user()
        event = SerialUpdatedEvent(info=_make_info(
            user["_key"], "nonexistent-key",
            serial_code="SN-GHOST",
        ))
        with pytest.raises(SerialNotUpdatedError):
            event.save()

    def test_serial_updated_duplicate_code_raises(
        self, db, create_user, create_product, create_serial
    ):
        """New territory: Changing code to an existing code raises SerialCodeAlreadyPresent.

        Given two serials for the same product, serial A with code 'SN-A' and serial B with code 'SN-B'
        When SerialUpdatedEvent tries to change serial A's code to 'SN-B'
        Then SerialCodeAlreadyPresent is raised
        """
        user = create_user()
        prod = create_product(traceability_level="complete")
        serial_a = create_serial(product_key=prod["product_key"], code="SN-A")
        create_serial(product_key=prod["product_key"], code="SN-B")
        event = SerialUpdatedEvent(info=_make_info(
            user["_key"], serial_a["_key"],
            serial_code="SN-B",
        ))
        with pytest.raises(SerialCodeAlreadyPresent):
            event.save()

    def test_serial_updated_unrelease(
        self, db, create_user, create_product, create_serial
    ):
        """New territory: Unreleasing a serial clears the released timestamp.

        Given an existing serial with released=datetime(2025, 1, 1)
        When SerialUpdatedEvent is saved with unrelease=True
        Then the Serial document's released field is None
        """
        user = create_user()
        prod = create_product(traceability_level="complete")
        serial = create_serial(
            product_key=prod["product_key"],
            code="SN-RELEASE",
            released=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        event = SerialUpdatedEvent(info=_make_info(
            user["_key"], serial["_key"],
            unrelease=True,
        ))
        event.save()
        updated = db.collection("Serial").get(serial["_key"])
        assert updated["released"] is None

    def test_serial_updated_code_edit_blocked_by_config(
        self, db, create_user, create_product, create_serial, seed_config
    ):
        """New territory: Config blocks serial code editing when allow_serial_code_edit is False.

        Given seed_config('allow_serial_code_edit', value=False) and a serial with code 'SN-LOCKED'
        When SerialUpdatedEvent tries to change code to 'SN-NEW'
        Then SerialNotUpdatedError is raised with message containing 'not allowed'
        """
        user = create_user()
        prod = create_product(traceability_level="complete")
        serial = create_serial(product_key=prod["product_key"], code="SN-LOCKED")
        seed_config("allow_serial_code_edit", value=False)
        event = SerialUpdatedEvent(info=_make_info(
            user["_key"], serial["_key"],
            serial_code="SN-NEW",
        ))
        with pytest.raises(SerialNotUpdatedError, match="not allowed"):
            event.save()


class TestSerialUpdatedAPI:
    """HTTP API tests for SerialUpdatedEvent via POST /event."""

    @pytest.mark.anyio
    async def test_http_serial_updated_returns_200(
        self, db, client, auth_headers, create_product, create_serial
    ):
        """New territory: HTTP serial update returns 200.

        Given an existing serial
        When POST /event is called with SERIAL_UPDATED payload
        Then response status is 200
        """
        prod = create_product(traceability_level="complete")
        serial = create_serial(product_key=prod["product_key"], code="SN-API-UPD")
        auth_headers("operator production")
        response = await client.post("/event", json={
            "event_type": "SERIAL_UPDATED",
            "primary": True,
            "user_key": "test-user-key",
            "serial_key": serial["_key"],
            "serial_code": "SN-API-UPDATED",
        })
        assert response.status_code == 200
