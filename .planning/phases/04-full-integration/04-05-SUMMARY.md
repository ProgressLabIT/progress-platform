---
phase: 04-full-integration
plan: 05
subsystem: ui
tags: [vue, pdfme, printing, btoa, base64]

# Dependency graph
requires:
  - phase: 04-full-integration
    provides: PrintDialog.vue with sendToPrinter PDF path and SSE result subscription
provides:
  - Chunked btoa conversion in PrintDialog.vue that handles PDFs of any size without stack overflow
affects: [04-full-integration]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Chunked Uint8Array-to-base64 conversion using 8192-byte subarray slices via String.fromCharCode.apply"]

key-files:
  created: []
  modified:
    - webapps/main/src/components/PrintDialog.vue

key-decisions:
  - "chunkSize = 8192 chosen as safe chunk size — well under V8's ~65000 argument limit, handles PDFs of any size"
  - "Used subarray() not slice() for zero-copy view; String.fromCharCode.apply(null, chunk) replaces spread operator"

patterns-established:
  - "Large binary-to-base64 conversions: always use chunked loop with subarray, never spread operator on Uint8Array"

requirements-completed: [DIAL-03]

# Metrics
duration: 1min
completed: 2026-03-20
---

# Phase 4 Plan 05: Fix PDF Stack Overflow in PrintDialog Summary

**Chunked 8192-byte btoa conversion in PrintDialog.vue replaces spread operator that crashed V8 with 50-500K argument PDFs**

## Performance

- **Duration:** ~1 min
- **Started:** 2026-03-20T13:04:10Z
- **Completed:** 2026-03-20T13:04:50Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Replaced `btoa(String.fromCharCode(...new Uint8Array(pdfBytes)))` with chunked 8192-byte loop
- Eliminated "Maximum call stack exceeded" crash for all PDF sizes (50KB-500KB range)
- Preserved identical base64 output — only the conversion path changed
- Zero-copy buffer access via `subarray()` instead of `slice()`

## Task Commits

Each task was committed atomically:

1. **Task 1: Replace spread-based btoa with chunked conversion** - `3eefbd8c` (fix)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `webapps/main/src/components/PrintDialog.vue` - Lines 742-748: replaced single-line spread btoa with chunked 8192-byte loop

## Decisions Made

- chunkSize = 8192 bytes: safe under V8's ~65000 argument limit while keeping chunk count low for large PDFs
- Used `subarray()` instead of `slice()`: zero-copy view on the same buffer, no intermediate allocations
- Did not refactor to use `generatePdf()` from lib/print/index.js as instructed — PrintDialog has gs1datamatrix migration logic specific to dialog context

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- PDF printing via PrintDialog.vue is now unblocked for any PDF size
- All three UAT issues from phase 04 gap closure are resolved (this was the last gap plan)

---
*Phase: 04-full-integration*
*Completed: 2026-03-20*
