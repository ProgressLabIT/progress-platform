---
status: resolved
trigger: "warehouse print job shows success on printer failure; notifications don't use theme colors"
created: 2026-03-20T00:00:00Z
updated: 2026-03-20T00:00:00Z
---

## Current Focus

hypothesis: confirmed — two independent bugs identified with strong evidence
test: code trace complete
expecting: n/a (diagnosis mode)
next_action: return diagnosis to caller

## Symptoms

expected: When the printer itself fails, the warehouse app should show an error notification. Notifications should use theme-green, theme-orange, theme-red color keys.
actual: Printer failure shows a success ("positive") notification. Notifications use type:'positive'/'negative' instead of color:'theme-*'.
errors: (none — silent wrong behavior)
reproduction: Send a print job from the warehouse app to a printer that is offline or rejects the connection. UI shows green success toast.
started: unknown — present in current codebase

## Eliminated

- hypothesis: The SSE result payload doesn't carry a `success` field
  evidence: PrintJobResult model (backend/api/models/print_job.py) has `ok: bool`. The result endpoint posts {ok, error, detail} into the SSE stream. The field IS present and named `ok`.
  timestamp: 2026-03-20

- hypothesis: The theme color names aren't defined in the warehouse app
  evidence: theme.scss in both apps generates .bg-theme-green/.bg-theme-red/.bg-theme-orange CSS classes. warehouse app already uses color:'theme-green' etc. in many other Notify.create calls. The print lib is uniquely out of step.
  timestamp: 2026-03-20

## Evidence

- timestamp: 2026-03-20
  checked: webapps/warehouse/src/lib/print/index.js lines 134-135 and 172-174
  found: After `await submitPrintJob(zpl, printer)` the code immediately calls `Notify.create({ type: 'positive', ... })` without inspecting the API response at all. submitPrintJob returns the raw axios response which contains `{ job_id }` — a job ID, not a printer result.
  implication: The warehouse print functions fire-and-forget. They post a job to the API and show success as soon as the HTTP 200 comes back from the API (job enqueued). The print service then processes the job asynchronously; its result is posted back via SSE to /print-jobs/{job_id}/result. The warehouse code never subscribes to that SSE result event and never checks `result.ok`. Any printer failure is silently ignored.

- timestamp: 2026-03-20
  checked: webapps/main/src/lib/print/index.js — sendToPrintService() + waitForPrintResult()
  found: The main app's print lib has a two-step flow: (1) POST /print-job to get `job_id`, (2) open EventSource on /notification/print-result and wait for the event matching `job_id`, then resolve with `{ ok, error, detail }`. PrintDialog.vue lines 746-757 then checks `result.ok` and branches to success / timeout / error notifications accordingly.
  implication: The main app correctly handles printer results. The warehouse app has no equivalent of `waitForPrintResult`.

- timestamp: 2026-03-20
  checked: webapps/warehouse/src/lib/print/index.js Notify.create calls (lines 114, 120, 126, 135, 152, 159, 165, 174)
  found: All Notify.create calls use `type: 'positive'` or `type: 'negative'`. No call uses `color: 'theme-*'`. The early-exit guards (no template, no printer) use `type: 'negative'`. The success notification uses `type: 'positive'`. None use color:'theme-green', color:'theme-red', or color:'theme-orange'.
  implication: Quasar's `type:'positive'` and `type:'negative'` use its built-in $positive/$negative colors (#21ba45 and #c10015 from quasar.variables.scss), not the app's custom theme-green/theme-red colors. The visual result is a differently-colored notification than every other notification in the warehouse app.

- timestamp: 2026-03-20
  checked: webapps/warehouse/src/composables/bulkEvent.js, event.js, stores/counting.js, shipment.js, and component CountingEmptyPositionCard.vue, CountingQuantityCard.vue, CountingSerialsCard.vue
  found: All of these use `color: 'theme-green'`, `color: 'theme-red'`, `color: 'theme-orange'` in Notify.create calls. The pattern is established and working.
  implication: The warehouse print lib is the only place using Quasar built-in type strings rather than theme color keys.

- timestamp: 2026-03-20
  checked: backend/api/endpoints/print.py — /print-jobs/{job_id}/result endpoint (lines 219-230)
  found: The result endpoint receives PrintJobResult (ok, error, detail) from the print service and re-emits it as SSE with subtopic="print-result" including job_id, ok, error, detail.
  implication: The SSE protocol is correct. The result IS available. The warehouse frontend just never listens for it.

- timestamp: 2026-03-20
  checked: backend/api/models/print_job.py
  found: PrintJobResult has `ok: bool`, `error: str | None` (values: connection_refused | timeout | send_error), `detail: str | None`.
  implication: Three outcomes need handling: ok=True (success), ok=False with error='timeout' (timeout), ok=False with other error (printer error).

## Resolution

root_cause: The warehouse print functions (`printProductLabel`, `printPositionLabel` in webapps/warehouse/src/lib/print/index.js) call `submitPrintJob` and immediately show a positive notification when the HTTP POST to `/print-job` succeeds (202/200 — job enqueued). They never call any equivalent of the main app's `waitForPrintResult()`, so the printer's actual success or failure (delivered asynchronously via SSE) is never observed. The positive notification is shown unconditionally for any non-thrown request.

root_cause_colors: The same two functions use Quasar's built-in `type:'positive'`/`type:'negative'` strings instead of the app's custom `color:'theme-green'`/`color:'theme-red'`/`color:'theme-orange'` pattern that is used consistently everywhere else in the warehouse app. The theme color CSS classes (.bg-theme-green etc.) are generated by theme.scss and ARE available; the print lib simply doesn't use them.

fix: (diagnosis only — not implemented)
verification: (diagnosis only)
files_changed: []
