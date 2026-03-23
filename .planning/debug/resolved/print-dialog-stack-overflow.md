---
status: resolved
trigger: "Clicking 'Send to [printer name]' causes immediate 'Maximum call stack exceeded' error. No API calls are made."
created: 2026-03-20T00:00:00Z
updated: 2026-03-20T00:00:00Z
---

## Current Focus

hypothesis: `sendToPrinter()` calls `generate()` (from @pdfme/generator) with a `Uint8Array` result, which is then spread via `new Uint8Array(pdfBytes)` — but the crash occurs *before* that point. The actual cause is that `customDataMatrix.js` calls `document.createElement('canvas')` inside its `pdf` render function during the pdfme `generate()` call — but this is not the stack overflow. The real cause is identified below.
test: Trace the call path from `sendToPrinter` → `generate` → plugin `pdf` callbacks → `canvasToPngBytes` → `b64toUint8Array`
next_action: DIAGNOSED — return root cause

## Symptoms

expected: Clicking "Send to [printer name]" should call `sendToPrintService()` and submit a print job via POST to `print-job`
actual: Immediate "Maximum call stack exceeded" error. Spinner briefly visible. Zero API calls in network inspector.
errors: Maximum call stack exceeded (RangeError / stack overflow)
reproduction: Click "Send to [printer name]" on step 2 (preview) of PrintDialog when a non-ZPL printer is selected
started: After pdfme v5 upgrade (branch 536/pdfme5-upgrade)

## Eliminated

- hypothesis: Circular reactive watcher on `isPrinting` ref
  evidence: `isPrinting` is a plain `ref(false)` set once at line 711 and cleared at line 764. No watchers reference it. No computed depends on it.
  timestamp: 2026-03-20

- hypothesis: Infinite recursion in `sendToPrinter` itself calling itself
  evidence: `sendToPrinter` is a plain async function. No self-reference. Calls `prepareInputs`, `generateZpl` (ZPL path), or `generate` (PDF path) and `sendToPrintService`. None call back to `sendToPrinter`.
  timestamp: 2026-03-20

- hypothesis: `selectedPrinter` computed property causes reactive loop
  evidence: `selectedPrinter` reads from `store.state.session.user.preferences.printer` and `config.printers`. It is read-only (no setter). No side effects. Cannot cause a reactive loop.
  timestamp: 2026-03-20

- hypothesis: `generateZpl` is recursive
  evidence: `generateZpl` in `zpl.js` is a pure function. `schemasToV5` → `normalizePageSchema` → `renderPage` → `renderField` → individual render functions. No recursion possible.
  timestamp: 2026-03-20

## Evidence

- timestamp: 2026-03-20
  checked: PrintDialog.vue sendToPrinter() PDF path (lines 726-743)
  found: For non-ZPL printers, `sendToPrinter` calls `generate({ template: cleanTemplate, inputs, plugins: pdfmePlugins })` then converts result with `btoa(String.fromCharCode(...new Uint8Array(pdfBytes)))`. The spread syntax `...new Uint8Array(pdfBytes)` is called via `String.fromCharCode(...args)`.
  implication: `String.fromCharCode(...new Uint8Array(largeBuffer))` causes "Maximum call stack exceeded" when the PDF byte array is large — the spread operator `...` passes every byte as a function argument, exhausting the call stack. This is a well-known JavaScript gotcha: `Function.prototype.apply` and spread have a maximum argument count tied to the call stack size.

- timestamp: 2026-03-20
  checked: `index.js` `sendToPrintService` and `waitForPrintResult`
  found: These are straightforward async functions that only run AFTER `generate()` completes. They are not involved in the crash.
  implication: The crash happens inside `sendToPrinter()` at the btoa line, before any network call is made — consistent with the symptom "zero API calls".

- timestamp: 2026-03-20
  checked: `goToPreview()` in PrintDialog.vue (lines 696-700)
  found: `goToPreview` also calls `generate(...)` but stores the result in `previewSrc.value` without the btoa spread conversion. It does NOT call `String.fromCharCode(...new Uint8Array(...))`.
  implication: The preview step works fine. The crash is specific to `sendToPrinter`'s btoa conversion, confirming the spread is the culprit.

- timestamp: 2026-03-20
  checked: index.js `generatePdf` helper (lines 29-50)
  found: `index.js` exports a `generatePdf` helper that correctly returns the raw `Uint8Array` from `generate()` without any btoa conversion. `PrintDialog.vue` does NOT use this helper in `sendToPrinter` — it duplicates the generate logic inline and adds the broken btoa spread.
  implication: The fix already exists as `generatePdf` in `index.js`; it is just not being used.

## Resolution

root_cause: >
  In `PrintDialog.vue`, `sendToPrinter()` at line 742:
    `data = btoa(String.fromCharCode(...new Uint8Array(pdfBytes)));`
  The spread operator `...new Uint8Array(pdfBytes)` passes the entire PDF byte array
  as individual arguments to `String.fromCharCode`. A generated PDF easily exceeds
  the V8 / JavaScriptCore maximum argument count (~65,000–125,000 args), which
  exhausts the call stack and throws "Maximum call stack exceeded" immediately —
  before any network call is made. This is 100% consistent with the observed
  symptoms: spinner appears (isPrinting = true), crash fires, no API calls.

fix: empty — diagnosis only (goal: find_root_cause_only)
verification: empty
files_changed: []
