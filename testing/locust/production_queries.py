"""Locust scenario: Production Queries (supervisor dashboard reads).

Simulates a production supervisor checking work order status,
job lists, queue state, and search options.

Run headless:
    locust -f testing/locust/production_queries.py --headless -u 10 -r 2 --run-time 30s --host http://localhost:8000

Decisions: D-12 through D-16 (context doc).
No SLA assertions — this phase establishes scenario existence and throughput data.
"""
import os

from locust import HttpUser, between, task


class ProductionQueriesUser(HttpUser):
    """Simulate a production supervisor doing read-heavy dashboard queries."""

    host = os.environ.get("PROGRESS_TEST_HOST", "http://localhost:8000")
    wait_time = between(0.3, 1.5)

    def on_start(self):
        """Authenticate and cache context for parameterized queries."""
        username = os.environ.get("PROGRESS_LOAD_USER", "admin")
        password = os.environ.get("PROGRESS_LOAD_PASSWORD", "changeme")

        resp = self.client.post(
            "/auth",
            data={"username": username, "password": password},
        )
        if resp.status_code == 200:
            token = resp.json().get("access_token", "")
            self.client.headers.update({"Authorization": f"Bearer {token}"})

        self._site_key = None
        self._job_key = None
        self._fetch_context()

    def _fetch_context(self):
        """Pre-fetch site key and job key for parameterized tasks."""
        # Try to get a site/org key for queue queries
        resp = self.client.get("/org", name="/org (setup)")
        if resp.status_code == 200:
            items = resp.json()
            if items:
                org = items[0]
                self._site_key = org.get("_key") or org.get("key")

        # Pre-fetch a job key
        resp = self.client.get("/job", params={"limit": 1}, name="/job (setup)")
        if resp.status_code == 200:
            items = resp.json()
            if items:
                j = items[0]
                self._job_key = j.get("_key") or j.get("key")

    @task(4)
    def list_work_orders(self):
        """Read: full work order list (main supervisor dashboard view)."""
        self.client.get("/work-order")

    @task(3)
    def search_opts(self):
        """Read: work order search options (dropdown population)."""
        self.client.get("/work-order-search-opts")

    @task(3)
    def list_jobs(self):
        """Read: all active jobs."""
        self.client.get("/job")

    @task(2)
    def job_assignments(self):
        """Read: job assignment list."""
        self.client.get("/job-assignment")

    @task(2)
    def site_queue(self):
        """Read: production queue for site (if site key available)."""
        if self._site_key:
            self.client.get(f"/queue/site/{self._site_key}")
        else:
            self.client.get("/work-order", name="/work-order (fallback)")

    @task(1)
    def job_detail(self):
        """Read: single job detail (if job key available)."""
        if self._job_key:
            self.client.get(f"/job/{self._job_key}")
        else:
            self.client.get("/job", name="/job (fallback)")
