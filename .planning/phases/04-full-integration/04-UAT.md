---
status: resolved
phase: 04-full-integration
source: [04-01-SUMMARY.md, 04-02-SUMMARY.md, 04-03-SUMMARY.md, 04-04-SUMMARY.md]
started: 2026-03-20T10:15:00Z
updated: 2026-03-20T12:00:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Kill any running server/service. Clear ephemeral state (temp DBs, caches, lock files). Start the application from scratch. Server boots without errors, any seed/migration completes, and a primary query (health check, homepage load, or basic API call) returns live data.
result: pass

### 2. Add Printer: Type and Timeout Fields
expected: Open Settings > Printers > Add Printer form. There is a "Type" dropdown with options ZPL and PDF, and a numeric "Timeout (seconds)" field defaulting to 5. Saving creates the printer with those values stored.
result: pass

### 3. Printer Table Shows Type and Timeout
expected: The Printers settings table shows Type and Timeout columns alongside Name, Host, and Port. Existing printers and newly added ones display their type and timeout values in the list.
result: pass

### 4. Send to Printer Button Visibility
expected: Open any print dialog and reach step 3. If your user preferences have a printer configured, a "Send to [printer name]" button appears next to "Download PDF". If no printer is configured in preferences, only the Download PDF button is shown.
result: pass

### 5. Print Spinner and Button Toggle
expected: In step 3 of the print dialog, click "Send to [printer name]". Both the Download PDF and Send to Printer buttons disappear and a centered spinner appears while the job is submitted. After the result arrives (success, error, or timeout), the dialog closes.
result: issue
reported: "after clicking the send to printer button the buttons disappear, the spinner appears, but only for a very short time, then an error notification appears saying 'Maximum call stack exceeded'. No api calls are shown in the inspector."
severity: blocker

### 6. Print Toast Notifications
expected: After clicking Send to Printer, once the print job completes a toast notification appears: green/success on successful print, red/error if the printer returned an error, and a timeout message if no result arrived within the configured timeout window.
result: skipped
reason: Cannot test — print command never reaches the server due to blocker in test 5

### 7. Download PDF Still Works
expected: In step 3 of the print dialog, clicking "Download PDF" still downloads the PDF file as before — the print dialog closes and the browser downloads the file. The send-to-printer flow has no effect on this path.
result: pass

### 8. Warehouse Settings: Template Selectors Visible
expected: Open Main App > Settings > Warehouse. There are two template selectors: "Product Label Template" and "Position Label Template". These selectors are visible regardless of whether Inventory Management is enabled — they appear outside that toggle's conditional section.
result: pass

### 9. Warehouse Printing Uses New Pipeline
expected: In the warehouse app, trigger a label print (e.g., during incoming quantity selection or container creation). The label is generated using the configured template and sent to the print service via /api/print-job. BrowserPrint is no longer involved in this flow.
result: issue
reported: "The print job is failing due to network configuration issues (not a problem in the code). The print-service correctly handles the thing, receiving the event and sending it to the configured printer, which then fails, but in the UI there's no hint at the failure, instead only a success notification is shown that the print job has been sent successfully. Also, the notification is not set with the theme color. Update the configuration so that success uses the theme-green color, warning theme-orange and error theme-red"
severity: major

## Summary

total: 9
passed: 6
issues: 2
pending: 0
skipped: 1

## Gaps

- truth: "Clicking Send to Printer submits a print job via API and shows spinner until result arrives"
  status: resolved
  reason: "User reported: after clicking the send to printer button the buttons disappear, the spinner appears, but only for a very short time, then an error notification appears saying 'Maximum call stack exceeded'. No api calls are shown in the inspector."
  severity: blocker
  test: 5
  root_cause: "PrintDialog.vue line 742 uses btoa(String.fromCharCode(...new Uint8Array(pdfBytes))) — spread operator expands the full PDF byte array (50–500KB) as individual function arguments, exceeding V8's max argument count (~65k). Crash is synchronous before sendToPrintService() fires. Fix: replace with chunked btoa conversion (loop over 8192-byte slices)."
  artifacts:
    - path: "webapps/main/src/components/PrintDialog.vue"
      issue: "line 742: btoa(String.fromCharCode(...new Uint8Array(pdfBytes))) causes RangeError on any real PDF"
    - path: "webapps/main/src/lib/print/index.js"
      issue: "generatePdf() helper at lines 29–50 exists and returns raw bytes correctly but is not imported/used by PrintDialog.vue"
  missing:
    - "Replace spread-based btoa with chunked conversion (8192 bytes per slice)"
    - "Optionally import generatePdf() from lib/print/index.js to deduplicate generate() call"
  debug_session: ".planning/debug/print-dialog-stack-overflow.md"

- truth: "Warehouse print notifications reflect actual print outcome (error shown on failure); notifications use theme colors (theme-green/theme-orange/theme-red)"
  status: resolved
  reason: "User reported: The print-service correctly handles the thing, receiving the event and sending it to the configured printer, which then fails, but in the UI there's no hint at the failure, instead only a success notification is shown. Also, the notification is not set with the theme color. Success should use theme-green, warning theme-orange, error theme-red."
  severity: major
  test: 9
  root_cause: "Two separate bugs. (1) printProductLabel/printPositionLabel fire success toast immediately after POST /print-job returns job_id (enqueue confirmation), never calling waitForPrintResult() to get the actual printer outcome from the SSE stream. (2) All 8 Notify.create calls use Quasar built-in type:'positive'/'negative' instead of the app pattern color:'theme-green'/'theme-red'/'theme-orange'."
  artifacts:
    - path: "webapps/warehouse/src/lib/print/index.js"
      issue: "lines 134–135 and 172–174: submitPrintJob result discarded, positive toast fired unconditionally with no SSE result check"
    - path: "webapps/warehouse/src/lib/print/index.js"
      issue: "all 8 Notify.create calls use type:'positive'/'negative' instead of color:'theme-*'"
    - path: "webapps/main/src/lib/print/index.js"
      issue: "reference: waitForPrintResult() at lines 78–104 is what warehouse lib is missing"
    - path: "webapps/main/src/components/PrintDialog.vue"
      issue: "reference: lines 746–757 show correct branching on result.ok / result.error === 'timeout'"
  missing:
    - "Call waitForPrintResult(job_id, timeoutMs) after submitPrintJob in printProductLabel and printPositionLabel"
    - "Branch on result.ok (success), result.error === 'timeout' (warning), other errors (failure)"
    - "Replace all type:'positive' with color:'theme-green' and type:'negative' with color:'theme-red'; use color:'theme-orange' for timeout"
  debug_session: ".planning/debug/warehouse-print-success-on-failure.md"
