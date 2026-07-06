"""
Feature: create_temporary_link endpoint — PUT /batch/{batch_key}/serial-temp-links
  Covers the batch component temp-link normalization contract.

  `parent_serial_key` accepts the batch-level sentinel "components" (or None) to
  mean "link the component to the batch, not to a parent serial". The endpoint must:
    - REJECT a MIXED payload (real parent serials + the sentinel together) with 422.
      That ambiguity previously persisted a component under a phantom
      `Serial/components` edge — orphaned genealogy. See
      km/domains/production/serial-management.md ("components" sentinel gotcha).
    - rewrite a homogeneous all-sentinel payload to `Batch/<batch_key>`;
    - leave real parent-serial links pointing at `Serial/<parent>`.

  Per D-03: httpx.AsyncClient with the auth_headers fixture.
  This endpoint has no event class — the persisted `contains` edge IS its
  contract — so tests assert on edge shape (like test_serial_linked.py), not
  only HTTP status. `contains` is truncated between tests (autouse fixture).
"""
import pytest


def _link(child_serial_key, parent_serial_key, batch_key, **overrides):
    """One SerialLink request dict using model FIELD NAMES (populate_by_name),
    mirroring exactly what the frontend `saveSerialLinks` sends."""
    return {
        "child_serial_key": child_serial_key,
        "parent_serial_key": parent_serial_key,
        "batch_key": batch_key,
        "confirmed": False,
        **overrides,
    }


def _setup_batch(create_product, create_work_order, create_job, create_batch):
    """Minimal traceable product → WO → job → batch chain (endpoint only needs the Batch)."""
    prod = create_product(traceability_level="serial")
    phase_key = prod["phases"][0]["_key"]
    wo = create_work_order(product_key=prod["product_key"], traceability_level="serial")
    job = create_job(wo_key=wo["_key"], phase_key=phase_key)
    batch = create_batch(job_key=job["_key"], work_order_key=wo["_key"], phase_key=phase_key)
    return prod, batch, phase_key


class TestCreateTemporaryLink:
    """HTTP tests for PUT /batch/{batch_key}/serial-temp-links."""

    async def test_mixed_parents_returns_422(
        self, db, client, auth_headers,
        create_product, create_work_order, create_job, create_batch, create_serial,
    ):
        """Mixed payload (one real parent serial + one `components` sentinel) → 422,
        and nothing is persisted (the check runs before delete+insert)."""
        prod, batch, _ = _setup_batch(create_product, create_work_order, create_job, create_batch)
        parent = create_serial(product_key=prod["product_key"], code="SN-PARENT")
        child_a = create_serial(product_key=prod["product_key"], code="SN-CHILD-A")
        child_b = create_serial(product_key=prod["product_key"], code="SN-CHILD-B")
        auth_headers()

        payload = [
            _link(child_a["_key"], parent["_key"], batch["_key"]),   # real parent serial
            _link(child_b["_key"], "components", batch["_key"]),     # batch-level sentinel
        ]

        response = await client.put(f"/batch/{batch['_key']}/serial-temp-links", json=payload)

        assert response.status_code == 422, (
            f"Expected 422 for mixed parent links, got {response.status_code}: {response.text}"
        )
        # Distinguish OUR 422 from a generic pydantic validation 422
        assert "mixed parent links" in str(response.json().get("detail", "")).lower()
        # Nothing should have been persisted — the mixed-set check precedes delete_match
        edges = list(db.collection("contains").find({"batch_key": batch["_key"]}))
        assert edges == [], f"Mixed payload must persist no links, found: {edges}"

    async def test_all_sentinel_links_to_batch(
        self, db, client, auth_headers,
        create_product, create_work_order, create_job, create_batch, create_serial,
    ):
        """Homogeneous all-`components` payload → every link rewritten to `Batch/<batch_key>`
        (the legitimate non-traceable-output path), never `Serial/components`."""
        prod, batch, _ = _setup_batch(create_product, create_work_order, create_job, create_batch)
        child_a = create_serial(product_key=prod["product_key"], code="SN-BC-A")
        child_b = create_serial(product_key=prod["product_key"], code="SN-BC-B")
        auth_headers()

        payload = [
            _link(child_a["_key"], "components", batch["_key"]),
            _link(child_b["_key"], "components", batch["_key"]),
        ]

        response = await client.put(f"/batch/{batch['_key']}/serial-temp-links", json=payload)

        assert response.status_code == 200, (
            f"Expected 200 for all-sentinel payload, got {response.status_code}: {response.text}"
        )
        edges = list(db.collection("contains").find({"batch_key": batch["_key"]}))
        assert len(edges) == 2, f"Expected 2 links, got {edges}"
        expected_children = {f"Serial/{child_a['_key']}", f"Serial/{child_b['_key']}"}
        for edge in edges:
            assert edge["_from"] == f"Batch/{batch['_key']}", (
                f"Sentinel must normalize to the batch, got _from={edge['_from']}"
            )
            assert edge["_to"] in expected_children

    async def test_all_real_parents_links_to_parent_serial(
        self, db, client, auth_headers,
        create_product, create_work_order, create_job, create_batch, create_serial,
    ):
        """Homogeneous real-parent payload → link points at `Serial/<parent>`
        (the normal traceable path is unaffected by the new check)."""
        prod, batch, _ = _setup_batch(create_product, create_work_order, create_job, create_batch)
        parent = create_serial(product_key=prod["product_key"], code="SN-RP-PARENT")
        child = create_serial(product_key=prod["product_key"], code="SN-RP-CHILD")
        auth_headers()

        payload = [_link(child["_key"], parent["_key"], batch["_key"])]

        response = await client.put(f"/batch/{batch['_key']}/serial-temp-links", json=payload)

        assert response.status_code == 200, (
            f"Expected 200 for real-parent payload, got {response.status_code}: {response.text}"
        )
        edges = list(db.collection("contains").find({"batch_key": batch["_key"]}))
        assert len(edges) == 1, f"Expected 1 link, got {edges}"
        assert edges[0]["_from"] == f"Serial/{parent['_key']}"
        assert edges[0]["_to"] == f"Serial/{child['_key']}"
