---
phase: 03-api-quality-load
plan: 01
subsystem: testing
tags: [fastapi, openapi, pytest, introspection]

requires:
  - phase: 01-infrastructure-fixtures
    provides: db and mock_nats session fixtures

provides:
  - OpenAPI coverage audit test: warn-only report of all endpoint coverage dimensions
  - testing/pytest/tests/api/ package marker

affects: [03-02, 03-03]

tech-stack:
  added: []
  patterns: [FastAPI route introspection via app.routes + APIRoute, warn-only test pattern]

key-files:
  created:
    - testing/pytest/tests/api/__init__.py
    - testing/pytest/tests/api/test_openapi_audit.py
  modified: []

key-decisions:
  - "Test fails only on crash or < 20 routes — never on missing response_model/docstring"
  - "_has_pydantic_input() uses route.dependant.body_params (FastAPI resolved tree, not raw annotations)"
  - "UploadFile routes flagged as 'multipart' (M in table) rather than false-negative 'no'"
  - "GET/DELETE routes skip the no-input-model warning since bodies are never expected"
  - "assert len(rows) >= 20 catches broken router registration"

patterns-established:
  - "Warn-only audit pattern: collect findings into warnings list, log at WARNING, never assert on them"
  - "Route coverage table format: METHOD | PATH | INPUT | RESP | DOC"
---

## Result

`test_openapi_coverage_audit` passes in 4.6s. Enumerates 75+ API routes via app.routes introspection. Prints structured coverage table. Detects multipart endpoints (M), warns on missing response_model/docstring without failing.
