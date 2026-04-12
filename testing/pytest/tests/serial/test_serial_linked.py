"""
Feature: SerialLinkedEvent test suite (new territory)
  Tests for serial linking — component-to-parent and component-to-batch
  relationships via the contains edge collection. Robot Framework never tested
  SerialLinked; this is entirely new coverage.

  All tests set process_inventory=False to isolate serial linking logic from
  inventory movement side effects. Inventory integration is tracked as BATCH-13
  (tech debt, deferred).

  Per D-01: Call event.save() — runs full lifecycle.
  Per D-02: Seed preconditions via fixtures -> instantiate event -> assert DB state.
"""
import pytest
from events.serial.serial_linked import SerialLinkedEvent
from utils.exceptions import SerialNotLinkedError


def _make_info(user_key, child_serial_key, **overrides):
    info = {
        "event_type": "SERIAL_LINKED",
        "primary": True,
        "user_key": user_key,
        "child_serial_key": child_serial_key,
        "process_inventory": False,
    }
    info.update(overrides)
    return info


class TestSerialLinkedDirect:
    """Direct event.save() tests for SerialLinkedEvent."""

    def test_link_child_to_parent_serial(
        self, db, create_user, create_product, create_serial,
        create_work_order, seed_config
    ):
        """New territory: Linking a child serial to a parent creates a contains edge.

        Given a parent serial and a child serial
        And a WorkOrder with traceability_level='serial'
        And inventory management disabled
        When SerialLinkedEvent is saved with parent_serial_key and child_serial_key
        Then a contains edge exists from parent to child with confirmed=True
        """
        user = create_user()
        prod = create_product(traceability_level="complete")
        parent = create_serial(product_key=prod["product_key"], code="SN-PARENT")
        child = create_serial(product_key=prod["product_key"], code="SN-CHILD")
        wo = create_work_order(product_key=prod["product_key"], traceability_level="serial")
        seed_config("enable_inventory_management", value=False)
        event = SerialLinkedEvent(info=_make_info(
            user["_key"], child["_key"],
            parent_serial_key=parent["_key"],
            wo_key=wo["_key"],
        ))
        event.save()
        edges = list(db.collection("contains").find({
            "_from": f"Serial/{parent['_key']}",
            "_to": f"Serial/{child['_key']}",
        }))
        assert len(edges) == 1
        assert edges[0]["confirmed"] is True

    def test_link_child_to_batch(
        self, db, create_user, create_product, create_serial,
        create_work_order, create_batch, create_job, seed_config
    ):
        """New territory: Linking a child serial to a batch (no traceability on WO).

        Given a child serial, a WorkOrder with traceability_level=None, and a Batch
        When SerialLinkedEvent is saved with batch_key and no parent_serial_key
        Then a contains edge exists from Batch to Serial
        """
        user = create_user()
        prod = create_product(traceability_level="complete")
        child = create_serial(product_key=prod["product_key"], code="SN-BATCH-CHILD")
        wo = create_work_order(product_key=prod["product_key"])  # no traceability_level
        job = create_job(wo_key=wo["_key"], phase_key=prod["phases"][0]["_key"])
        batch = create_batch(job_key=job["_key"], work_order_key=wo["_key"])
        seed_config("enable_inventory_management", value=False)
        event = SerialLinkedEvent(info=_make_info(
            user["_key"], child["_key"],
            batch_key=batch["_key"],
            wo_key=wo["_key"],
        ))
        event.save()
        edges = list(db.collection("contains").find({
            "_from": f"Batch/{batch['_key']}",
            "_to": f"Serial/{child['_key']}",
        }))
        assert len(edges) >= 1

    def test_link_duplicate_same_parent_ignored(
        self, db, create_user, create_product, create_serial,
        create_work_order, seed_config
    ):
        """New territory: Re-linking to the same parent is a no-op.

        Given an existing confirmed contains edge from parent to child
        When SerialLinkedEvent is saved with the same parent/child
        Then the event completes with 'Link already exists' and no new edge
        """
        user = create_user()
        prod = create_product(traceability_level="complete")
        parent = create_serial(product_key=prod["product_key"], code="SN-P-DUP")
        child = create_serial(product_key=prod["product_key"], code="SN-C-DUP")
        wo = create_work_order(product_key=prod["product_key"], traceability_level="serial")
        # Pre-create the link
        db.collection("contains").insert({
            "_from": f"Serial/{parent['_key']}",
            "_to": f"Serial/{child['_key']}",
            "confirmed": True,
            "replaced": False,
        })
        seed_config("enable_inventory_management", value=False)
        event = SerialLinkedEvent(info=_make_info(
            user["_key"], child["_key"],
            parent_serial_key=parent["_key"],
            wo_key=wo["_key"],
        ))
        event.save()
        assert "already exists" in event.response["message"]
        # Verify no duplicate edge was created
        edges = list(db.collection("contains").find({
            "_from": f"Serial/{parent['_key']}",
            "_to": f"Serial/{child['_key']}",
        }))
        assert len(edges) == 1

    def test_link_to_different_parent_without_replace_raises(
        self, db, create_user, create_product, create_serial,
        create_work_order, seed_config
    ):
        """New territory: Linking to a different parent without replace raises error.

        Given an existing contains edge from parent_A to child
        When SerialLinkedEvent is saved with parent_B and replace_existing=None
        Then SerialNotLinkedError is raised
        """
        user = create_user()
        prod = create_product(traceability_level="complete")
        parent_a = create_serial(product_key=prod["product_key"], code="SN-PA")
        parent_b = create_serial(product_key=prod["product_key"], code="SN-PB")
        child = create_serial(product_key=prod["product_key"], code="SN-C-DIFF")
        wo = create_work_order(product_key=prod["product_key"], traceability_level="serial")
        db.collection("contains").insert({
            "_from": f"Serial/{parent_a['_key']}",
            "_to": f"Serial/{child['_key']}",
            "confirmed": True,
            "replaced": False,
        })
        seed_config("enable_inventory_management", value=False)
        event = SerialLinkedEvent(info=_make_info(
            user["_key"], child["_key"],
            parent_serial_key=parent_b["_key"],
            wo_key=wo["_key"],
        ))
        with pytest.raises(SerialNotLinkedError):
            event.save()

    def test_link_to_different_parent_with_replace(
        self, db, create_user, create_product, create_serial,
        create_work_order, seed_config
    ):
        """New territory: Replacing an existing parent link creates new contains edge.

        Given an existing contains edge from parent_A to child
        When SerialLinkedEvent is saved with parent_B and replace_existing=True
        Then a new contains edge exists from parent_B to child with confirmed=True
        """
        user = create_user()
        prod = create_product(traceability_level="complete")
        parent_a = create_serial(product_key=prod["product_key"], code="SN-PA-REP")
        parent_b = create_serial(product_key=prod["product_key"], code="SN-PB-REP")
        child = create_serial(product_key=prod["product_key"], code="SN-C-REP")
        wo = create_work_order(product_key=prod["product_key"], traceability_level="serial")
        db.collection("contains").insert({
            "_from": f"Serial/{parent_a['_key']}",
            "_to": f"Serial/{child['_key']}",
            "confirmed": True,
            "replaced": False,
        })
        seed_config("enable_inventory_management", value=False)
        event = SerialLinkedEvent(info=_make_info(
            user["_key"], child["_key"],
            parent_serial_key=parent_b["_key"],
            wo_key=wo["_key"],
            replace_existing=True,
        ))
        event.save()
        new_edges = list(db.collection("contains").find({
            "_from": f"Serial/{parent_b['_key']}",
            "_to": f"Serial/{child['_key']}",
        }))
        assert len(new_edges) == 1
        assert new_edges[0]["confirmed"] is True

    def test_link_requires_parent_for_traceable_wo(
        self, db, create_user, create_product, create_serial,
        create_work_order, create_batch, create_job, seed_config
    ):
        """New territory: Traceable WO requires parent_serial_key, not just batch_key.

        Given a WorkOrder with traceability_level='serial'
        When SerialLinkedEvent is saved with parent_serial_key=None and batch_key set
        Then SerialNotLinkedError is raised
        """
        user = create_user()
        prod = create_product(traceability_level="complete")
        child = create_serial(product_key=prod["product_key"], code="SN-NO-PARENT")
        wo = create_work_order(product_key=prod["product_key"], traceability_level="serial")
        job = create_job(wo_key=wo["_key"], phase_key=prod["phases"][0]["_key"])
        batch = create_batch(job_key=job["_key"], work_order_key=wo["_key"])
        seed_config("enable_inventory_management", value=False)
        event = SerialLinkedEvent(info=_make_info(
            user["_key"], child["_key"],
            batch_key=batch["_key"],
            wo_key=wo["_key"],
        ))
        with pytest.raises(SerialNotLinkedError):
            event.save()
