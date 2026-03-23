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

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Plans | Key Change |
|-----------|----------|--------|-------|------------|
| v1.0 | ~10 | 4 | 14 | First milestone on this project |

### Cumulative Quality

| Milestone | Tests | Zero-Dep Additions | Audit Status |
|-----------|-------|--------------------|--------------|
| v1.0 | 38 (vitest) + 8 (pytest) | templateResolver.js, zpl.js, tcp_sender.py | tech_debt |

### Top Lessons (Verified Across Milestones)

1. Document architectural deviations in requirements at decision time, not retrospectively
2. UAT is the right gate for runtime-only failures that static verification cannot catch
