---
phase: quick
plan: 260319-ios
type: execute
wave: 1
depends_on: []
files_modified:
  - .planning/ROADMAP.md
autonomous: true
requirements: [DIAL-01, DIAL-02]
must_haves:
  truths:
    - "Phase 4 ROADMAP reflects that PrintJob DB collection is dropped and job_id is uuid4() in-memory"
    - "Phase 4 ROADMAP requires frontend to subscribe to /notification/print-result SSE stream, filtering by job_id"
    - "Phase 3 success criteria updated to match the actual stateless architecture"
  artifacts:
    - path: ".planning/ROADMAP.md"
      provides: "Updated Phase 3 + Phase 4 descriptions"
      contains: "print-result"
---

<objective>
Update ROADMAP.md to reflect architecture changes made during Phase 3 execution and capture new Phase 4 requirements for SSE-based print result feedback.

Purpose: Phase 3 was completed with significant architecture simplifications (no PrintJob DB collection, SSE-based result delivery) that are not yet reflected in the roadmap. Phase 4 planning cannot begin until these changes are captured.

Output: Updated ROADMAP.md with accurate Phase 3 success criteria and new Phase 4 requirements for print-result SSE subscription.
</objective>

<execution_context>
@/Users/luca/.claude/get-shit-done/workflows/execute-plan.md
@/Users/luca/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/ROADMAP.md
@.planning/STATE.md
@backend/api/endpoints/print.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Update ROADMAP.md Phase 3 and Phase 4</name>
  <files>.planning/ROADMAP.md</files>
  <action>
Update `.planning/ROADMAP.md` with two sets of changes:

**Phase 3 — Correct success criteria to match actual implementation:**

Replace the current Phase 3 success criteria with:
1. `POST /api/print-job` accepts a valid payload, generates a uuid4 job_id in memory (no DB collection), and enqueues an SSE event on the "print-jobs" subtopic; `GET /api/print-jobs/stream` delivers jobs to the print service subscriber
2. The print service subscribes to the SSE stream, sends data over TCP to `printer_host:printer_port`, and POSTs the result back to `/api/print-jobs/{id}/result` which enqueues a "print-result" SSE event
3. The service runs in Docker via `deploy/compose/print.yaml` with `traefik.enable=false` and no inbound port requirements
4. Both ZPL (ASCII-encoded) and PDF (base64-decoded) formats are accepted; TCP errors are classified as `connection_refused`, `timeout`, or `send_error`

Key changes from original: criterion 1 removes "stores a PrintJob DB record" and replaces with "generates a uuid4 job_id in memory (no DB collection)". Criterion 2 adds the "print-result" SSE event detail.

**Phase 4 — Add SSE print-result subscription requirements:**

Update the Phase 4 Goal to:
"Factory operators can print labels directly to any configured printer from the main app print dialog and the warehouse app, with real-time success/error feedback via SSE, replacing all hardcoded ZPL and `/pstprint` dependencies"

Add these requirements to the Phase 4 Requirements list (after existing DIAL-06, before WH-01):
- `SSE-01`: Frontend subscribes to `/notification/print-result` SSE stream after submitting a print job
- `SSE-02`: Frontend filters "print-result" events by `job_id` to match the response to the originating request

Update Phase 4 success criteria — add a new criterion between current #2 and #3:
"3. After submitting a print job, the frontend subscribes to the `/notification/print-result` SSE stream, filters events by the returned `job_id`, and displays a success toast or error message to the user"

Renumber subsequent criteria (old 3->4, old 4->5, old 5->6).

Do NOT change Phase 4 Plans (keep "TBD").
  </action>
  <verify>
    <automated>grep -c "print-result" .planning/ROADMAP.md | xargs test 3 -le</automated>
  </verify>
  <done>
    - Phase 3 success criteria no longer mention PrintJob DB record
    - Phase 3 success criteria mention uuid4 in-memory job_id and "print-result" SSE event
    - Phase 4 requirements include SSE-01 and SSE-02
    - Phase 4 success criteria include SSE stream subscription with job_id filtering
    - Phase 4 has 6 success criteria (was 5)
  </done>
</task>

</tasks>

<verification>
- `grep "PrintJob DB" .planning/ROADMAP.md` returns nothing (removed)
- `grep "print-result" .planning/ROADMAP.md` returns multiple matches in Phase 3 and Phase 4
- `grep "SSE-01" .planning/ROADMAP.md` returns a match in Phase 4 requirements
- `grep "uuid4" .planning/ROADMAP.md` returns a match in Phase 3 success criteria
</verification>

<success_criteria>
ROADMAP.md Phase 3 accurately reflects the stateless (no DB) architecture with SSE-based result delivery. Phase 4 requirements and success criteria explicitly mandate frontend SSE subscription to "print-result" subtopic with job_id filtering for user feedback.
</success_criteria>

<output>
After completion, create `.planning/quick/260319-ios-update-roadmap-phase-4-print-result-sse-/260319-ios-SUMMARY.md`
</output>
