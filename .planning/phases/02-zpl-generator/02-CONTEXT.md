# Phase 2: ZPL Generator - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Pure-JS transpiler: `generateZpl(template, inputs, { dpi, quantity })` converts pdfme template schemas + resolved inputs into a valid, printer-ready ZPL string. No UI, no backend changes, no print dialog wiring — that is Phase 4. This phase delivers the generation function and its tests only.

</domain>

<decisions>
## Implementation Decisions

### Multi-page templates
- All pages are always printed — no page selection
- `generateZpl()` returns a single ZPL string with all pages as concatenated `^XA...^XZ` blocks (standard ZPL multi-label format)
- The print service sends the whole string in one TCP write; no caller-side iteration needed
- `quantity` (`^PQ`) applies per page/label block

### Text field fidelity
- Proportional font size mapping: pdfme `fontSize` (pt) → ZPL dots at the configured DPI
- Alignment mapped: pdfme `alignment` (left/center/right) → `^FB` justification (`L`/`C`/`R`)
- Field position (`x`, `y` in mm) → `^FO` in dots
- Goal is designer-intent fidelity, not pixel-perfect rendering

### Field block width (^FB)
- Use each field's own `width` property from the pdfme schema (in mm), converted to dots
- No label-level basePdf parsing needed
- `^FB{fieldWidthDots},1,0,{alignment},0` for text fields — single line, field-width constraint

### Module placement
- New file: `webapps/main/src/lib/print/zpl.js`
- `schemasToV5()` and `normalizePageSchema()` exported from `index.js` so `zpl.js` can import them
- Mirrors the `templateResolver.js` pattern — pure logic module, no framework deps

### TDD approach
- Same RED → GREEN → commit pattern as Phase 1
- Tests in `webapps/main/src/lib/print/zpl.test.js`
- Vitest already installed and configured

### Claude's Discretion
- Exact `^A0N` height/width calculation formula (pt → dots conversion)
- Max line count for `^FB` (default 1 or auto)
- Barcode height derivation from field `height` in mm
- Whether to handle `template_string` / `linked_text` field types the same as base `text`
- Exact ZPL command parameters for each barcode type (module size, error correction defaults)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `schemasToV5()` / `normalizePageSchema()` in `index.js`: Schema normalization to flat array of field objects — export these for `zpl.js` to reuse
- `templateResolver.js`: Pattern for a pure ES module with no framework deps — follow the same structure
- `templateResolver.test.js`: Existing vitest test file — follow same test structure for `zpl.test.js`
- `linkedBarcodes.js` `createLinkedBarcodes()`: Lists all supported barcode types (`qrcode`, `ean13`, `code39`, `code128`, `gs1datamatrix`, plus others) — reference for type detection

### Established Patterns
- pdfme schema fields have: `name`, `type`, `position` (`{x, y}` in mm), `width` (mm), `height` (mm), `content` (value), `fontSize` (pt), `alignment`
- `inputs` is an array of objects (one per page) keyed by field name — `inputs[pageIndex][fieldName]` is the resolved string value
- Image field types to skip: `image`, `linkedImage` (and any `type` containing "image")
- `gs1datamatrix` field type: in `generatePdf()` there's a migration step that falls back to `datamatrix` when value isn't valid GS1 format — similar defensive handling may be needed in ZPL

### Integration Points
- `index.js`: Export `schemasToV5` and `normalizePageSchema` from here
- `zpl.js`: New file, exports `generateZpl(template, inputs, { dpi, quantity })`
- Phase 4 will import `generateZpl` from `lib/print/zpl.js` for the print dialog integration

</code_context>

<specifics>
## Specific Ideas

- ZPL field type mapping (from requirements):
  - `text` / `template_string` → `^FO^A0N^FB^FD^FS`
  - `qrcode` → `^BQN`
  - `code128` → `^BCN`
  - `code39` → `^B3N`
  - `ean13` → `^BEN`
  - `gs1datamatrix` → `^BXN`
- Image fields: `console.warn()` + skip (do not throw)
- Output envelope: `^XA ... ^PQ{quantity} ^XZ` per page, all pages concatenated

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-zpl-generator*
*Context gathered: 2026-03-18*
