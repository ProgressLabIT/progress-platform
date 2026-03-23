---
status: complete
phase: 03-print-service
source: 03-01-SUMMARY.md, 03-02-SUMMARY.md
started: 2026-03-19T00:05:00Z
updated: 2026-03-19T12:00:00Z
---

## Current Test

<!-- OVERWRITE each test - shows where we are -->

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Kill any running print service. Start `python main.py` (or Docker). Process boots without errors, health endpoint on :8200 responds.
result: pass

### 2. TCP Sender Unit Tests
expected: Run `cd backend/print-service && pytest test_tcp_sender.py` — all 8 tests pass (encode_zpl ASCII/replace/error, decode_pdf valid/invalid, send_tcp success/refused/timeout).
result: pass

### 3. POST /print-job Creates Pending Record
expected: POST to `/api/print-job` with a valid PrintJobRequest body returns 200. A new record with `status: pending` appears in the PrintJob ArangoDB collection.
result: issue
reported: "we've dropped the PrintJob collection"
severity: minor

### 4. GET /print-jobs/stream Delivers SSE Events
expected: A client subscribed to `GET /api/print-jobs/stream` (e.g. curl -N or the print service itself) receives an SSE event when a job is submitted via POST /print-job. The event payload includes the job data and `subtopic: print-jobs`.
result: pass

### 5. POST /print-jobs/{job_id}/result Updates Job Status
expected: POST to `/api/print-jobs/{job_id}/result` with `{"status": "sent"}` updates the DB record from `pending` to `sent`. The browser receives a global refresh notification (notifyGlobalRefresh triggered).
result: skipped
reason: test after client is updated

### 6. Print Service Dockerfile Builds
expected: `docker build -f backend/print-service/Dockerfile backend/print-service` completes without error. The image contains only main.py, config.py, tcp_sender.py (no test file).
result: pass

## Summary

total: 6
passed: 4
issues: 1
pending: 0
skipped: 1
skipped: 0

## Gaps

- truth: "POST /print-job returns 200 and job is tracked (in-memory, no DB collection)"
  status: failed
  reason: "User reported: we've dropped the PrintJob collection"
  severity: minor
  test: 3
  artifacts: []
  missing: []
