"""
Feature: SerialReleasedEvent dual-layer test suite (new territory)
  Tests for serial release — setting the released timestamp on a serial.
  Robot Framework never tested SerialReleased; this is entirely new coverage.

  Per D-01: Call event.save() — runs full lifecycle.
  Per D-02: Seed preconditions via fixtures -> instantiate event -> assert DB state.
  Per D-04: HTTP layer asserts response shape only.
"""
import pytest
from datetime import datetime, timezone
from events.serial.serial_released import SerialReleasedEvent


def _make_info(user_key, serial_key, **overrides):
    info = {
        "event_type": "SERIAL_RELEASED",
        "primary": True,
        "user_key": user_key,
        "serial_key": serial_key,
    }
    info.update(overrides)
    return info


class TestSerialReleasedDirect:
    """Direct event.save() tests for SerialReleasedEvent."""

    def test_serial_released_sets_timestamp(
        self, db, create_user, create_product, create_serial
    ):
        """New territory: Releasing a serial without explicit date sets event timestamp.

        Given an existing serial with released=None
        When SerialReleasedEvent is saved without explicit released date
        Then the Serial document's released field is not None
        """
        user = create_user()
        prod = create_product(traceability_level="complete")
        serial = create_serial(product_key=prod["product_key"], code="SN-REL-AUTO")
        event = SerialReleasedEvent(info=_make_info(
            user["_key"], serial["_key"],
        ))
        event.save()
        updated = db.collection("Serial").get(serial["_key"])
        assert updated["released"] is not None

    def test_serial_released_with_explicit_date(
        self, db, create_user, create_product, create_serial
    ):
        """New territory: Releasing a serial with explicit date uses provided datetime.

        Given an existing serial with released=None
        When SerialReleasedEvent is saved with released=datetime(2025, 6, 15, 12, 0, 0)
        Then the Serial document's released field matches the provided datetime
        """
        user = create_user()
        prod = create_product(traceability_level="complete")
        serial = create_serial(product_key=prod["product_key"], code="SN-REL-EXPLICIT")
        release_date = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        event = SerialReleasedEvent(info=_make_info(
            user["_key"], serial["_key"],
            released=release_date.isoformat(),
        ))
        event.save()
        updated = db.collection("Serial").get(serial["_key"])
        assert updated["released"] is not None
        # The released field should contain the date we provided
        # ArangoDB may serialize datetime differently, so check the date component
        released_str = str(updated["released"])
        assert "2025-06-15" in released_str

    def test_serial_released_already_released_overwrites(
        self, db, create_user, create_product, create_serial
    ):
        """New territory: Re-releasing an already-released serial overwrites timestamp.

        Given an existing serial with released=datetime(2025, 1, 1)
        When SerialReleasedEvent is saved with a new released datetime
        Then the Serial document's released field is updated to the new value
        """
        user = create_user()
        prod = create_product(traceability_level="complete")
        serial = create_serial(
            product_key=prod["product_key"],
            code="SN-REL-OVERWRITE",
            released=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        new_date = datetime(2025, 12, 25, 0, 0, 0, tzinfo=timezone.utc)
        event = SerialReleasedEvent(info=_make_info(
            user["_key"], serial["_key"],
            released=new_date.isoformat(),
        ))
        event.save()
        updated = db.collection("Serial").get(serial["_key"])
        released_str = str(updated["released"])
        assert "2025-12-25" in released_str


class TestSerialReleasedAPI:
    """HTTP API tests for SerialReleasedEvent via POST /event."""

    @pytest.mark.anyio
    async def test_http_serial_released_returns_200(
        self, db, client, auth_headers, create_product, create_serial
    ):
        """New territory: HTTP serial release returns 200 with serial_key.

        Given an existing serial
        When POST /event with SERIAL_RELEASED payload
        Then response status is 200 and response JSON contains serial_key
        """
        prod = create_product(traceability_level="complete")
        serial = create_serial(product_key=prod["product_key"], code="SN-REL-API")
        auth_headers("operator production")
        response = await client.post("/event", json={
            "event_type": "SERIAL_RELEASED",
            "primary": True,
            "user_key": "test-user-key",
            "serial_key": serial["_key"],
        })
        assert response.status_code == 200
        assert "serial_key" in response.json()["detail"]
