"""
Feature: Factory Infrastructure
  All factory fixtures produce valid domain documents that exist in ArangoDB
  and are correctly linked to each other.
"""


class TestCoreFactories:
    """Scenario: Individual factories produce valid documents"""

    def test_create_user(self, db, create_user):
        """Given the create_user factory,
        when creating a user with operator scope,
        then the User document exists in ArangoDB with correct fields"""
        user = create_user(scope="operator quality")
        stored = db.collection("User").get(user["_key"])
        assert stored is not None
        assert stored["scope"] == "operator quality"
        assert stored["active"] is True

    def test_create_product_with_phases(self, db, create_product):
        """Given the create_product factory,
        when creating a product with 2 phases and 3 steps each,
        then Product, Phase, Operation, Step documents exist"""
        data = create_product(num_phases=2, steps_per_phase=3)
        assert db.collection("Product").get(data["product_key"]) is not None
        assert len(data["phases"]) == 2
        assert len(data["operations"]) == 2
        assert len(data["steps"]) == 6

    def test_create_bom(self, db, create_product, create_bom):
        """Given two products,
        when creating a BOM link,
        then a 'requires' edge exists between them"""
        parent = create_product()
        component = create_product()
        edge = create_bom(parent["product_key"], component["product_key"], quantity=2.0)
        assert edge["_from"] == f"Product/{parent['product_key']}"
        assert edge["_to"] == f"Product/{component['product_key']}"
        assert edge["quantity"] == 2.0

    def test_create_work_order(self, db, create_product, create_work_order):
        """Given a product,
        when creating a work order,
        then the WorkOrder document exists with correct product link"""
        product = create_product()
        wo = create_work_order(product["product_key"], qt_planned=50)
        stored = db.collection("WorkOrder").get(wo["_key"])
        assert stored is not None
        assert stored["product_key"] == product["product_key"]
        assert stored["qt_planned"] == 50

    def test_create_job(self, db, create_product, create_work_order, create_job):
        """Given a work order and phase,
        when creating a job,
        then the Job document exists with configurable parameters"""
        product = create_product()
        wo = create_work_order(product["product_key"])
        job = create_job(
            wo_key=wo["_key"],
            phase_key=product["phases"][0]["_key"],
            step_check=True,
            auto_new_batch=True,
        )
        stored = db.collection("Job").get(job["_key"])
        assert stored is not None
        assert stored["parameters"]["step_check"] is True
        assert stored["parameters"]["auto_new_batch"] is True
        assert stored["wo_key"] == wo["_key"]

    def test_create_batch(self, db, create_product, create_work_order, create_job, create_batch):
        """Given a job,
        when creating a batch,
        then the Batch document exists linked to the job"""
        product = create_product()
        wo = create_work_order(product["product_key"])
        job = create_job(wo_key=wo["_key"], phase_key=product["phases"][0]["_key"])
        batch = create_batch(job_key=job["_key"], qt_total=5)
        stored = db.collection("Batch").get(batch["_key"])
        assert stored is not None
        assert stored["job_key"] == job["_key"]
        assert stored["qt_total"] == 5

    def test_create_work_session(self, db, create_product, create_work_order, create_job, create_batch, create_work_session):
        """Given a batch,
        when creating a work session,
        then the WorkSession document exists linked to the batch"""
        product = create_product()
        wo = create_work_order(product["product_key"])
        job = create_job(wo_key=wo["_key"], phase_key=product["phases"][0]["_key"])
        batch = create_batch(job_key=job["_key"])
        ws = create_work_session(batch_key=batch["_key"], job_key=job["_key"])
        stored = db.collection("WorkSession").get(ws["_key"])
        assert stored is not None
        assert stored["batch_key"] == batch["_key"]

    def test_create_step_execution(self, db, create_product, create_work_order, create_job, create_batch, create_step_execution):
        """Given a batch and step,
        when creating step execution data,
        then the StepExecutionData document exists"""
        product = create_product(steps_per_phase=2)
        wo = create_work_order(product["product_key"])
        job = create_job(wo_key=wo["_key"], phase_key=product["phases"][0]["_key"])
        batch = create_batch(job_key=job["_key"])
        sxd = create_step_execution(batch_key=batch["_key"], step_key=product["steps"][0]["_key"])
        stored = db.collection("StepExecutionData").get(sxd["_key"])
        assert stored is not None
        assert stored["batch_key"] == batch["_key"]

    def test_seed_config_upsert(self, db, seed_config):
        """Given Config defaults from schema init,
        when seed_config overrides a value,
        then the Config document reflects the new value"""
        seed_config("enable_inventory_management", value=True)
        stored = db.collection("Config").get("enable_inventory_management")
        assert stored["value"] is True


class TestAdvancedFactories:
    """Scenario: Advanced factories produce valid documents"""

    def test_create_serial(self, db, create_product, create_serial):
        """Given a product,
        when creating a serial,
        then the Serial document exists linked to the product"""
        product = create_product()
        serial = create_serial(product_key=product["product_key"])
        stored = db.collection("Serial").get(serial["_key"])
        assert stored is not None
        assert stored["product_key"] == product["product_key"]
        assert stored["code"].startswith("SN-")

    def test_create_wip(self, db, create_product, create_work_order, create_wip):
        """Given two phases,
        when creating a WIP edge,
        then the wip document exists with correct from/to"""
        product = create_product(num_phases=2)
        wo = create_work_order(product["product_key"])
        wip = create_wip(
            from_phase_key=product["phases"][0]["_key"],
            to_phase_key=product["phases"][1]["_key"],
            wo_key=wo["_key"],
            quantity=5,
        )
        assert wip["_from"] == f"Phase/{product['phases'][0]['_key']}"
        assert wip["_to"] == f"Phase/{product['phases'][1]['_key']}"
        assert wip["quantity"] == 5
        # Verify document exists in DB
        stored = db.collection("wip").get(wip["_key"])
        assert stored is not None

    def test_create_position(self, db, create_position):
        """Given the position factory,
        when creating a custom position,
        then the Position document exists"""
        pos = create_position(code="SHELF-A1")
        stored = db.collection("Position").get(pos["_key"])
        assert stored is not None
        assert stored["code"] == "SHELF-A1"

    def test_create_queue(self, db, create_user, create_queue):
        """Given a user,
        when creating an operator queue,
        then the Queue document exists"""
        user = create_user()
        queue = create_queue(user_key=user["_key"])
        stored = db.collection("Queue").get(queue["_key"])
        assert stored is not None
        assert stored["type"] == "o"
        assert stored["subqueue_target_key"] == user["_key"]


class TestParametrizedBuilder:
    """Scenario: The production graph builder creates complete, linked object graphs"""

    def test_simple_graph(self, db, create_production_graph):
        """Given default flags (first_phase=True, last_phase=True),
        when creating a production graph,
        then all documents exist and are correctly linked"""
        g = create_production_graph()
        assert db.collection("User").get(g["user"]["_key"]) is not None
        assert db.collection("Product").get(g["product"]["product_key"]) is not None
        assert db.collection("WorkOrder").get(g["work_order"]["_key"]) is not None
        assert db.collection("Job").get(g["job"]["_key"]) is not None
        assert db.collection("Batch").get(g["batch"]["_key"]) is not None
        assert db.collection("WorkSession").get(g["work_session"]["_key"]) is not None

        # Verify linkage
        assert g["job"]["wo_key"] == g["work_order"]["_key"]
        assert g["batch"]["job_key"] == g["job"]["_key"]
        assert g["work_session"]["batch_key"] == g["batch"]["_key"]

    def test_non_first_phase_has_upstream_wip(self, db, create_production_graph):
        """Given first_phase=False,
        when creating a production graph,
        then an upstream phase and WIP edge exist"""
        g = create_production_graph(first_phase=False)
        assert len(g["wip_records"]) == 1
        assert g["target_phase_idx"] > 0
        # Verify WIP points to the target phase
        wip = g["wip_records"][0]
        assert wip["_to"] == f"Phase/{g['target_phase']['_key']}"

    def test_traceability_creates_serials(self, db, create_production_graph):
        """Given traceability_level='serial',
        when creating a production graph,
        then serial records are created"""
        g = create_production_graph(traceability_level="serial", batch_qt=3)
        assert len(g["serials"]) == 3
        for s in g["serials"]:
            assert db.collection("Serial").get(s["_key"]) is not None

    def test_warehouse_management_seeds_config(self, db, create_production_graph):
        """Given warehouse_management=True,
        when creating a production graph,
        then enable_inventory_management Config is set to True"""
        g = create_production_graph(warehouse_management=True)
        config = db.collection("Config").get("enable_inventory_management")
        assert config["value"] is True

    def test_with_bom_creates_component(self, db, create_production_graph):
        """Given with_bom=True,
        when creating a production graph,
        then a component product and BOM edge exist"""
        g = create_production_graph(with_bom=True)
        assert g["bom_data"] is not None
        assert g["bom_data"]["component_product"]["product_key"] is not None
        # Verify requires edge exists
        edges = list(db.collection("requires").all())
        assert len(edges) >= 1

    def test_step_check_flag_propagates(self, db, create_production_graph):
        """Given step_check=True,
        when creating a production graph,
        then the Job document has step_check=True"""
        g = create_production_graph(step_check=True)
        stored = db.collection("Job").get(g["job"]["_key"])
        assert stored["parameters"]["step_check"] is True
