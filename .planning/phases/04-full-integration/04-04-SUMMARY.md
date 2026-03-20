---
phase: 04-full-integration
plan: 04
subsystem: documentation
tags: [docs, km, zpl, print-service, sse, warehouse, pdfme]

# Dependency graph
requires:
  - phase: 04-full-integration
    plan: 01
    provides: sendToPrintService, waitForPrintResult, printer type/timeout fields
  - phase: 04-full-integration
    plan: 02
    provides: PrintDialog Send-to-Printer flow, SSE result handling
  - phase: 04-full-integration
    plan: 03
    provides: warehouse template assignment, BrowserPrint removal
provides:
  - complete reference documentation for printing v2 in km/domains/printing/print-templates.md
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - km/domains/printing/print-templates.md

key-decisions:
  - "PRINT_SERVICE_API_PASSWORD documented (secret-mounted) rather than PRINT_SERVICE_API_TOKEN — matches actual config.py field name (api_password via secret)"
  - "BrowserPrint mentioned in removal context only — documents what was removed, not an active reference"

requirements-completed: [DOC-01]

# Metrics
duration: 2min
completed: 2026-03-20
---

# Phase 4 Plan 04: Print Templates Documentation Summary

**km/domains/printing/print-templates.md extended with six new sections covering template string syntax, ZPL transpiler, print service deployment, printer type/timeout, Send to Printer dialog, and warehouse template assignment — fulfilling DOC-01**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-20T10:03:48Z
- **Completed:** 2026-03-20T10:06:42Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Preserved all original content (Architecture, Field properties, Link configuration, Data flow, Barcode types) with one small addition: `template_expression` added to the linkType column in the Field properties table
- Added section: **Template String Fields** — `{{variable}}` syntax, storage format (encode/decode round-trip for `cf::_key` vs `cf::slug`), `resolveExpression()` usage example, `template_expression` link type
- Added section: **ZPL Transpiler** — `generateZpl()` signature, coordinate conversion formulas (mm → dots, pt → dots), supported field types table with ZPL commands, output envelope format
- Added section: **Print Service** — full architecture diagram, deployment guide referencing `deploy/compose/print.yaml`, environment variables table, complete API contract (POST /print-job, GET /print-jobs/stream, POST /print-jobs/{id}/result, SSE notification), health check description
- Added section: **Printer Type Field** — `type` and `timeout_seconds` fields table, configuration location, ZPL vs PDF routing logic, timeout behavior (TCP + frontend +5s window)
- Added section: **Print Dialog: Send to Printer** — visibility rule, button label format, 5-step flow, toast outcomes table, "Download PDF" preserved alongside
- Added section: **Warehouse Template Assignment** — main app config keys (`product_label_template`, `position_label_template`), preset contexts for product and position labels, print flow steps, BrowserPrint removal summary

## Task Commits

Each task was committed atomically:

1. **Task 1: Update print-templates.md with full printing v2 documentation** - `c516d681` (docs)

## Files Created/Modified

- `km/domains/printing/print-templates.md` - Extended from 48 lines to 418 lines; six new sections added covering all DOC-01 topic areas

## Decisions Made

- `PRINT_SERVICE_API_PASSWORD` documented instead of `PRINT_SERVICE_API_TOKEN` — the actual `config.py` uses `api_password` as the field name, mounted via Docker secret `print_service_pwd`. The plan referenced `PRINT_SERVICE_API_TOKEN` in the action spec, but the implementation uses username+password auth, not a JWT token.
- BrowserPrint appears 3 times in the document but only in the "BrowserPrint removal" section explaining what was replaced. This is the correct documentation pattern — explaining migration context, not documenting an active dependency.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected auth env var name: PRINT_SERVICE_API_TOKEN → PRINT_SERVICE_API_PASSWORD**
- **Found during:** Task 1 (reading config.py)
- **Issue:** Plan spec said to document `PRINT_SERVICE_API_TOKEN` but `config.py` declares `api_password` (env prefix `PRINT_SERVICE_`, so env var is `PRINT_SERVICE_API_PASSWORD`). The service uses username/password login, not a pre-issued JWT token.
- **Fix:** Documented `PRINT_SERVICE_API_PASSWORD` with correct description (stored in Docker secret `print_service_pwd`, mounted at `/run/secrets/api_password`)
- **Files modified:** km/domains/printing/print-templates.md
- **Impact:** Documentation accurately reflects the deployed implementation

---

**Total deviations:** 1 auto-fixed (1 accuracy correction)
**Impact on plan:** Documentation correctness improved. No scope changes.

## Issues Encountered

None beyond the env var name correction.

## User Setup Required

None — this is documentation only.

## Next Phase Readiness

- Phase 04 is complete. All 12 plans across all 4 phases have been executed.
- DOC-01 is the final requirement; all v1 requirements are now complete.
- A new operator or admin can use `km/domains/printing/print-templates.md` as the single reference for deploying, configuring, and troubleshooting the printing v2 system.

---
*Phase: 04-full-integration*
*Completed: 2026-03-20*

## Self-Check: PASSED

All files found and commits verified.
