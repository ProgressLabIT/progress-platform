---
phase: 03-api-quality-load
plan: 03
subsystem: testing
tags: [locust, load-testing, http, production, inventory]

requires:
  - phase: 03-01
    provides: understanding of API endpoint structure
  - phase: 03-02
    provides: auth pattern for HTTP clients

provides:
  - Three standalone Locust scenario scripts in testing/locust/
  - locust>=2.0 installed in test venv

affects: []

tech-stack:
  added: [locust==2.43.4]
  patterns: [HttpUser with on_start() OAuth2 auth, env-var configurable host, task weights]

key-files:
  created:
    - testing/locust/__init__.py
    - testing/locust/batch_completion.py
    - testing/locust/inventory_movement.py
    - testing/locust/production_queries.py
  modified:
    - testing/pytest/pyproject.toml

key-decisions:
  - "HOST configurable via PROGRESS_TEST_HOST env var with http://localhost:8000 fallback"
  - "Credentials via PROGRESS_LOAD_USER / PROGRESS_LOAD_PASSWORD env vars with obvious placeholders"
  - "on_start() POST /auth with form-encoded data (OAuth2PasswordRequestForm)"
  - "No SLA assertions — pass bar is 'runs without crashing and produces throughput output'"
  - "Task weights reflect realistic user behavior (reads 3x more frequent than writes)"
  - "Write tasks omitted from batch_completion (require seeded DB keys)"

patterns-established:
  - "Locust scenario: on_start() auth → _fetch_context() setup → @task() read/write mix"
  - "Graceful degradation: if setup fetch fails, tasks fall back to simpler reads"
---

## Result

All three Locust scripts are valid Python, import cleanly, and define the required HttpUser subclasses with correct on_start() auth pattern. Ready for headless execution against a seeded target server.

Run command:
    locust -f testing/locust/batch_completion.py --headless -u 10 -r 2 --run-time 30s --host http://localhost:8000
