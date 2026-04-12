"""
Feature: Work Order CRUD via HTTP API
  Tests covering create, read, update, and delete of work orders.
  Migrated from Robot Framework WorkOrderAPI and production.resource keywords.

  Per D-03: HTTP API layer only — no direct event instantiation.
  Per D-05: Uses authed_client fixture pattern from Phase 5.
"""
import pytest


class TestWorkOrderCRUD:
    """HTTP API tests for Work Order CRUD operations.

    Per D-04: Each test creates its own preconditions via factories.
    All tests call auth_headers() to set up the dependency override before requests.
    """

    async def test_create_work_order_returns_work_order_and_jobs(
        self, client, auth_headers, create_product
    ):
        """Given a product exists
        When a work order is created via POST /work-order
        Then the response contains work_order with _key and a jobs list.
        Migrated from: production.resource Create work order keyword.
        """
        product_data = create_product(num_phases=1, steps_per_phase=1)
        auth_headers("operator production admin")

        payload = {
            "product_key": product_data["product_key"],
            "qt_planned": 10,
        }
        response = await client.post("/work-order", json=payload)

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        detail = response.json().get("detail", {})
        assert "work_order" in detail, (
            f"Expected 'work_order' in detail, got keys: {list(detail.keys())}"
        )
        wo = detail["work_order"]
        assert "_key" in wo, "work_order missing _key"
        assert "jobs" in detail, "Response missing 'jobs' list"
        assert len(detail["jobs"]) >= 1, "Expected at least one job"

    async def test_create_work_order_duplicate_code_returns_409(
        self, client, auth_headers, create_product
    ):
        """Given a product exists
        When two work orders are created with the same wo_code
        Then the first returns 200 and the second returns 409.
        Migrated from: production.resource duplicate work order guard.
        """
        product_data = create_product(num_phases=1, steps_per_phase=1)
        auth_headers("operator production admin")

        payload = {
            "wo_code": "WO-DUP-TEST",
            "product_key": product_data["product_key"],
            "qt_planned": 10,
        }
        first = await client.post("/work-order", json=payload)
        assert first.status_code == 200, (
            f"First create failed: {first.status_code}: {first.text}"
        )

        second = await client.post("/work-order", json=payload)
        assert second.status_code == 409, (
            f"Expected 409 for duplicate wo_code, got {second.status_code}: {second.text}"
        )

    async def test_get_work_order_returns_details(
        self, client, auth_headers, create_product
    ):
        """Given a work order has been created
        When GET /work-order/{wo_key} is called
        Then the response contains the work order data with matching _key.
        Migrated from: production.resource work order read flow.
        """
        product_data = create_product(num_phases=1, steps_per_phase=1)
        auth_headers("operator production admin")

        create_resp = await client.post("/work-order", json={
            "product_key": product_data["product_key"],
            "qt_planned": 10,
        })
        assert create_resp.status_code == 200
        wo_key = create_resp.json()["detail"]["work_order"]["_key"]

        response = await client.get(f"/work-order/{wo_key}")

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        detail = response.json().get("detail", {})
        assert detail.get("_key") == wo_key, (
            f"Expected _key={wo_key}, got {detail.get('_key')}"
        )

    async def test_update_work_order_notes(
        self, client, auth_headers, create_product
    ):
        """Given a work order exists
        When PATCH /work-order/{wo_key} is called with notes
        Then the response contains the updated notes value.
        """
        product_data = create_product(num_phases=1, steps_per_phase=1)
        auth_headers("operator production admin")

        create_resp = await client.post("/work-order", json={
            "product_key": product_data["product_key"],
            "qt_planned": 10,
        })
        assert create_resp.status_code == 200
        wo_key = create_resp.json()["detail"]["work_order"]["_key"]

        response = await client.patch(
            f"/work-order/{wo_key}",
            json={"notes": "updated notes"},
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        detail = response.json().get("detail", {})
        assert detail.get("notes") == "updated notes", (
            f"Expected notes='updated notes', got {detail.get('notes')}"
        )

    async def test_delete_work_order_in_created_status(
        self, client, auth_headers, create_product
    ):
        """Given a work order in 'created' status
        When DELETE /work-order/{wo_key} is called
        Then it returns 200 and the work order is no longer accessible.
        Migrated from: production.resource Delete work order teardown keyword.
        """
        product_data = create_product(num_phases=1, steps_per_phase=1)
        auth_headers("operator production admin")

        create_resp = await client.post("/work-order", json={
            "product_key": product_data["product_key"],
            "qt_planned": 10,
        })
        assert create_resp.status_code == 200
        wo_key = create_resp.json()["detail"]["work_order"]["_key"]

        response = await client.delete(f"/work-order/{wo_key}")

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )

        # Verify the work order no longer exists
        get_resp = await client.get(f"/work-order/{wo_key}")
        assert get_resp.status_code in (404, 500), (
            f"Expected 404 or 500 after deletion, got {get_resp.status_code}"
        )

    async def test_delete_started_work_order_returns_403(
        self, db, client, auth_headers, create_product
    ):
        """Given a work order whose status is 'started'
        When DELETE /work-order/{wo_key} is called
        Then it returns 403 because started work orders cannot be deleted.
        """
        product_data = create_product(num_phases=1, steps_per_phase=1)
        auth_headers("operator production admin")

        create_resp = await client.post("/work-order", json={
            "product_key": product_data["product_key"],
            "qt_planned": 10,
        })
        assert create_resp.status_code == 200
        wo_key = create_resp.json()["detail"]["work_order"]["_key"]

        # Simulate the work order having been started by updating status directly
        db.collection("WorkOrder").update({"_key": wo_key, "status": "started"})

        response = await client.delete(f"/work-order/{wo_key}")

        assert response.status_code == 403, (
            f"Expected 403 for started work order, got {response.status_code}: {response.text}"
        )
