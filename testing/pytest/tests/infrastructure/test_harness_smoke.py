"""
Feature: Test Infrastructure
  The pytest harness can spin up ArangoDB, override singletons,
  mock NATS, serve the FastAPI app in-memory, and isolate tests.
"""
import pytest


class TestArangoDBContainer:
    """Scenario: ArangoDB testcontainer is running and accessible"""

    def test_container_reachable(self, db):
        """Given the arango_container fixture has started,
        when we query the server version,
        then it returns a version string starting with '3.11'"""
        version = db.version()
        assert version.startswith("3.11"), f"Expected ArangoDB 3.11, got {version}"

    def test_all_collections_exist(self, db):
        """Given schema initialization has run,
        when we list all collections,
        then all expected collections exist"""
        existing = {c["name"] for c in db.collections() if not c["system"]}
        # Verify a representative set of critical collections
        expected = {
            "Batch", "Job", "WorkOrder", "WorkSession", "Product",
            "Phase", "Operation", "Step", "StepExecutionData",
            "Serial", "Position", "User", "Config", "Counter",
            "Event", "Queue", "CustomField", "wip", "movement",
            "is_in_position", "requires", "batch_serial", "event_source",
        }
        missing = expected - existing
        assert not missing, f"Missing collections: {missing}"

    def test_config_defaults_exist(self, db):
        """Given schema initialization inserted default records,
        when we query Config collection,
        then enable_inventory_management and default_operation_parameters exist"""
        config_col = db.collection("Config")
        inv_mgmt = config_col.get("enable_inventory_management")
        assert inv_mgmt is not None, "Config 'enable_inventory_management' missing"
        assert inv_mgmt["value"] == False

        op_params = config_col.get("default_operation_parameters")
        assert op_params is not None, "Config 'default_operation_parameters' missing"
        assert op_params["step_check"] == False
        assert op_params["production_batch_qt"] == 1

    def test_counter_default_exists(self, db):
        """Given schema initialization inserted default records,
        when we query Counter collection,
        then the 'default' counter exists with next_tick=1"""
        counter = db.collection("Counter").get("default")
        assert counter is not None, "Counter 'default' missing"
        assert counter["next_tick"] == 1

    def test_queue_default_exists(self, db):
        """Given schema initialization inserted default records,
        when we query Queue collection,
        then the site queue default record exists"""
        queues = list(db.collection("Queue").all())
        assert len(queues) >= 1, "Queue default record missing"
        site_queue = [q for q in queues if q.get("type") == "s"]
        assert len(site_queue) == 1, "Site queue default record missing"


class TestDBSingletonOverride:
    """Scenario: The db singleton in utils.db points to the testcontainer"""

    def test_db_module_points_to_testcontainer(self, db):
        """Given the db fixture has overridden the singleton,
        when we import utils.db and check its db attribute,
        then it is the same object as the fixture's db"""
        import utils.db as db_module
        assert db_module.db is db, "utils.db.db does not point to testcontainer db"

    def test_auth_module_db_overridden(self, db):
        """Given the db fixture has overridden auth.db,
        when we import utils.auth and check its db attribute,
        then it is the same object as the fixture's db"""
        import utils.auth as auth_module
        assert auth_module.db is db, "utils.auth.db does not point to testcontainer db"


class TestNATSMock:
    """Scenario: NATS publish_sync is mocked and does not raise"""

    def test_publish_sync_noop(self):
        """Given the mock_nats fixture has replaced publish_sync,
        when we call publish_sync from the source module,
        then it does not raise"""
        import utils.nats_client as nats_module
        # Should not raise RuntimeError("NATS client not connected")
        nats_module.publish_sync("test.subject", b"test-data")

    def test_publish_sync_mocked_in_base_event(self):
        """Given the mock_nats fixture has patched base_event's local binding,
        when we access publish_sync from events.base_event,
        then it is the noop function (not the original)"""
        import events.base_event as mod
        # Calling should not raise
        mod.publish_sync("test.subject", b"data")


class TestHTTPClient:
    """Scenario: httpx AsyncClient can reach the FastAPI app"""

    async def test_hello_endpoint(self, client):
        """Given the ASGI client is connected to the FastAPI app,
        when we GET /hello,
        then we receive 200 with 'Hi!'
        Note: root_path='/api' only affects OpenAPI docs routing, not actual route paths."""
        response = await client.get("/hello")
        assert response.status_code == 200
        assert response.json() == "Hi!"


class TestCollectionIsolation:
    """Scenario: Collection truncation ensures test isolation"""

    def test_insert_then_truncation(self, db):
        """Given we insert a record into User collection,
        when this test completes (truncation runs in teardown),
        then the next test should see an empty User collection"""
        db.collection("User").insert({"_key": "isolation-test", "username": "test"})
        users = list(db.collection("User").all())
        assert any(u["_key"] == "isolation-test" for u in users)

    def test_previous_data_gone(self, db):
        """Given the previous test inserted a User record,
        when we query User collection,
        then the isolation-test record is gone (truncation ran)"""
        users = list(db.collection("User").all())
        assert not any(u.get("_key") == "isolation-test" for u in users), \
            "Truncation did not clear User collection"

    def test_config_survives_truncation(self, db):
        """Given Config is in SKIP_TRUNCATE,
        when truncation runs between tests,
        then Config default records are preserved"""
        config_col = db.collection("Config")
        inv_mgmt = config_col.get("enable_inventory_management")
        assert inv_mgmt is not None, "Config defaults were truncated!"
