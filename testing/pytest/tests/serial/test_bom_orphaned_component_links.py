"""
Feature: BOM completion is blind to component links parented to defunct output serials.

  When a batch's output serial is regenerated in place (qty change, wip re-book),
  the old temporary `contains` edges keep the same `batch_key` but point at a
  parent serial no longer produced by the batch. Two regressions follow:

    1. GET_WORKING_JOB_DATA (`utils/production.py`) counted those orphans toward
       `declared_serials` — parent-agnostic — so the BOM line showed complete
       while the serial dialog (parent-specific) showed nothing. The count is now
       parent-aware: only links to a current batch output serial, or the
       batch-level sentinel (`Batch/<key>`, non-traceable output), count.

    2. PRUNE_ORPHANED_COMPONENT_LINKS (`utils/serial.py`) is the shared cleanup
       run wherever a batch's output serials change (active_batch_changed,
       wip_booked, batch_canceled) to stop the orphans accumulating.

  See km/domains/production/serial-management.md ("regenerated output serial"
  genealogy-corruption mode).
"""
import pytest

from utils.production import Queries as ProductionQueries
from utils.serial import Queries as SerialQueries


def _setup_orphan_scenario(
    db, create_product, create_work_order, create_job, create_batch, create_serial,
    output_traceable=True,
):
    """Traceable batch with a CURRENT output serial S2 and a DEFUNCT one S1.

    Component links:
      - child C_valid  -> parent S2 (current output serial)   [should count]
      - child C_orphan -> parent S1 (no batch_serial edge)     [must NOT count]

    Returns keys needed by the assertions.
    """
    output = create_product(num_phases=1, traceability_level="serial")
    phase_key = output["phases"][0]["_key"]
    component = create_product(num_phases=1)  # component product must exist (manage_inventory lookup)

    wo_bom_line = {
        "component_key": component["product_key"],
        "component_code": "COMP-1",
        "component_description": "Component 1",
        "phase_key": phase_key,
        "traceability_level": "serial",
        "qt": 1,
    }
    wo = create_work_order(product_key=output["product_key"], wo_bom=[wo_bom_line])

    job = create_job(
        wo_key=wo["_key"],
        phase_key=phase_key,
        product_key=output["product_key"],
        traceability_level="serial",
    )
    batch = create_batch(
        job_key=job["_key"], work_order_key=wo["_key"], phase_key=phase_key,
        qt_total=1.0, active=True,
    )
    db.collection("Job").update({
        "_key": job["_key"], "active_batch_key": batch["_key"], "active_batch_qt": 1,
    })

    # Current output serial S2 — linked to the batch via batch_serial.
    s2 = create_serial(product_key=output["product_key"], wo_key=wo["_key"])
    db.collection("batch_serial").insert({"_from": f"Batch/{batch['_key']}", "_to": f"Serial/{s2['_key']}"})

    # Defunct output serial S1 — exists, but NO batch_serial edge (regenerated away).
    s1 = create_serial(product_key=output["product_key"], wo_key=wo["_key"])

    c_valid = create_serial(product_key=component["product_key"], code="C-VALID")
    c_orphan = create_serial(product_key=component["product_key"], code="C-ORPHAN")

    def _contains(parent_from, child_key):
        return {
            "_from": parent_from,
            "_to": f"Serial/{child_key}",
            "component_key": component["product_key"],
            "phase_key": phase_key,
            "batch_key": batch["_key"],
            "confirmed": False,
            "replaced": False,
        }

    db.collection("contains").insert(_contains(f"Serial/{s2['_key']}", c_valid["_key"]))     # valid
    db.collection("contains").insert(_contains(f"Serial/{s1['_key']}", c_orphan["_key"]))    # orphan

    return {
        "job_key": job["_key"], "batch_key": batch["_key"],
        "s1": s1["_key"], "s2": s2["_key"],
        "c_valid": c_valid["_key"], "c_orphan": c_orphan["_key"],
    }


class TestDeclaredSerialsParentAware:
    """GET_WORKING_JOB_DATA must not count links parented to defunct output serials."""

    def test_orphaned_link_is_not_counted(
        self, db, create_product, create_work_order, create_job, create_batch, create_serial,
    ):
        ctx = _setup_orphan_scenario(
            db, create_product, create_work_order, create_job, create_batch, create_serial,
        )

        job_data = db.aql.execute(
            ProductionQueries.GET_WORKING_JOB_DATA, bind_vars={"job_key": ctx["job_key"]}
        ).next()

        declared = job_data["wo_bom"][0]["declared_serials"]
        declared_children = {d["_key"] for d in declared}

        # Only the link to the current output serial counts — orphan excluded.
        assert declared_children == {ctx["c_valid"]}, declared
        assert ctx["c_orphan"] not in declared_children

    def test_batch_level_sentinel_still_counts(
        self, db, create_product, create_work_order, create_job, create_batch, create_serial,
    ):
        """Non-traceable output links components to `Batch/<key>` — those must still count."""
        ctx = _setup_orphan_scenario(
            db, create_product, create_work_order, create_job, create_batch, create_serial,
        )
        # Add a batch-level sentinel link (its own child); it must be counted.
        sentinel_child = create_serial(product_key="COMP-anything", code="C-SENTINEL")
        db.collection("contains").insert({
            "_from": f"Batch/{ctx['batch_key']}",
            "_to": f"Serial/{sentinel_child['_key']}",
            # component_key/phase must match the bom line to be counted
            "component_key": db.aql.execute(
                ProductionQueries.GET_WORKING_JOB_DATA, bind_vars={"job_key": ctx["job_key"]}
            ).next()["wo_bom"][0]["component_key"],
            "phase_key": db.collection("Job").get(ctx["job_key"])["phase_key"],
            "batch_key": ctx["batch_key"],
            "confirmed": False,
            "replaced": False,
        })

        job_data = db.aql.execute(
            ProductionQueries.GET_WORKING_JOB_DATA, bind_vars={"job_key": ctx["job_key"]}
        ).next()
        declared_children = {d["_key"] for d in job_data["wo_bom"][0]["declared_serials"]}

        assert ctx["c_valid"] in declared_children
        assert sentinel_child["_key"] in declared_children
        assert ctx["c_orphan"] not in declared_children


class TestPruneOrphanedComponentLinks:
    """PRUNE_ORPHANED_COMPONENT_LINKS removes the stale edges, keeps the live ones."""

    def test_prune_removes_only_orphans(
        self, db, create_product, create_work_order, create_job, create_batch, create_serial,
    ):
        ctx = _setup_orphan_scenario(
            db, create_product, create_work_order, create_job, create_batch, create_serial,
        )

        before = db.aql.execute(
            "FOR c IN contains FILTER c.batch_key == @b RETURN c._key",
            bind_vars={"b": ctx["batch_key"]},
        )
        assert len(list(before)) == 2

        db.aql.execute(
            SerialQueries.PRUNE_ORPHANED_COMPONENT_LINKS, bind_vars={"batch_key": ctx["batch_key"]}
        )

        remaining = list(db.aql.execute(
            "FOR c IN contains FILTER c.batch_key == @b RETURN PARSE_IDENTIFIER(c._to).key",
            bind_vars={"b": ctx["batch_key"]},
        ))
        # Orphan gone, valid link kept.
        assert remaining == [ctx["c_valid"]]

    def test_prune_keeps_confirmed_links(
        self, db, create_product, create_work_order, create_job, create_batch, create_serial,
    ):
        """A confirmed (committed) link to a defunct parent is genealogy of record —
        prune only touches unconfirmed temp links."""
        ctx = _setup_orphan_scenario(
            db, create_product, create_work_order, create_job, create_batch, create_serial,
        )
        confirmed_child = create_serial(product_key="COMP-x", code="C-CONFIRMED")
        db.collection("contains").insert({
            "_from": f"Serial/{ctx['s1']}",  # defunct parent
            "_to": f"Serial/{confirmed_child['_key']}",
            "component_key": "whatever",
            "phase_key": "whatever",
            "batch_key": ctx["batch_key"],
            "confirmed": True,
            "replaced": False,
        })

        db.aql.execute(
            SerialQueries.PRUNE_ORPHANED_COMPONENT_LINKS, bind_vars={"batch_key": ctx["batch_key"]}
        )

        children = set(db.aql.execute(
            "FOR c IN contains FILTER c.batch_key == @b RETURN PARSE_IDENTIFIER(c._to).key",
            bind_vars={"b": ctx["batch_key"]},
        ))
        assert confirmed_child["_key"] in children  # confirmed survives
        assert ctx["c_orphan"] not in children       # unconfirmed orphan pruned
