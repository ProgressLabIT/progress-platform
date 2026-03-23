---
phase: 04-full-integration
plan: 02
subsystem: ui
tags: [vue, quasar, print, zpl, pdf, sse, notify, spinner]

# Dependency graph
requires:
  - phase: 04-full-integration
    plan: 01
    provides: sendToPrintService(), waitForPrintResult(), printer type/timeout fields in config store
provides:
  - PrintDialog.vue step 3 "Send to [printer name]" button with ZPL/PDF routing
  - spinner state during print submission (isPrinting)
  - toast notifications for print success/error/timeout
  - selectedPrinter computed resolving user preference to config.printers entry
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "PrintDialog step 3: template v-if/v-else toggling buttons vs spinner via isPrinting ref"
    - "selectedPrinter: computed from store.state.session.user.preferences.printer matched to config.printers by host:port"
    - "sendToPrinter(): ZPL path uses generateZpl(); PDF path uses generate()+btoa(); both call sendToPrintService()+waitForPrintResult()"
    - "onDialogHide() for send-to-printer close (no download); onDialogOK() for download path"

key-files:
  created: []
  modified:
    - webapps/main/src/components/PrintDialog.vue

key-decisions:
  - "sendToPrinter uses onDialogHide() not onDialogOK() — keeps download and print paths independent with no code changes to usePrintDialog"
  - "No printServerURL or appConfig.js changes (DIAL-01 superseded) — button visibility driven by selectedPrinter computed"

requirements-completed: [DIAL-01, DIAL-03, DIAL-04, DIAL-06]

# Metrics
duration: 2min
completed: 2026-03-20
---

# Phase 4 Plan 02: PrintDialog Send-to-Printer Wiring Summary

**PrintDialog.vue step 3 wired with ZPL/PDF-routed send-to-printer action, isPrinting spinner state, and SSE-backed toast notifications alongside the unchanged Download PDF button**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-20T09:55:44Z
- **Completed:** 2026-03-20T09:58:04Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- PrintDialog.vue imports `Notify`, `useConfigStore`, `generateZpl`, `sendToPrintService`, `waitForPrintResult`, `computed`
- `selectedPrinter` computed resolves user's `preferences.printer` ("host:port") to a full printer object from `config.printers`
- `isPrinting` ref controls step 3 button/spinner toggle
- `sendToPrinter()` function: ZPL printers call `generateZpl()`, PDF printers call `generate()+btoa()`; both route through `sendToPrintService()`+`waitForPrintResult()`
- Step 3 stepper navigation: `[Cancel] [spacer] [Back] [Download PDF] [Send to {name}]` — printer button only shown when `selectedPrinter !== null`
- During printing: both buttons hidden, centered `q-spinner` shown
- Success/error/timeout toasts via `Notify.create()` after dialog closes with `onDialogHide()`
- POST failures keep dialog open (user can retry); `isPrinting` reset to false
- Verified: `sendToPrinter()` uses `onDialogHide()` NOT `onDialogOK()` — download path unchanged in `usePrintDialog`

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Send to Printer button and print flow to PrintDialog.vue** - `96adae4a` (feat)
2. **Task 2: Verify download vs send-to-printer path separation** - `8f7c6b22` (chore, no file changes)

**Plan metadata:** (docs commit below)

## Files Created/Modified

- `webapps/main/src/components/PrintDialog.vue` - Added imports, selectedPrinter computed, isPrinting ref, sendToPrinter() function, updated step 3 stepper navigation

## Decisions Made

- `sendToPrinter()` calls `onDialogHide()` — the `.onOk()` handler in `usePrintDialog` fires only on `onDialogOK()`, so the download path is untouched with zero changes to `lib/print/index.js`.
- Button visibility driven entirely by `selectedPrinter !== null` — no `printServerURL` or `appConfig.js` changes (DIAL-01 superseded per plan spec).

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None.

## Next Phase Readiness

- Plan 03 (warehouse app integration) can proceed; the print library functions (`sendToPrintService`, `waitForPrintResult`) are identical and available from `lib/print/index.js`
- Factory operators will see "Send to [printer name]" button in step 3 of any print dialog when they have a printer configured in their preferences

---
*Phase: 04-full-integration*
*Completed: 2026-03-20*
