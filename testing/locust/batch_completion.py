"""Locust scenario: Batch Completion cycle.

Simulates a production operator checking active work orders and jobs,
then submitting a job update (batch record insertion).

Run headless:
    locust -f testing/locust/batch_completion.py --headless -u 10 -r 2 --run-time 30s --host http://localhost:8000

Or with env vars:
    PROGRESS_LOAD_USER=admin PROGRESS_LOAD_PASSWORD=secret locust -f ...

Decisions: D-12 through D-16 (context doc).
No SLA assertions — this phase establishes scenario existence and throughput data.
"""
import os

from locust import HttpUser, between, task


class BatchCompletionUser(HttpUser):
    """Simulate an operator checking jobs and submitting batch updates."""

    # --host CLI flag overrides this at runtime
    host = os.environ.get("PROGRESS_TEST_HOST", "http://localhost:8000")
    wait_time = between(0.5, 2.0)

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
        # If auth fails (no seeded user), requests will return 401 — recorded as failures

        # Cache a work order key for write scenarios
        self._wo_key = None
        self._job_key = None
        self._fetch_work_order()

    def _fetch_work_order(self):
        """Pre-fetch one work order key for use in write tasks."""
        resp = self.client.get("/work-order", params={"limit": 1}, name="/work-order (setup)")
        if resp.status_code == 200:
            items = resp.json()
            if items:
                wo = items[0]
                self._wo_key = wo.get("_key") or wo.get("key")

    @task(3)
    def list_work_orders(self):
        """Read: list all active work orders."""
        self.client.get("/work-order")

    @task(3)
    def list_jobs(self):
        """Read: list jobs, optionally filtered by work order."""
        params = {}
        if self._wo_key:
            params["wo_key"] = self._wo_key
        self.client.get("/job", params=params)

    @task(2)
    def get_job_detail(self):
        """Read: fetch single job detail by key (if available)."""
        if not self._job_key:
            # Try to resolve a job key
            resp = self.client.get("/job", params={"limit": 1}, name="/job (setup)")
            if resp.status_code == 200:
                items = resp.json()
                if items:
                    j = items[0]
                    self._job_key = j.get("_key") or j.get("key")
        if self._job_key:
            self.client.get(f"/job/{self._job_key}")

    @task(1)
    def get_search_opts(self):
        """Read: fetch work order search options."""
        self.client.get("/work-order-search-opts")
