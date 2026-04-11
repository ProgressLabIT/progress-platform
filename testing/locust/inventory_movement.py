"""Locust scenario: Inventory Movement queries.

Simulates a warehouse operator checking inventory positions,
movement journal, and inventory quantity summary.

Run headless:
    locust -f testing/locust/inventory_movement.py --headless -u 10 -r 2 --run-time 30s --host http://localhost:8000

Decisions: D-12 through D-16 (context doc).
No SLA assertions — this phase establishes scenario existence and throughput data.
"""
import os
from datetime import datetime, timedelta

from locust import HttpUser, between, task


class InventoryMovementUser(HttpUser):
    """Simulate a warehouse operator browsing inventory positions and movement history."""

    host = os.environ.get("PROGRESS_TEST_HOST", "http://localhost:8000")
    wait_time = between(0.5, 2.5)

    def on_start(self):
        """Authenticate and store token for subsequent requests."""
        username = os.environ.get("PROGRESS_LOAD_USER", "admin")
        password = os.environ.get("PROGRESS_LOAD_PASSWORD", "changeme")

        resp = self.client.post(
            "/auth",
            data={"username": username, "password": password},
        )
        if resp.status_code == 200:
            token = resp.json().get("access_token", "")
            self.client.headers.update({"Authorization": f"Bearer {token}"})

        self._position_key = None
        self._fetch_position()

    def _fetch_position(self):
        """Pre-fetch one position key for detail queries."""
        resp = self.client.get("/position", params={"limit": 1}, name="/position (setup)")
        if resp.status_code == 200:
            items = resp.json()
            if items:
                p = items[0]
                self._position_key = p.get("_key") or p.get("key")

    @task(3)
    def list_positions(self):
        """Read: list all inventory positions."""
        self.client.get("/position")

    @task(2)
    def get_position_detail(self):
        """Read: detail for a single position (if key available)."""
        if self._position_key:
            self.client.get(f"/position/{self._position_key}")
        else:
            self.client.get("/position")

    @task(2)
    def movement_journal(self):
        """Read: inventory movement journal with 7-day date range."""
        today = datetime.utcnow()
        week_ago = today - timedelta(days=7)
        self.client.get(
            "/movement",
            params={
                "date_from": week_ago.strftime("%Y-%m-%d"),
                "date_to": today.strftime("%Y-%m-%d"),
            },
        )

    @task(2)
    def latest_positions(self):
        """Read: most recently active inventory positions."""
        self.client.get("/movement/latest-positions")

    @task(1)
    def latest_products(self):
        """Read: most recently moved products."""
        self.client.get("/movement/latest-products")

    @task(1)
    def inventory_summary(self):
        """Read: inventory quantity summary."""
        self.client.get("/inventory")
