---
phase: 03-print-service
plan: 01
subsystem: api
tags: [fastapi, pydantic, sse, arangodb, print-jobs]

# Dependency graph
requires:
  - phase: 02-zpl-generator
    provides: ZPL generation pipeline that produces the data payload for print jobs
provides:
  - PrintJob pydantic models (PrintJobRequest, PrintJobResult, PrintJobRecord, PrintFormat)
  - POST /print-job endpoint: accepts job from browser, stores DB record, enqueues SSE event
  - GET /print-jobs/stream endpoint: SSE channel for print service subscription
  - POST /print-jobs/{job_id}/result endpoint: job result callback, updates DB, notifies browser
affects: [03-print-service]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - SSE routing via subtopic key in JSON payload (ServerEventManager.enqueue expects json.loads(message)['subtopic'])
    - Print job lifecycle via SSE-subscriber pattern (browser -> main API -> SSE -> print service -> callback)
    - ArangoDB insert/update via db.collection('PrintJob').insert() and .update() with _key

key-files:
  created:
    - backend/api/models/print_job.py
  modified:
    - backend/api/endpoints/print.py

key-decisions:
  - "data field excluded from PrintJobRecord DB storage (can be large base64 PDF) — only passes through SSE payload"
  - "SVC-03 (CORS on print service) claimed for traceability only — no implementation needed since browser never calls print service directly"

patterns-established:
  - "SSE endpoint pattern: EventSourceResponse(ServerEventManager.getInstance().push_events(request, topic))"
  - "SSE enqueue pattern: payload must include subtopic key for routing — json.dumps({..., 'subtopic': 'print-jobs'})"
  - "Print job status lifecycle: pending -> sent | failed, updated via /result callback"

requirements-completed: [SVC-01, SVC-02, SVC-03]

# Metrics
duration: 5min
completed: 2026-03-18
---

# Phase 03 Plan 01: Print Job API Endpoints Summary

**Three SSE-backed print job endpoints added to main API: browser submits jobs via POST, print service subscribes via SSE stream, result callback updates DB and pushes browser notification**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-18T21:42:27Z
- **Completed:** 2026-03-18T21:47:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Created `PrintJobRequest`, `PrintJobRecord`, `PrintJobResult`, and `PrintFormat` pydantic models in `backend/api/models/print_job.py`
- Added POST /print-job endpoint that stores a pending DB record and enqueues an SSE event with subtopic "print-jobs"
- Added GET /print-jobs/stream SSE channel following the same EventSourceResponse pattern as notification.py
- Added POST /print-jobs/{job_id}/result endpoint that marks jobs sent/failed and triggers notifyGlobalRefresh() for browser push

## Task Commits

Each task was committed atomically:

1. **Task 1: Create PrintJob pydantic models** - `5da95004` (feat)
2. **Task 2: Add print job endpoints to existing print router** - `f3764a36` (feat)

## Files Created/Modified

- `backend/api/models/print_job.py` - PrintFormat enum, PrintJobRequest, PrintJobRecord (extends ArangoDocument), PrintJobResult models
- `backend/api/endpoints/print.py` - Added 3 new print job endpoints and necessary imports alongside existing 6 template endpoints

## Decisions Made

- `data` field excluded from `PrintJobRecord` DB storage — it passes through the SSE payload to the print service but is not persisted (large base64 PDF payloads would bloat the database)
- SVC-03 (CORS on print service) required no implementation — the SSE-subscriber architecture means the browser never contacts the print service directly; claimed for requirements traceability only

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. The `PrintJob` ArangoDB collection must exist (assumed pre-configured in the database).

## Next Phase Readiness

- All three print job lifecycle endpoints are live on the existing authenticated main API
- The print service (plan 03-02) can now subscribe to GET /print-jobs/stream with a Bearer token and receive job payloads via SSE
- The result callback POST /print-jobs/{job_id}/result is ready to receive completion status from the print service

---
*Phase: 03-print-service*
*Completed: 2026-03-18*
