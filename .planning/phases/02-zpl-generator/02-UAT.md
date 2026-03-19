---
status: complete
phase: 02-zpl-generator
source: 02-01-SUMMARY.md
started: 2026-03-19T00:00:00Z
updated: 2026-03-19T00:01:00Z
---

## Current Test

<!-- OVERWRITE each test - shows where we are -->

[testing complete]

## Tests

### 1. Vitest Suite Passes
expected: Run `yarn vitest run src/lib/print/zpl.test.js` — all 28 tests pass, no failures.
result: pass

### 2. No Regression in Full Suite
expected: Run `yarn vitest run` — 38/38 tests pass (templateResolver suite unaffected by new zpl.js).
result: pass

### 3. generateZpl Produces Correct ZPL Envelope
expected: Calling `generateZpl(template, inputs, { dpi: 203, quantity: 2 })` produces ZPL that starts with `^XA`, ends with `^XZ`, and contains `^PQ2` for quantity.
result: pass

### 4. Text Field ZPL Command
expected: A text field renders as `^FO{x},{y}^A0N,{h},{h}^FB{w},1,0,{align},0^FD{value}^FS` — position, font size from height, and field box width all correctly converted from mm to dots.
result: pass

### 5. Barcode Fields (all 5 types)
expected: QR (`^BQN`), Code128 (`^BCN`), Code39 (`^B3N`), EAN (`^BEN`), DataMatrix (`^BXN`) each produce the correct ZPL barcode command. Tests cover all 5 and pass.
result: pass

### 6. Image Fields Silently Skipped
expected: A template with an image field produces ZPL with no image command (skipped), and `console.warn` is called. No error thrown.
result: pass

### 7. Multi-Page Template
expected: A template with 2 pages produces 2 concatenated `^XA...^XZ` blocks in the output — one per page.
result: pass

## Summary

total: 7
passed: 7
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]
