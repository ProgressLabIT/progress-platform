---
phase: 03-api-quality-load
plan: 02
subsystem: testing
tags: [schemathesis, fuzzing, openapi, pytest, fastapi, jwt]

requires:
  - phase: 03-01
    provides: testing/pytest/tests/api/ package
  - phase: 01-infrastructure-fixtures
    provides: db and mock_nats session fixtures

provides:
  - Schemathesis v4 fuzzing test: all non-excluded endpoints fuzzed with JWT auth
  - schemathesis>=4.15 installed in test venv

affects: [03-03]

tech-stack:
  added: [schemathesis==4.15.1]
  patterns: [schemathesis.openapi.from_asgi, @schemathesis.auth() class decorator, schemathesis.pytest.from_fixture]

key-files:
  created:
    - testing/pytest/tests/api/test_schemathesis.py
  modified:
    - testing/pytest/pyproject.toml

key-decisions:
  - "schemathesis.openapi.from_asgi('/openapi.json', app) — v4 entrypoint (not top-level from_asgi)"
  - "@schemathesis.auth() class with get()/set() protocol injects JWT header per case"
  - "set() also activates app.dependency_overrides[verify_token] so backend accepts token"
  - "api_schema fixture patches nats_client.subscribe to no-op — Schemathesis fires startup event per sub-test, which calls subscribe() after connect() returns None"
  - "case.call() used (not call_and_validate()) for explicit status code assertions with clear messages"
  - "5xx → fail, 401 → fail (auth broken), 422 → pass (expected from fuzzing)"
  - "Excluded: SSE /notification/{topic}, all UploadFile multipart routes"

patterns-established:
  - "Schemathesis from_fixture pattern: schema = schemathesis.pytest.from_fixture('api_schema')"
  - "ASGI lifespan mock: patch nats_client.subscribe in schema fixture since Schemathesis fires startup per case"
---

## Result

Test passes (exit code 0). 9 Schemathesis sub-cases run against all non-excluded endpoints. No 5xx responses. SSE and multipart routes skipped. Auth injection via dependency override confirmed working.

Key discovery: Schemathesis v4 fires FastAPI ASGI startup event for each parametrized sub-test (not just once). The mock_nats fixture patches connect() but subscribe() still calls get_nats() which fails with _nc=None. Fixed by also patching subscribe() as a no-op in the api_schema fixture.
