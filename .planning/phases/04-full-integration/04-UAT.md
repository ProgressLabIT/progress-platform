---
status: complete
phase: 04-full-integration
source: [04-01-SUMMARY.md, 04-02-SUMMARY.md, 04-03-SUMMARY.md, 04-04-SUMMARY.md]
started: 2026-03-20T10:15:00Z
updated: 2026-03-20T10:35:00Z
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
  status: failed
  reason: "User reported: after clicking the send to printer button the buttons disappear, the spinner appears, but only for a very short time, then an error notification appears saying 'Maximum call stack exceeded'. No api calls are shown in the inspector."
  severity: blocker
  test: 5
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""

- truth: "Warehouse print notifications reflect actual print outcome (error shown on failure); notifications use theme colors (theme-green/theme-orange/theme-red)"
  status: failed
  reason: "User reported: The print-service correctly handles the thing, receiving the event and sending it to the configured printer, which then fails, but in the UI there's no hint at the failure, instead only a success notification is shown. Also, the notification is not set with the theme color. Success should use theme-green, warning theme-orange, error theme-red."
  severity: major
  test: 9
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""
