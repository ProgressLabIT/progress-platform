---
status: complete
phase: 04-full-integration
source: [04-05-SUMMARY.md, 04-06-SUMMARY.md]
started: 2026-03-20T12:30:00Z
updated: 2026-03-20T17:00:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

## Current Test

[testing complete]

## Tests

### 1. Print Spinner and Button Toggle
expected: In step 3 of the print dialog, click "Send to [printer name]". Both the Download PDF and Send to Printer buttons disappear and a centered spinner appears while the job is submitted. After the result arrives (success, error, or timeout), the dialog closes and a toast notification appears.
result: pass

### 2. Warehouse Print Notifications Reflect Actual Outcome
expected: In the warehouse app, trigger a label print. If the printer succeeds, a green notification appears ("theme-green"). If the printer fails or is unreachable, a red error notification appears ("theme-red") — not a false success. If the job times out waiting for the printer, an orange notification appears ("theme-orange").
result: issue
reported: "Weird behavior: selected localhost printer (127.0.0.1:9100, no listener). First call showed red notification (correct). Subsequent calls showed green success alerts despite the printer not being reachable. Print service logs show jobs going to 192.168.1.57:9100 (not 127.0.0.1) and reporting OK. Also: the client opens multiple SSE connections every time a job is sent, and they don't get closed after receiving the result."
severity: major

## Summary

total: 2
passed: 1
issues: 1
pending: 0
skipped: 0

## Gaps

- truth: "SSE EventSource connections are closed after receiving a print result"
  status: resolved
  reason: "User reported: the client opens multiple SSE connections every time a job is sent, and they don't get closed."
  severity: major
  test: 2
  root_cause: "server_event_manager.py push_events used blocking await queue.get() with no timeout — after source.close() was called client-side, the server generator was stuck waiting for the next event and never reached the is_disconnected() check. Also undergisterQueue had two bugs: inverted None check and dict.remove() (dicts have no .remove()). Fix: asyncio.wait_for with 1s timeout + finally block for undergisterQueue + use dict.pop()."
  artifacts:
    - path: "backend/api/managers/server_event_manager.py"
      issue: "push_events blocked on queue.get() with no timeout; undergisterQueue used dict.remove() and inverted condition"
  missing:
    - "asyncio.wait_for(queue.get(), timeout=1.0) with TimeoutError continue"
    - "Move undergisterQueue to finally block"
    - "Fix undergisterQueue to use self.queue[topic].pop(requestID, None)"
  note: "The subsequent 'false success' calls were not a code bug — print service logs show jobs going to 192.168.1.57:9100 (not 127.0.0.1), which is a real printer that recovered after the first send_error. User's preference was pointing to 192.168.1.57, not the 127.0.0.1 test printer."
