"""
Feature: SerialCreatedEvent dual-layer test suite
  Migrates Robot Framework serial creation tests (ROBOT-03) and adds new
  territory coverage for counter-based generation, duplicate detection,
  traceability guards, and data fields.

  Per D-01: Call event.save() (not event.apply()) — runs full lifecycle.
  Per D-02: Seed preconditions via fixtures -> instantiate event -> assert DB state.
  Per D-04: HTTP layer asserts response shape only.
"""
import pytest
from events.serial.serial_created import SerialCreatedEvent
from utils.exceptions import SerialCodeAlreadyPresent


def _make_info(user_key, product_key, **overrides):
    info = {
        "event_type": "SERIAL_CREATED",
        "primary": True,
        "user_key": user_key,
        "product_key": product_key,
        "data": [],
    }
    info.update(overrides)
    return info


class TestSerialCreatedDirect:
    """Direct event.save() tests for SerialCreatedEvent."""

    def test_serial_created_with_code(
        self, db, create_user, create_product
    ):
        """Robot migration: Serial created with explicit code persists to DB.

        Given a product with traceability_level='complete'
        When SerialCreatedEvent is saved with code='SN-TEST-001'
        Then a Serial document exists with code 'SN-TEST-001' and deleted=False
        """
        user = create_user()
        prod = create_product(traceability_level="complete")
        event = SerialCreatedEvent(info=_make_info(
            user["_key"], prod["product_key"],
            code="SN-TEST-001",
        ))
        event.save()
        serials = list(db.collection("Serial").find({"code": "SN-TEST-001"}))
        assert len(serials) == 1
        assert serials[0]["product_key"] == prod["product_key"]
        assert serials[0]["deleted"] is False

    def test_serial_created_without_code_generates_from_counter(
        self, db, create_user, create_product
    ):
        """New territory: Serial with counter_key generates code automatically.

        Given a product with traceability_level='complete' and serial_code_on_creation=True
        And a Counter document seeded with prefix='SN-' and padding=5
        When SerialCreatedEvent is saved without an explicit code
        Then a Serial document exists with a generated code starting with 'SN-'
        """
        user = create_user()
        counter_key = "test-counter-sn"
        db.collection("Counter").insert({
            "_key": counter_key,
            "value": 0,
            "prefix": "SN-",
            "padding": 5,
        })
        prod = create_product(
            traceability_level="complete",
            serial_code_on_creation=True,
            counter_key=counter_key,
        )
        event = SerialCreatedEvent(info=_make_info(
            user["_key"], prod["product_key"],
        ))
        event.save()
        serial_key = event.response["serial_key"]
        serial = db.collection("Serial").get(serial_key)
        assert serial is not None
        assert serial["code"].startswith("SN-")

    def test_serial_created_duplicate_code_raises(
        self, db, create_user, create_product, create_serial
    ):
        """New territory: Duplicate serial code for same product raises SerialCodeAlreadyPresent.

        Given a product with traceability_level='complete' and an existing serial with code 'SN-DUP-001'
        When SerialCreatedEvent is saved with code='SN-DUP-001' for the same product
        Then SerialCodeAlreadyPresent is raised
        """
        user = create_user()
        prod = create_product(traceability_level="complete")
        create_serial(product_key=prod["product_key"], code="SN-DUP-001")
        event = SerialCreatedEvent(info=_make_info(
            user["_key"], prod["product_key"],
            code="SN-DUP-001",
        ))
        with pytest.raises(SerialCodeAlreadyPresent):
            event.save()

    def test_serial_created_no_traceability_raises(
        self, db, create_user, create_product
    ):
        """New territory: Product without traceability rejects serial creation.

        Given a product with no traceability_level
        When SerialCreatedEvent is saved
        Then ValueError is raised with message containing 'Traceability is not enabled'
        """
        user = create_user()
        prod = create_product()  # no traceability_level
        event = SerialCreatedEvent(info=_make_info(
            user["_key"], prod["product_key"],
            code="SN-NO-TRACE",
        ))
        with pytest.raises(ValueError, match="Traceability is not enabled"):
            event.save()

    def test_serial_created_with_data_fields(
        self, db, create_user, create_product
    ):
        """Robot migration: Serial created with data fields persists form field values.

        Given a product with traceability_level='complete'
        When SerialCreatedEvent is saved with data containing form field values
        Then the Serial document's data list has matching entries with last_updated set
        """
        user = create_user()
        prod = create_product(traceability_level="complete")
        data = [{
            "step_key": "s1",
            "form_field_key": "ff1",
            "custom_field_key": "cf1",
            "value": "v1",
        }]
        event = SerialCreatedEvent(info=_make_info(
            user["_key"], prod["product_key"],
            code="SN-DATA-001",
            data=data,
        ))
        event.save()
        serial_key = event.response["serial_key"]
        serial = db.collection("Serial").get(serial_key)
        assert serial["data"] is not None
        assert len(serial["data"]) == 1
        assert serial["data"][0]["form_field_key"] == "ff1"
        assert serial["data"][0].get("last_updated") is not None


class TestSerialCreatedAPI:
    """HTTP API tests for SerialCreatedEvent via POST /event."""

    @pytest.mark.anyio
    async def test_http_serial_created_returns_200(
        self, db, client, auth_headers, create_product
    ):
        """New territory: HTTP serial creation returns 200 with serial_key.

        Given a product with traceability_level='complete'
        When POST /event is called with SERIAL_CREATED payload
        Then response status is 200 and response JSON contains serial_key
        """
        prod = create_product(traceability_level="complete")
        auth_headers("operator production")
        response = await client.post("/event", json={
            "event_type": "SERIAL_CREATED",
            "primary": True,
            "user_key": "test-user-key",
            "product_key": prod["product_key"],
            "code": "SN-API-001",
            "data": [],
        })
        assert response.status_code == 200
        assert "serial_key" in response.json()["detail"]

    @pytest.mark.anyio
    async def test_http_serial_created_duplicate_returns_422(
        self, db, client, auth_headers, create_product, create_serial
    ):
        """New territory: HTTP duplicate serial code returns 422.

        Given an existing serial with code 'SN-DUP-API'
        When POST /event is called with the same code for the same product
        Then response status is 422 and error_type is SerialCodeAlreadyPresent
        """
        prod = create_product(traceability_level="complete")
        create_serial(product_key=prod["product_key"], code="SN-DUP-API")
        auth_headers("operator production")
        response = await client.post("/event", json={
            "event_type": "SERIAL_CREATED",
            "primary": True,
            "user_key": "test-user-key",
            "product_key": prod["product_key"],
            "code": "SN-DUP-API",
            "data": [],
        })
        assert response.status_code == 422
        assert response.json()["detail"]["error_type"] == "SerialCodeAlreadyPresent"
