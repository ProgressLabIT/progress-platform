# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — Printing v2

**Shipped:** 2026-03-20
**Phases:** 4 | **Plans:** 14 | **Timeline:** 9 days (2026-03-12 → 2026-03-20)

### What Was Built

- Template string `{{variable}}` composite text fields in pdfme designer with encode/decode/resolve pipeline
- Pure-JS `generateZpl()` ZPL II transpiler (text, 5 barcode types, configurable DPI, image skip)
- On-prem SSE-subscriber print service: Python asyncio TCP relay with Docker Compose deployment
- PrintDialog "Send to Printer" with ZPL/PDF routing, chunked btoa, real-time SSE feedback
- Warehouse app migrated from hardcoded Zebra `/pstprint` to unified print service + pdfme templates
- Full knowledge management documentation

### What Worked

- **SSE-subscriber architecture**: Choosing an outbound SSE subscriber over an inbound HTTP server eliminated CORS complexity, Traefik config, and firewall concerns in one decision. The ~100-line print service delivered on the "stateless relay" promise.
- **Subscribe-before-submit pattern**: Registering the SSE listener before calling `sendToPrintService()` eliminated the race condition that would have caused intermittent missed results.
- **Phase verification + UAT catching real bugs**: Verification caught that Phase 01 VERIFICATION.md had an incorrect finding (toolbar button), and UAT caught two blockers (btoa stack overflow, warehouse false-success notifications) before milestone close — exactly the right time.
- **Yolo mode + coarse granularity**: 14 plans across 9 days with minimal friction. Plan-execute-verify cycle ran cleanly for all 4 phases.

### What Was Inefficient

- **Phase 01 architectural deviation poorly documented**: The decision to replace the `template_string` pdfme plugin with a `linkType` option was correct but wasn't reflected back into the requirements or the Phase 01 VERIFICATION.md. This caused VERIFICATION.md to claim the toolbar button was missing when it wasn't, and left `linkedTemplateString.js` as an orphan. The architectural decision should have triggered a requirements update at decision time.
- **SUMMARY frontmatter `requirements-completed` field empty in all plans**: The 3-source cross-reference in audit-milestone relies on this field. All SUMMARYs had it as `MISSING`, forcing the audit to rely solely on VERIFICATION.md tables. A structured frontmatter field would have made the audit more authoritative.
- **Phase 01 re-verification not triggered after architectural deviation**: The verification was written before the Phase 04 architectural clarification. A re-verification of Phase 01 should have been triggered when the linkType deviation was finalized.

### Patterns Established

- **SSE print result pattern**: Subscribe to `/notification/print-result` EventSource BEFORE job submission, match by `job_id`, close on match or timeout. Use `theme-green`/`theme-orange`/`theme-red` notification colors in warehouse, `type: 'positive'/'negative'` in main app (different conventions per app).
- **Large binary-to-base64**: Always use chunked loop with `subarray(i, i + 8192)` + `String.fromCharCode.apply()` — never spread `Uint8Array` into `fromCharCode`.
- **Vitest node environment**: Use `environment: 'node'` in `vitest.config.js` for print lib tests — avoids Vue/Quasar framework import resolution errors for pure-JS modules.
- **Print service deployment**: `traefik.enable=false`, no networks, no volumes, `PRINT_SERVICE_*` env prefix, outbound SSE only. Health endpoint as raw asyncio TCP on :8200.

### Key Lessons

1. **Document architectural deviations immediately in requirements**: When a plan deviates from the spec (e.g., linkType vs dedicated plugin), update REQUIREMENTS.md at that moment — not retrospectively. Stale requirements create audit noise.
2. **UAT is the right gate for E2E issues**: Both blockers found in this milestone (btoa overflow, false-success notification) were correctly caught at UAT — not earlier. The verifier can't catch runtime-only failures. This confirms UAT as a valuable step even when it feels redundant.
3. **SUMMARY frontmatter is only valuable if filled**: The `requirements-completed` field in SUMMARY frontmatter was present in the schema but never populated. Either enforce it during execution or remove it from the audit cross-reference.
4. **Architecture deviation in one phase ripples into later verification**: A decision made in Phase 04 (linkType approach) changed the expected artifacts for Phase 01 verification. Cross-phase architectural decisions need a designated owner to update earlier phase documentation.

### Cost Observations

- Model mix: primarily sonnet (balanced profile)
- Sessions: ~8-10 sessions across 9 days
- Notable: 14 plans at avg ~4 min each = highly efficient execution; planning and verification overhead was proportionally larger than execution

---

## Milestone: v2.0 — Test Suite

**Shipped:** 2026-04-11
**Phases:** 4 | **Plans:** 15 | **Timeline:** 3 days (2026-04-09 → 2026-04-11)

### What Was Built

- pytest + testcontainers harness with db singleton override, NATS mock, httpx ASGI client, per-class collection truncation
- 14 domain factory fixtures covering the full object graph (WorkOrder → Job → Batch → WorkSession → StepExecution → Config → Serial → WIP → Position)
- Dual-layer test suites for 4 critical events: StepCompleted (8), BatchCompleted (24), ProgressOverrideRequested (16), MovementCompleted (18)
- OpenAPI audit (75+ routes, warn-only) + Schemathesis fuzzing (zero 5xx) + Locust load scenarios (3 endpoints)
- Vitest component tests for ProgressBtn (8) + WorkSessionSteps (11) + Playwright E2E (3 journeys)

### What Worked

- **Dual-layer strategy paid off immediately**: Direct event instantiation tests caught edge cases (form_data type mismatch, SXD factory collision, _rev conflicts) that HTTP tests would have missed entirely. The separation of "realism" vs "coverage" is load-bearing.
- **Testcontainers + db singleton override**: The env-vars-before-import + lru_cache-clear pattern worked reliably. Zero flaky container startup failures across 15 plans.
- **Curated parametrize matrix for BatchCompleted**: 9 rows covering all branch points was the right call — 32-row exhaustive matrix would have been brittle and unmaintainable. Trade-off: left BATCH-13 uncovered.
- **Warn-only OpenAPI audit**: Correct framing — audit reveals state, doesn't gate CI. Avoids blocking development on a 75+ endpoint remediation effort.
- **3-day execution**: All 15 plans in 3 days with yolo+coarse granularity. No friction from planning overhead.

### What Was Inefficient

- **SUMMARY frontmatter inconsistency**: Phases 1-3 used different SUMMARY structures (YAML tags vs narrative vs frontmatter-only). gsd-tools milestone complete extracted junk accomplishments as a result. Needs a consistent structured one_liner field enforced during execution.
- **BATCH-13 / PROG-10 / PROG-11 left uncovered**: These require `manage_inventory=True` + warehouse interaction in factory fixtures — a path not built during Phase 1. Should have been flagged as factory gap in Phase 1 PLAN and addressed before Phase 2. Audit surfaced these too late.
- **Nyquist validation skipped entirely**: All 4 phases missing VALIDATION.md. The validation step was disabled in config (nyquist_validation: false) and no manual override was done. Coverage quality unvalidated.
- **STATE.md milestone field not updated by gsd-tools**: milestone field remained v1.0 after archive; needed manual correction.

### Patterns Established

- **db singleton override pattern**: Set `PROGRESS_ARANGO_URL`, `PROGRESS_DB_NAME` via `os.environ.update()` at module level in conftest.py before any backend import. Call `get_config.cache_clear()` after. Override `db_module.db` and `auth_module.db` with the test db object.
- **NATS mock pattern**: `monkeypatch.setattr` on 5 namespaces: the nats module + 4 local import paths across event files. Session-scoped, autouse.
- **Dual-layer test structure**: One file per event, two `TestXxxHTTP` / `TestXxxDirect` classes. HTTP tests use `httpx.AsyncClient` with `ASGITransport`. Direct tests instantiate event class with factory-built objects.
- **Factory fixture ordering**: `conftest_helpers/schema.py` must import before backend modules. Factory fixtures are function-scoped; container + db are session-scoped; truncation is autouse function-scoped.
- **Warn-only test audit**: Collect findings into a `warnings` list, log at WARNING level, assert only on structural completeness (>= N routes), never on content quality.

### Key Lessons

1. **Factory gaps compound**: Missing fields in factory fixtures (manage_inventory, product_key, batch_serial edges) silently skip business logic branches. Factory completeness should be validated against all event apply() methods before Phase 2, not discovered during audit.
2. **SUMMARY frontmatter needs a one_liner field**: The milestone archive tool relies on structured extraction. Free-form SUMMARYs produce garbage accomplishments. Enforce `one_liner:` as a required field in SUMMARY frontmatter.
3. **Curated > exhaustive for parametrize**: 9 rows covering all branch points beats 32 rows covering all combinations. Exhaustive matrices create maintenance burden without proportional coverage gain — but document explicitly which combinations are excluded and why.
4. **Testcontainers is the right call for ArangoDB**: Zero shared state issues, zero test ordering dependencies, zero environment assumptions. The 20-30s startup cost is worth it for the isolation guarantee.

### Cost Observations

- Model mix: primarily sonnet (balanced profile)
- Sessions: ~5-6 sessions across 3 days
- Notable: 15 plans in 3 days at yolo+coarse — fastest milestone execution yet; planning was proportionally small vs execution

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Plans | Key Change |
|-----------|----------|--------|-------|------------|
| v1.0 | ~10 | 4 | 14 | First milestone on this project |
| v2.0 | ~6 | 4 | 15 | New project (test suite); fastest execution yet |

### Cumulative Quality

| Milestone | Tests | Key Additions | Audit Status |
|-----------|-------|---------------|--------------|
| v1.0 | 38 (vitest) + 8 (pytest) | templateResolver.js, zpl.js, tcp_sender.py | tech_debt |
| v2.0 | 75+ (pytest) + 19 (vitest) + 10 (playwright) | testcontainers harness, 14 factory fixtures, 4 event test suites | gaps_found (3/106) |

### Top Lessons (Verified Across Milestones)

1. Document architectural deviations in requirements at decision time, not retrospectively
2. UAT is the right gate for runtime-only failures that static verification cannot catch
3. Factory/fixture completeness must be verified against all downstream business logic paths before dependent phases begin
4. Structured SUMMARY frontmatter (one_liner field) is required for automated milestone archive quality
