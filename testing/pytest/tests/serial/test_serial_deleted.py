"""
Feature: SerialDeletedEvent dual-layer test suite
  Migrates Robot Framework serial deletion test (ROBOT-03) and adds new territory
  coverage for hard delete, config blocking, children cascade, and contains edge cleanup.

  Per D-01: Call event.save() — runs full lifecycle.
  Per D-02: Seed preconditions via fixtures -> instantiate event -> assert DB state.
  Per D-04: HTTP layer asserts response shape only.
"""
import pytest
from events.serial.serial_deleted import SerialDeletedEvent
from utils.exceptions import SerialNotDeletedError


def _make_info(user_key, serial_key, **overrides):
    info = {
        "event_type": "SERIAL_DELETED",
        "primary": True,
        "user_key": user_key,
        "serial_key": serial_key,
    }
    info.update(overrides)
    return info


class TestSerialDeletedDirect:
    """Direct event.save() tests for SerialDeletedEvent."""

    def test_serial_soft_deleted(
        self, db, create_user, create_product, create_serial, seed_config
    ):
        """Robot migration: Soft delete marks serial.deleted with event key (not False).

        Given an existing serial and allow_serial_delete=True
        When SerialDeletedEvent is saved with soft=True (default)
        Then the Serial document's deleted field is a truthy string (the event key)
        """
        user = create_user()
        prod = create_product(traceability_level="complete")
        serial = create_serial(product_key=prod["product_key"])
        seed_config("allow_serial_delete", value=True)
        event = SerialDeletedEvent(info=_make_info(
            user["_key"], serial["_key"],
            soft=True,
        ))
        event.save()
        updated = db.collection("Serial").get(serial["_key"])
        assert updated["deleted"]  # truthy — event key string
        assert updated["deleted"] is not False

    def test_serial_hard_deleted(
        self, db, create_user, create_product, create_serial, seed_config
    ):
        """New territory: Hard delete removes the serial document entirely.

        Given an existing serial and allow_serial_delete=True
        When SerialDeletedEvent is saved with soft=False
        Then db.collection('Serial').get(serial_key) returns None
        """
        user = create_user()
        prod = create_product(traceability_level="complete")
        serial = create_serial(product_key=prod["product_key"])
        seed_config("allow_serial_delete", value=True)
        event = SerialDeletedEvent(info=_make_info(
            user["_key"], serial["_key"],
            soft=False,
        ))
        event.save()
        assert db.collection("Serial").get(serial["_key"]) is None

    def test_serial_delete_blocked_by_config(
        self, db, create_user, create_product, create_serial, seed_config
    ):
        """New territory: Config blocks serial deletion when allow_serial_delete is False.

        Given seed_config('allow_serial_delete', value=False) and an existing serial
        When SerialDeletedEvent is saved with primary=True
        Then SerialNotDeletedError is raised with message containing 'not allowed by configuration'
        """
        user = create_user()
        prod = create_product(traceability_level="complete")
        serial = create_serial(product_key=prod["product_key"])
        seed_config("allow_serial_delete", value=False)
        event = SerialDeletedEvent(info=_make_info(
            user["_key"], serial["_key"],
        ))
        with pytest.raises(SerialNotDeletedError, match="not allowed by configuration"):
            event.save()

    def test_serial_delete_children_cascade(
        self, db, create_user, create_product, create_serial, seed_config
    ):
        """Robot migration: Deleting with delete_children=True cascades to child serials.

        Given a parent serial and a child serial linked via contains edge
        And allow_serial_delete=True
        When SerialDeletedEvent is saved with delete_children=True
        Then both parent and child Serial documents have deleted set to truthy values
        """
        user = create_user()
        prod = create_product(traceability_level="complete")
        parent = create_serial(product_key=prod["product_key"], code="SN-PARENT")
        child = create_serial(product_key=prod["product_key"], code="SN-CHILD")
        # Link child to parent via contains edge
        db.collection("contains").insert({
            "_from": f"Serial/{parent['_key']}",
            "_to": f"Serial/{child['_key']}",
            "confirmed": True,
            "replaced": False,
        })
        seed_config("allow_serial_delete", value=True)
        event = SerialDeletedEvent(info=_make_info(
            user["_key"], parent["_key"],
            delete_children=True,
        ))
        event.save()
        parent_doc = db.collection("Serial").get(parent["_key"])
        child_doc = db.collection("Serial").get(child["_key"])
        assert parent_doc["deleted"]  # truthy
        assert child_doc["deleted"]  # truthy

    def test_serial_delete_removes_contains_edges(
        self, db, create_user, create_product, create_serial, seed_config
    ):
        """New territory: Deleting a serial removes its outgoing contains edges.

        Given a serial with a contains edge
        And allow_serial_delete=True
        When SerialDeletedEvent is saved
        Then contains edges from that serial are removed
        """
        user = create_user()
        prod = create_product(traceability_level="complete")
        serial = create_serial(product_key=prod["product_key"], code="SN-EDGE")
        child = create_serial(product_key=prod["product_key"], code="SN-EDGE-CHILD")
        db.collection("contains").insert({
            "_from": f"Serial/{serial['_key']}",
            "_to": f"Serial/{child['_key']}",
            "confirmed": True,
            "replaced": False,
        })
        seed_config("allow_serial_delete", value=True)
        event = SerialDeletedEvent(info=_make_info(
            user["_key"], serial["_key"],
        ))
        event.save()
        edges = list(db.collection("contains").find({
            "_from": f"Serial/{serial['_key']}",
        }))
        assert len(edges) == 0


class TestSerialDeletedAPI:
    """HTTP API tests for SerialDeletedEvent via POST /event."""

    @pytest.mark.anyio
    async def test_http_serial_deleted_returns_200(
        self, db, client, auth_headers, create_product, create_serial, seed_config
    ):
        """New territory: HTTP serial deletion returns 200.

        Given an existing serial and allow_serial_delete=True
        When POST /event with SERIAL_DELETED payload and soft=true
        Then response status is 200
        """
        prod = create_product(traceability_level="complete")
        serial = create_serial(product_key=prod["product_key"])
        seed_config("allow_serial_delete", value=True)
        auth_headers("operator production")
        response = await client.post("/event", json={
            "event_type": "SERIAL_DELETED",
            "primary": True,
            "user_key": "test-user-key",
            "serial_key": serial["_key"],
            "soft": True,
        })
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_http_serial_delete_blocked_returns_422(
        self, db, client, auth_headers, create_product, create_serial, seed_config
    ):
        """New territory: HTTP serial deletion blocked by config returns 422.

        Given allow_serial_delete=False
        When POST /event with SERIAL_DELETED payload
        Then response status is 422
        """
        prod = create_product(traceability_level="complete")
        serial = create_serial(product_key=prod["product_key"])
        seed_config("allow_serial_delete", value=False)
        auth_headers("operator production")
        response = await client.post("/event", json={
            "event_type": "SERIAL_DELETED",
            "primary": True,
            "user_key": "test-user-key",
            "serial_key": serial["_key"],
        })
        assert response.status_code == 422
