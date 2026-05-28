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

    # ------------------------------------------------------------------
    # WOU-API-01 through WOU-API-08: Work Order update baseline tests
    # ------------------------------------------------------------------

    async def test_update_work_order_due_date(
        self, client, auth_headers, create_product
    ):
        """WOU-API-01: Given a work order exists
        When PATCH /work-order/{wo_key} is called with new_due_date
        Then response is 200 and detail.due_by reflects the new date.
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
            json={"new_due_date": "2026-12-31"},
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        detail = response.json().get("detail", {})
        due_by = detail.get("due_by", "")
        assert due_by and "2026-12-31" in due_by, (
            f"Expected due_by to contain '2026-12-31', got {due_by!r}"
        )

    async def test_update_work_order_project_code_propagates_to_jobs(
        self, client, auth_headers, create_product
    ):
        """WOU-API-02: Given a work order with jobs exists
        When PATCH /work-order/{wo_key} is called with new_project_code
        Then response is 200, WO project_code is updated, and every Job has the new project_code.
        """
        product_data = create_product(num_phases=1, steps_per_phase=1)
        auth_headers("operator production admin")

        create_resp = await client.post("/work-order", json={
            "product_key": product_data["product_key"],
            "qt_planned": 10,
        })
        assert create_resp.status_code == 200
        wo_data = create_resp.json()["detail"]
        wo_key = wo_data["work_order"]["_key"]
        job_keys = [j["_key"] for j in wo_data.get("jobs", [])]
        assert job_keys, "Expected at least one job from POST /work-order"

        response = await client.patch(
            f"/work-order/{wo_key}",
            json={"new_project_code": "PRJ-X"},
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        detail = response.json().get("detail", {})
        assert detail.get("project_code") == "PRJ-X", (
            f"Expected project_code='PRJ-X', got {detail.get('project_code')!r}"
        )

        for job_key in job_keys:
            job_resp = await client.get(f"/job/{job_key}")
            assert job_resp.status_code == 200, (
                f"GET /job/{job_key} returned {job_resp.status_code}"
            )
            job_detail = job_resp.json().get("detail", {})
            assert job_detail.get("project_code") == "PRJ-X", (
                f"Job {job_key}: expected project_code='PRJ-X', got {job_detail.get('project_code')!r}"
            )

    async def test_update_work_order_from_date_propagates_to_jobs(
        self, client, auth_headers, create_product
    ):
        """WOU-API-03: Given a work order with jobs exists
        When PATCH /work-order/{wo_key} is called with new_from_date
        Then response is 200, WO start_from is updated, and every Job has the new start_from.
        """
        product_data = create_product(num_phases=1, steps_per_phase=1)
        auth_headers("operator production admin")

        create_resp = await client.post("/work-order", json={
            "product_key": product_data["product_key"],
            "qt_planned": 10,
        })
        assert create_resp.status_code == 200
        wo_data = create_resp.json()["detail"]
        wo_key = wo_data["work_order"]["_key"]
        job_keys = [j["_key"] for j in wo_data.get("jobs", [])]
        assert job_keys, "Expected at least one job from POST /work-order"

        response = await client.patch(
            f"/work-order/{wo_key}",
            json={"new_from_date": "2026-06-01"},
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        detail = response.json().get("detail", {})
        start_from = detail.get("start_from", "")
        assert start_from and "2026-06-01" in start_from, (
            f"Expected start_from to contain '2026-06-01', got {start_from!r}"
        )

        for job_key in job_keys:
            job_resp = await client.get(f"/job/{job_key}")
            assert job_resp.status_code == 200
            job_detail = job_resp.json().get("detail", {})
            job_start = job_detail.get("start_from", "")
            assert job_start and "2026-06-01" in job_start, (
                f"Job {job_key}: expected start_from to contain '2026-06-01', got {job_start!r}"
            )

    async def test_update_work_order_project_and_from_date_combined(
        self, client, auth_headers, create_product
    ):
        """WOU-API-04: Given a work order with jobs exists
        When PATCH /work-order/{wo_key} is called with both new_project_code and new_from_date
        Then both fields are reflected on the WO and every Job.
        """
        product_data = create_product(num_phases=1, steps_per_phase=1)
        auth_headers("operator production admin")

        create_resp = await client.post("/work-order", json={
            "product_key": product_data["product_key"],
            "qt_planned": 10,
        })
        assert create_resp.status_code == 200
        wo_data = create_resp.json()["detail"]
        wo_key = wo_data["work_order"]["_key"]
        job_keys = [j["_key"] for j in wo_data.get("jobs", [])]

        response = await client.patch(
            f"/work-order/{wo_key}",
            json={"new_project_code": "PRJ-COMBINED", "new_from_date": "2026-07-01"},
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        detail = response.json().get("detail", {})
        assert detail.get("project_code") == "PRJ-COMBINED", (
            f"Expected project_code='PRJ-COMBINED', got {detail.get('project_code')!r}"
        )
        start_from = detail.get("start_from", "")
        assert start_from and "2026-07-01" in start_from, (
            f"Expected start_from to contain '2026-07-01', got {start_from!r}"
        )

        for job_key in job_keys:
            job_resp = await client.get(f"/job/{job_key}")
            assert job_resp.status_code == 200
            job_detail = job_resp.json().get("detail", {})
            assert job_detail.get("project_code") == "PRJ-COMBINED", (
                f"Job {job_key}: expected project_code='PRJ-COMBINED', got {job_detail.get('project_code')!r}"
            )
            job_start = job_detail.get("start_from", "")
            assert job_start and "2026-07-01" in job_start, (
                f"Job {job_key}: expected start_from to contain '2026-07-01', got {job_start!r}"
            )

    async def test_update_work_order_bom(
        self, client, auth_headers, create_product
    ):
        """WOU-API-05: Given a work order exists
        When PATCH /work-order/{wo_key} is called with new_bom
        Then response is 200 and detail.wo_bom matches (jobs untouched).
        """
        product_data = create_product(num_phases=1, steps_per_phase=1)
        auth_headers("operator production admin")

        create_resp = await client.post("/work-order", json={
            "product_key": product_data["product_key"],
            "qt_planned": 10,
        })
        assert create_resp.status_code == 200
        wo_key = create_resp.json()["detail"]["work_order"]["_key"]

        bom_payload = [
            {
                "component_key": "comp-001",
                "component_code": "COMP-001",
                "component_description": "Test component",
                "qt": 2.0,
            }
        ]
        response = await client.patch(
            f"/work-order/{wo_key}",
            json={"new_bom": bom_payload},
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        detail = response.json().get("detail", {})
        wo_bom = detail.get("wo_bom", [])
        assert len(wo_bom) == 1, f"Expected 1 BOM line, got {len(wo_bom)}"
        assert wo_bom[0].get("component_key") == "comp-001", (
            f"Expected component_key='comp-001', got {wo_bom[0].get('component_key')!r}"
        )

    async def test_update_work_order_output_position_key(
        self, client, auth_headers, create_product
    ):
        """WOU-API-06: Given a work order exists
        When PATCH /work-order/{wo_key} is called with new_output_position_key
        Then response is 200 and detail.output_position_key matches.
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
            json={"new_output_position_key": "POS-1"},
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        detail = response.json().get("detail", {})
        assert detail.get("output_position_key") == "POS-1", (
            f"Expected output_position_key='POS-1', got {detail.get('output_position_key')!r}"
        )

    async def test_update_work_order_multiple_fields_atomic(
        self, client, auth_headers, create_product
    ):
        """WOU-API-07: Given a work order with jobs exists
        When PATCH /work-order/{wo_key} is called with new_due_date + new_project_code + notes
        Then response is 200, all three fields reflected on WO, jobs see project_code update.
        """
        product_data = create_product(num_phases=1, steps_per_phase=1)
        auth_headers("operator production admin")

        create_resp = await client.post("/work-order", json={
            "product_key": product_data["product_key"],
            "qt_planned": 10,
        })
        assert create_resp.status_code == 200
        wo_data = create_resp.json()["detail"]
        wo_key = wo_data["work_order"]["_key"]
        job_keys = [j["_key"] for j in wo_data.get("jobs", [])]

        response = await client.patch(
            f"/work-order/{wo_key}",
            json={
                "new_due_date": "2026-11-30",
                "new_project_code": "PRJ-MULTI",
                "notes": "multi-field atomic update",
            },
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        detail = response.json().get("detail", {})
        due_by = detail.get("due_by", "")
        assert due_by and "2026-11-30" in due_by, (
            f"Expected due_by to contain '2026-11-30', got {due_by!r}"
        )
        assert detail.get("project_code") == "PRJ-MULTI", (
            f"Expected project_code='PRJ-MULTI', got {detail.get('project_code')!r}"
        )
        assert detail.get("notes") == "multi-field atomic update", (
            f"Expected notes='multi-field atomic update', got {detail.get('notes')!r}"
        )

        for job_key in job_keys:
            job_resp = await client.get(f"/job/{job_key}")
            assert job_resp.status_code == 200
            job_detail = job_resp.json().get("detail", {})
            assert job_detail.get("project_code") == "PRJ-MULTI", (
                f"Job {job_key}: expected project_code='PRJ-MULTI', got {job_detail.get('project_code')!r}"
            )

    async def test_update_work_order_emits_event(
        self, db, client, auth_headers, create_product
    ):
        """WOU-API-08 (EXPECTED TO FAIL in RED phase): Given a work order exists
        When PATCH /work-order/{wo_key} is called with any field
        Then an Event record with event_type=WORK_ORDER_UPDATED is stored in the Event collection.
        This test fails in Phase 1 (direct-transaction endpoint) and passes after Phase 2 refactor.
        """
        from tests.helpers import assert_event_dispatched

        product_data = create_product(num_phases=1, steps_per_phase=1)
        auth_headers("operator production admin")

        create_resp = await client.post("/work-order", json={
            "product_key": product_data["product_key"],
            "qt_planned": 10,
        })
        assert create_resp.status_code == 200
        wo_key = create_resp.json()["detail"]["work_order"]["_key"]

        patch_resp = await client.patch(
            f"/work-order/{wo_key}",
            json={"notes": "event emission test"},
        )
        assert patch_resp.status_code == 200, (
            f"Expected 200, got {patch_resp.status_code}: {patch_resp.text}"
        )

        assert_event_dispatched(db, "WORK_ORDER_UPDATED", work_order_key=wo_key)

    async def test_update_nonexistent_work_order_returns_422(
        self, client, auth_headers
    ):
        """WOU-API-09: Given a wo_key that does not exist
        When PATCH /work-order/{wo_key} is called
        Then response is 422 (ValueError from wo_key existence check maps to 422).
        """
        import uuid
        auth_headers("operator production admin")

        response = await client.patch(
            f"/work-order/does-not-exist-{uuid.uuid4()}",
            json={"notes": "should fail"},
        )

        assert response.status_code == 422, (
            f"Expected 422 for nonexistent wo_key, got {response.status_code}: {response.text}"
        )

    async def test_post_event_work_order_updated(
        self, db, client, auth_headers, create_product
    ):
        """WOU-API-10: Given a work order exists
        When POST /event with event_type=WORK_ORDER_UPDATED is called
        Then response is 200 and the WO document reflects the update.
        Verifies the bonus POST /event path exercises the same WorkOrderUpdatedEvent.apply().
        """
        product_data = create_product(num_phases=1, steps_per_phase=1)
        auth_headers("operator production admin")

        create_resp = await client.post("/work-order", json={
            "product_key": product_data["product_key"],
            "qt_planned": 10,
        })
        assert create_resp.status_code == 200
        wo_key = create_resp.json()["detail"]["work_order"]["_key"]

        event_resp = await client.post("/event", json={
            "event_type": "WORK_ORDER_UPDATED",
            "primary": True,
            "work_order_key": wo_key,
            "new_project_code": "PRJ-Y",
        })

        assert event_resp.status_code == 200, (
            f"Expected 200, got {event_resp.status_code}: {event_resp.text}"
        )

        wo_resp = await client.get(f"/work-order/{wo_key}")
        assert wo_resp.status_code == 200
        wo_detail = wo_resp.json().get("detail", {})
        assert wo_detail.get("project_code") == "PRJ-Y", (
            f"Expected project_code='PRJ-Y' after POST /event, got {wo_detail.get('project_code')!r}"
        )
