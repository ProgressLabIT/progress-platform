# Phase 3: API Quality + Load - Context

**Gathered:** 2026-04-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver three testing artifacts:
1. An OpenAPI spec audit (pytest test, warn-only) that reports endpoint coverage for input models, response models, and docstrings across all 20+ endpoint files
2. A Schemathesis fuzzing run (pytest test) via `from_asgi()` against all endpoints using an injected JWT fixture token — fails on any 5xx response to valid inputs
3. Three Locust scenario scripts (standalone, headless) for batch completion, inventory movement, and production queries — must run without crashing and produce throughput/latency output

No changes to the backend event system, no new fixtures beyond auth token injection. This phase consumes Phase 1 infrastructure (ASGITransport client, auth_headers fixture).

</domain>

<decisions>
## Implementation Decisions

### Audit Scope and Pass Bar
- **D-01:** Audit runs against ALL endpoints in `backend/api/endpoints/` (20+ files) — not just critical ones
- **D-02:** Audit is warn-only: missing `response_model`, missing docstring, or missing Pydantic input model are WARNING-level findings — the test produces a structured report but does NOT fail on them
- **D-03:** Test fails ONLY on: crashes (unhandled exceptions during audit), or 5xx responses from the app itself
- **D-04:** Audit output format: printed table/report listing each endpoint with its coverage status (✓/✗ for each dimension: input_model, response_model, docstring)
- **D-05:** Audit uses FastAPI's `app.routes` introspection to enumerate routes — no manual list maintenance

### Schemathesis Auth Strategy
- **D-06:** Schemathesis uses `from_asgi(app)` with the same ASGITransport approach from Phase 1
- **D-07:** Inject a valid JWT token via the `auth_headers` fixture (admin or planning scope) into the Schemathesis session — all endpoints covered, not just unauthenticated ones
- **D-08:** 401 responses on valid inputs count as failures (means auth injection is broken)
- **D-09:** 422 responses are expected and acceptable (schema fuzzing will generate invalid payloads)
- **D-10:** 5xx responses on valid inputs count as failures — the primary signal Schemathesis is looking for
- **D-11:** Schemathesis runs as a pytest test (not standalone script) so it uses the testcontainer ArangoDB

### Locust Scenarios
- **D-12:** Three standalone Locust scripts (not pytest): batch completion, inventory movement, production queries
- **D-13:** "Can be executed" means: `locust --headless -u 10 -r 2 --run-time 30s` completes without crashing and produces output
- **D-14:** No SLA assertions (no p95 targets, no error rate thresholds) — this phase establishes scenario existence, not performance tuning
- **D-15:** Locust scripts live in `testing/locust/` directory, one file per scenario
- **D-16:** Locust scenarios target a running server (not in-process) — they are documented as manual-run tools, not CI tests

### Test vs Script Boundary
- **D-17:** Audit (warn-only report) → pytest test in `testing/pytest/tests/api/test_openapi_audit.py`
- **D-18:** Schemathesis fuzzing → pytest test in `testing/pytest/tests/api/test_schemathesis.py`
- **D-19:** Locust scenarios → standalone scripts in `testing/locust/` — separate from pytest entirely
- **D-20:** Both pytest tests use the existing `client` and `auth_headers` fixtures from Phase 1 conftest

### Plan Split
- **D-21:** Plan 03-01: OpenAPI audit test — enumerate routes via `app.routes`, report per-endpoint coverage (SPEC-01 through SPEC-06)
- **D-22:** Plan 03-02: Schemathesis fuzzing pytest test — `from_asgi(app)`, JWT injection, fail on 5xx (SPEC-03)
- **D-23:** Plan 03-03: Locust scenario scripts — three files in `testing/locust/`, headless execution documented (LOAD-01 through LOAD-03)

### Claude's Discretion
- Exact Schemathesis API version and `auth_provider` vs `headers` injection mechanism — researcher to confirm from installed package
- Which endpoint routes to exclude from Schemathesis (e.g., WebSocket endpoints, file upload endpoints that need multipart) — planner to decide based on route inspection
- Locust `HttpUser` base URL configuration (env var vs hardcoded localhost) — planner decides

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `backend/api/main.py` — FastAPI app definition, route registration, middleware chain
- `backend/api/endpoints/` — All 20+ endpoint files to be audited
- `testing/pytest/conftest.py` — Root conftest with ArangoDB testcontainer, client fixture, auth_headers
- `testing/pytest/pyproject.toml` — Test dependencies (check if schemathesis and locust are already declared)
- `backend/api/models/` — Pydantic models used as input/response models in endpoints

</canonical_refs>

<code_context>
## Existing Code Insights

- FastAPI app at `backend/api/main.py` — uses `root_path=config.api_root_path`
- 20+ endpoint files in `backend/api/endpoints/` (admin, auth, bom, collaboration, config, counter, counting, file, form, inventory, media, notification, org, print, process, product, production, serial, tag)
- Endpoints use wildcard imports (`from models.production import *`) — response_model coverage may be patchy
- Phase 1 fixtures provide: ArangoDB testcontainer (session-scoped), `client` (httpx.AsyncClient with ASGITransport), `auth_headers` (JWT fixture)
- No existing Schemathesis or Locust infrastructure in the project

</code_context>

<specifics>
## Specific Ideas

- Use `app.routes` introspection (FastAPI's `APIRoute`) to enumerate endpoints — avoids maintaining a manual list
- Schemathesis `from_asgi(app, base_url="http://testserver")` — same pattern as Phase 1 HTTP tests
- Locust headless invocation: `locust -f testing/locust/batch_completion.py --headless -u 10 -r 2 --run-time 30s --host http://localhost:8000`

</specifics>

<deferred>
## Deferred Ideas

- **Printer routing todo** (reviewed, not folded): "Support local printers with per-printer print service routing" — out of scope for this phase, already in backlog
- **SLA enforcement**: If load testing needs pass/fail gates in CI, add a Phase 3.1 or Phase 5 with Locust thresholds and environment-specific tuning
- **Schemathesis stateful testing** (stateful mode / OpenAPI links): More advanced, deferred to future iteration

</deferred>
