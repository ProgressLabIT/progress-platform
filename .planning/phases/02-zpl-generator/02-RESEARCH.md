# Phase 2: ZPL Generator - Research

**Researched:** 2026-03-18
**Domain:** ZPL II label generation, pure-JS transpiler, coordinate conversion
**Confidence:** HIGH

## Summary

Phase 2 is a pure-JS transpiler: `generateZpl(template, inputs, { dpi, quantity })` reads pdfme schema
fields (position in mm, width/height in mm, fontSize in pt) and emits valid ZPL II strings. The work
is self-contained — no UI, no backend, no new dependencies. All the building blocks exist in the
codebase: `schemasToV5()` and `normalizePageSchema()` normalize templates, and the field type list
from `linkedBarcodes.js` defines the supported set.

ZPL II coordinate units are "dots". The universal conversion is: `dots = mm * (dpi / 25.4)`. At 203
dpi this is ~8 dots/mm, at 300 dpi it is ~11.8 dots/mm. Font point-to-dot conversion follows
typography convention: `dots = pt * (dpi / 72)`. Both formulas are simple multiplications — no
external library needed.

Each barcode type maps directly to a ZPL command family (`^BC`, `^B3`, `^BE`, `^BX`, `^BQ`), each
wrapped in `^FO...^FD...^FS`. Text fields use `^A0N` (scalable Font 0, no rotation) + `^FB` for
width/alignment. The output structure is one `^XA...^PQ{quantity}^XZ` block per page, all
blocks concatenated.

**Primary recommendation:** Implement `zpl.js` as a plain ES module mirroring the
`templateResolver.js` pattern. Use field-level `width` and `height` (mm → dots) for barcode sizing.
No external ZPL library needed.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Multi-page output:** All pages always printed; `generateZpl()` returns one ZPL string, all
  pages as concatenated `^XA...^XZ` blocks. `^PQ{quantity}` applies per block.
- **Text field fidelity:** Proportional font-size mapping (pt → dots at DPI); pdfme `alignment`
  → `^FB` justification (`L`/`C`/`R`); position (`x`,`y` in mm) → `^FO` in dots. Goal is
  designer-intent fidelity, not pixel-perfect rendering.
- **Field block width:** Use each field's own `width` (mm → dots) — no basePdf parsing.
  `^FB{fieldWidthDots},1,0,{alignment},0` for text fields (single line, field-width constrained).
- **Module placement:** `webapps/main/src/lib/print/zpl.js`; `schemasToV5()` and
  `normalizePageSchema()` exported from `index.js` so `zpl.js` can import them.
- **TDD:** RED → GREEN → commit; tests in `zpl.test.js`; Vitest already installed.
- **Field type mapping:**
  - `text` / `template_string` → `^FO^A0N^FB^FD^FS`
  - `qrcode` → `^BQN`
  - `code128` → `^BCN`
  - `code39` → `^B3N`
  - `ean13` → `^BEN`
  - `gs1datamatrix` → `^BXN`
- **Image fields:** `console.warn()` + skip (do not throw).

### Claude's Discretion

- Exact `^A0N` height/width calculation formula (pt → dots conversion).
- Max line count for `^FB` (default 1 or auto).
- Barcode height derivation from field `height` in mm.
- Whether to handle `template_string` / `linked_text` field types the same as base `text`.
- Exact ZPL command parameters for each barcode type (module size, error correction defaults).

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ZPL-01 | `generateZpl(template, inputs, { dpi, quantity })` transpiles a pdfme template + resolved inputs into a valid ZPL string | Core function signature; mm→dots formula; `^XA…^PQ…^XZ` envelope; multi-page concat |
| ZPL-02 | Coordinate mapping: pdfme mm → ZPL dots at configurable DPI (default 203) | Formula: `dots = mm * (dpi / 25.4)`; font dots = `pt * (dpi / 72)` |
| ZPL-03 | Supported field types: `text`, `qrcode`, `code128`, `code39`, `ean13`, `gs1datamatrix` | Command syntax researched for all six types; see Code Examples section |
| ZPL-04 | Image fields log a console warning and are skipped | Pattern: `if (type.includes('image')) { console.warn(...); continue; }` |
| ZPL-05 | Output wraps fields with `^XA ... ^PQ{quantity} ^XZ` | Envelope confirmed in ZPL II spec; `^PQ` syntax: `^PQ{q}` minimum |
</phase_requirements>

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Vitest | ^4.1.0 (installed) | Unit tests | Already configured in project |
| ES modules (plain JS) | — | `zpl.js` implementation | Matches `templateResolver.js` pattern; no new deps |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| None — no external ZPL lib | — | — | ZPL generation is simple string concatenation; no library adds value over hand-crafted strings |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Hand-crafted ZPL strings | `jszpl`, `simple-zpl2` | Libraries add abstraction but require a dep, version management, and don't cover all required barcode types cleanly. String templates are transparent and testable. |

**Installation:** No new packages needed.

---

## Architecture Patterns

### Recommended Project Structure

```
webapps/main/src/lib/print/
├── index.js              # Export schemasToV5, normalizePageSchema (already exists; needs exports added)
├── zpl.js                # NEW: exports generateZpl()
├── zpl.test.js           # NEW: Vitest test file
├── templateResolver.js   # Existing — model for pure-module style
└── plugins/              # Unchanged
```

### Pattern 1: Pure ES Module (no framework deps)

**What:** `zpl.js` exports only `generateZpl`. No Vue, no Quasar, no store imports.
**When to use:** Always — mirrors `templateResolver.js` exactly.
**Example:**
```javascript
// webapps/main/src/lib/print/zpl.js
// Source: templateResolver.js pattern (same codebase)

import { schemasToV5 } from './index.js';

const DEFAULT_DPI = 203;

export function generateZpl(template, inputs, { dpi = DEFAULT_DPI, quantity = 1 } = {}) {
  const pages = schemasToV5(template.schemas);
  return pages.map((fields, pageIndex) =>
    renderPage(fields, inputs?.[pageIndex] ?? {}, dpi, quantity)
  ).join('\n');
}
```

### Pattern 2: Per-field dispatch with type guard

**What:** Central switch/if-else on `field.type` dispatching to renderer functions.
**When to use:** For each field in a normalized page schema.
**Example:**
```javascript
// Source: linkedBarcodes.js type list (same codebase)
const IMAGE_TYPES = ['image', 'linkedImage'];

function renderField(field, value, dpi) {
  if (IMAGE_TYPES.some(t => field.type.toLowerCase().includes(t.toLowerCase()))) {
    console.warn(`[generateZpl] Image field "${field.name}" skipped (type: ${field.type})`);
    return '';
  }
  switch (field.type) {
    case 'text':
    case 'template_string':
      return renderText(field, value, dpi);
    case 'qrcode':
      return renderQr(field, value, dpi);
    case 'code128':
      return renderCode128(field, value, dpi);
    case 'code39':
      return renderCode39(field, value, dpi);
    case 'ean13':
      return renderEan13(field, value, dpi);
    case 'gs1datamatrix':
      return renderDataMatrix(field, value, dpi);
    default:
      console.warn(`[generateZpl] Unknown field type "${field.type}" skipped`);
      return '';
  }
}
```

### Pattern 3: Coordinate helper functions

**What:** Single source of truth for mm→dots and pt→dots conversions.
**When to use:** All positioning and sizing.
**Example:**
```javascript
// Source: ZPL II spec, 203 dpi = 8 dpmm (labelary.com, simple-zpl2 docs)
function mmToDots(mm, dpi) { return Math.round(mm * dpi / 25.4); }
function ptToDots(pt, dpi) { return Math.round(pt * dpi / 72); }
```

### Anti-Patterns to Avoid

- **Parsing `basePdf`:** Not needed — field widths/heights are in the schema. CONTEXT.md explicitly bans this.
- **Throwing on unsupported types:** Log warning and return `''` so generation continues.
- **Hardcoding 203 dpi:** Always pass `dpi` through to conversion helpers.
- **Using `inputs[0]` for all pages:** Use `inputs[pageIndex]` — each page has its own input object.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ZPL string formatting | Custom template DSL | Plain template literals | ZPL is simple concatenation; a DSL adds complexity without benefit |
| mm↔dots math | External unit-conversion lib | Two one-liner functions | Formula is `mm * dpi / 25.4`; no edge cases |
| Barcode validation | Custom regex validators | None (pass value through) | ZPL printer handles invalid data; generator's job is transpilation only |

**Key insight:** ZPL generation for this use case is string concatenation of ~10 fixed command
templates. External ZPL libraries are heavier than the problem.

---

## Common Pitfalls

### Pitfall 1: QR Code data prefix requirement

**What goes wrong:** `^FD{data}^FS` prints garbled QR if the `MA,` prefix is omitted.
**Why it happens:** ZPL `^BQ` requires `^FD` data to start with switches in the format
`{mixed-mode-flag}{error-correction},{data-mode},{data}`. Omitting the prefix yields undefined behavior.
**How to avoid:** Always emit `^FDMA,{value}^FS` (manual input, automatic character selection).
**Warning signs:** QR code prints but scanner cannot read it.

```javascript
// Correct QR field data format
// Source: simple-zpl2 docs fd_switches default 'M,A'; Zebra ZPL II pg vol 2
function renderQr(field, value, dpi) {
  const x = mmToDots(field.position.x, dpi);
  const y = mmToDots(field.position.y, dpi);
  const moduleSize = Math.max(2, Math.round(mmToDots(field.height, dpi) / 22));
  // ^BQN,2,{moduleSize} — model 2 (enhanced), magnification derived from field height
  return `^FO${x},${y}^BQN,2,${moduleSize}^FDMA,${value}^FS`;
}
```

### Pitfall 2: ^FB width of zero silently suppresses text

**What goes wrong:** Text field prints nothing.
**Why it happens:** If `^FBa` parameter `a` (width) is 0 or less than font width, text does not print.
This can happen if `field.width` is missing/null and falls back to 0.
**How to avoid:** Guard with `Math.max(1, mmToDots(field.width, dpi))`. Default to label width if width is absent.
**Warning signs:** Text field produces no output with no error.

### Pitfall 3: EAN-13 requires exactly 12 digits (check digit auto-added)

**What goes wrong:** EAN-13 barcode prints incorrectly or errors.
**Why it happens:** ZPL `^BE` expects 12 numeric digits; the 13th (check digit) is computed by the printer. Passing 13 digits or non-numeric values corrupts the barcode.
**How to avoid:** The `generateZpl` function should pass values through as-is (caller is responsible for valid data). Document this constraint in the function's JSDoc.
**Warning signs:** Barcode renders with wrong data or fails to scan.

### Pitfall 4: schemasToV5 / normalizePageSchema not yet exported from index.js

**What goes wrong:** `import { schemasToV5 } from './index.js'` in `zpl.js` throws "not exported".
**Why it happens:** Currently `index.js` defines both functions but does not export them (they are used internally by `generatePdf`).
**How to avoid:** Wave 0 task must add `export` to both functions in `index.js`. This is explicitly called out in CONTEXT.md.
**Warning signs:** Import error at module load time.

### Pitfall 5: GS1 DataMatrix value may need FNC1 prefix

**What goes wrong:** GS1 DataMatrix barcode is technically invalid (not GS1-128 compliant).
**Why it happens:** GS1 DataMatrix encodes Application Identifiers; the printer needs `>8` FNC1 escape to signal GS1 encoding. Without it, the code scans but fails GS1 validation.
**How to avoid:** This is discretionary per CONTEXT.md. Research `^BX` format_id=6 (GS1) vs plain DataMatrix. Safe default: pass value through; document the GS1 encoding requirement.
**Warning signs:** Barcode scans as raw data rather than structured GS1 AIs.

---

## Code Examples

Verified patterns from official ZPL II docs and labelary.com:

### ZPL Label Envelope (ZPL-05)

```javascript
// Source: Zebra ZPL II Programming Guide (labelary.com)
function renderPage(fields, inputValues, dpi, quantity) {
  const fieldLines = fields.map(f => renderField(f, inputValues[f.name] ?? '', dpi)).filter(Boolean);
  return `^XA\n${fieldLines.join('\n')}\n^PQ${quantity}\n^XZ`;
}
```

### Coordinate Conversion (ZPL-02)

```javascript
// Source: simple-zpl2 docs; labelary.com (203 dpi = 8 dpmm)
// 1 inch = 25.4 mm; 1 point = 1/72 inch
function mmToDots(mm, dpi) { return Math.round(mm * dpi / 25.4); }
function ptToDots(pt, dpi) { return Math.round(pt * dpi / 72); }
```

### Text Field with ^A0N + ^FB (ZPL-03 text)

```javascript
// Source: Zebra ZPL II pg; ^FB docs at docs.zebra.com/us/en/printers/software/zpl-pg/c-zpl-zpl-commands/r-zpl-fb.html
// ^A0N,{height},{width} — Font 0, Normal orientation, height and width in dots
// ^FB{widthDots},{maxLines},{lineSpacing},{justification},{hangIndent}
// Alignment map: pdfme uses 'left'|'center'|'right'; ZPL uses 'L'|'C'|'R'
const ALIGN_MAP = { left: 'L', center: 'C', right: 'R' };

function renderText(field, value, dpi) {
  const x = mmToDots(field.position.x, dpi);
  const y = mmToDots(field.position.y, dpi);
  const fontH = ptToDots(field.fontSize ?? 10, dpi);
  const fieldW = Math.max(1, mmToDots(field.width ?? 50, dpi));
  const align = ALIGN_MAP[field.alignment] ?? 'L';
  // Width parameter to ^A0N can be omitted (defaults to match height); supply it for explicit control
  return `^FO${x},${y}^A0N,${fontH},${fontH}^FB${fieldW},1,0,${align},0^FD${value}^FS`;
}
```

### Code 128 Barcode (ZPL-03 code128)

```javascript
// Source: Zebra ^BC docs; simple-zpl2 Code128_Barcode
// ^BCN,{height},Y,N,N — Normal rotation, height in dots, print HRI below, no text above, no UCC
function renderCode128(field, value, dpi) {
  const x = mmToDots(field.position.x, dpi);
  const y = mmToDots(field.position.y, dpi);
  const h = mmToDots(field.height ?? 10, dpi);
  return `^FO${x},${y}^BCN,${h},Y,N,N^FD${value}^FS`;
}
```

### Code 39 Barcode (ZPL-03 code39)

```javascript
// Source: Zebra ^B3 docs; ^B3o,e,h,f,g — orientation, checkDigit, height, printText, textAbove
function renderCode39(field, value, dpi) {
  const x = mmToDots(field.position.x, dpi);
  const y = mmToDots(field.position.y, dpi);
  const h = mmToDots(field.height ?? 10, dpi);
  return `^FO${x},${y}^B3N,N,${h},Y,N^FD${value}^FS`;
}
```

### EAN-13 Barcode (ZPL-03 ean13)

```javascript
// Source: Zebra ^BE docs; simple-zpl2 EAN13_Barcode; expects 12 numeric digits
// ^BEo,h,f,g,e — orientation, height, printText, textAbove, checkDigit(reserved)
function renderEan13(field, value, dpi) {
  const x = mmToDots(field.position.x, dpi);
  const y = mmToDots(field.position.y, dpi);
  const h = mmToDots(field.height ?? 10, dpi);
  return `^FO${x},${y}^BEN,${h},Y,N^FD${value}^FS`;
}
```

### GS1 DataMatrix (ZPL-03 gs1datamatrix)

```javascript
// Source: Zebra ^BX docs; simple-zpl2 DataMatrix_Barcode
// ^BXN,{height},200 — Normal rotation, cell height in dots, quality 200 (ECC 200 = standard DataMatrix)
// format_id omitted (default); aspect_ratio=1 (square)
function renderDataMatrix(field, value, dpi) {
  const x = mmToDots(field.position.x, dpi);
  const y = mmToDots(field.position.y, dpi);
  const cellSize = Math.max(2, mmToDots(field.height ?? 8, dpi) / 22);
  const h = Math.max(2, Math.round(cellSize));
  return `^FO${x},${y}^BXN,${h},200^FD${value}^FS`;
}
```

### QR Code (ZPL-03 qrcode)

```javascript
// Source: simple-zpl2 QR_Barcode; ZPL II pg QR section
// ^BQN,2,{magnification} — Normal, model 2 (enhanced), magnification 1-10
// ^FD data must start with switches: MA, = manual input, automatic char mode
function renderQr(field, value, dpi) {
  const x = mmToDots(field.position.x, dpi);
  const y = mmToDots(field.position.y, dpi);
  // Derive magnification from field height: each QR cell is magnification dots
  const mag = Math.max(1, Math.min(10, Math.round(mmToDots(field.height ?? 20, dpi) / 22)));
  return `^FO${x},${y}^BQN,2,${mag}^FDMA,${value}^FS`;
}
```

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Vitest ^4.1.0 |
| Config file | `webapps/main/vitest.config.js` |
| Quick run command | `cd webapps/main && yarn vitest run src/lib/print/zpl.test.js` |
| Full suite command | `cd webapps/main && yarn vitest run` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ZPL-01 | `generateZpl()` returns string starting with `^XA` and ending with `^XZ` | unit | `yarn vitest run src/lib/print/zpl.test.js` | ❌ Wave 0 |
| ZPL-01 | Multi-page template produces two `^XA...^XZ` blocks | unit | same | ❌ Wave 0 |
| ZPL-01 | `^PQ{quantity}` appears before `^XZ` | unit | same | ❌ Wave 0 |
| ZPL-02 | mm→dots at 203 dpi: `mmToDots(25.4, 203) === 203` | unit | same | ❌ Wave 0 |
| ZPL-02 | mm→dots at 300 dpi: `mmToDots(25.4, 300) === 300` | unit | same | ❌ Wave 0 |
| ZPL-02 | pt→dots at 203 dpi: `ptToDots(72, 203) === 203` | unit | same | ❌ Wave 0 |
| ZPL-03 | Text field produces `^A0N` + `^FB` + `^FD{value}^FS` | unit | same | ❌ Wave 0 |
| ZPL-03 | QR code field produces `^BQN` with `^FDMA,{value}^FS` | unit | same | ❌ Wave 0 |
| ZPL-03 | Code128 field produces `^BCN,{h},Y,N,N` | unit | same | ❌ Wave 0 |
| ZPL-03 | Code39 field produces `^B3N,N,{h},Y,N` | unit | same | ❌ Wave 0 |
| ZPL-03 | EAN-13 field produces `^BEN` | unit | same | ❌ Wave 0 |
| ZPL-03 | GS1 DataMatrix field produces `^BXN` | unit | same | ❌ Wave 0 |
| ZPL-04 | Image field type: console.warn called, no output | unit | same | ❌ Wave 0 |
| ZPL-05 | Envelope: first chars `^XA`, last chars `^XZ`, `^PQ` present | unit | same | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `cd webapps/main && yarn vitest run src/lib/print/zpl.test.js`
- **Per wave merge:** `cd webapps/main && yarn vitest run`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `webapps/main/src/lib/print/zpl.test.js` — covers all ZPL-01 through ZPL-05 test cases
- [ ] `webapps/main/src/lib/print/zpl.js` — implementation module (created in Wave 0)
- [ ] Export `schemasToV5` and `normalizePageSchema` from `webapps/main/src/lib/print/index.js`

---

## Open Questions

1. **`template_string` / `linked_text` field type handling**
   - What we know: `linkedText.js` likely uses type `template_string` or similar; `linkConfig.js` sets `linkType` on existing plugins. CONTEXT.md delegates to Claude's discretion.
   - What's unclear: Whether the resolved `inputs[pageIndex][fieldName]` value for a `template_string` field is already a plain string (fully resolved before `generateZpl` is called), or still contains `{{...}}` tokens.
   - Recommendation: Treat any field whose `type` includes `text` (case-insensitive) as a text field using `^A0N^FB^FD^FS`. The caller is expected to pass fully resolved inputs.

2. **GS1 DataMatrix FNC1 / GS1 compliance**
   - What we know: `generatePdf()` migrates `gs1datamatrix` → `datamatrix` when value isn't valid GS1 format. CONTEXT.md notes similar defensive handling may be needed.
   - What's unclear: Whether ZPL `^BX` requires FNC1 prefix `>8` to be genuinely GS1-compliant, or if the printer handles it from the command alone.
   - Recommendation: Pass value through as-is; document that GS1 AI format is caller responsibility. Optionally apply the same `gs1Re` check from `generatePdf()` and prepend `>8` FNC1 if valid.

3. **QR code module size / magnification formula**
   - What we know: ZPL `^BQ` magnification is 1-10 (integer multiplier of module dots, typically 4-6 dots/module at 203 dpi).
   - What's unclear: Best formula to map pdfme field `height` (mm) to magnification that fills the field.
   - Recommendation: `mag = clamp(round(mmToDots(height, dpi) / 22), 1, 10)`. 22 modules is a typical QR v2 dimension; adjust in testing.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded ZPL strings in warehouse app | Generated from pdfme templates via `generateZpl()` | Phase 2 (this phase) | Templates become printer-agnostic |
| Image fields in ZPL (`^GFA`) | Silently skipped with warning | v3 scope | No blocking impact on current labels |

---

## Sources

### Primary (HIGH confidence)

- [Labelary ZPL Introduction](https://labelary.com/zpl.html) — coordinate system, dpi reference, command overview
- [Simple ZPL2 Python Library Docs](https://simple-zpl2.readthedocs.io/en/latest/api/simple_zpl2.zpl_document.html) — confirmed parameter sets for all 6 barcode types, field block, font, mm→dots table
- [Zebra ^FB official docs](https://docs.zebra.com/us/en/printers/software/zpl-pg/c-zpl-zpl-commands/r-zpl-fb.html) — ^FB parameter list confirmed via search result extract
- [ZPL Quick Reference Gist](https://gist.github.com/metafloor/773bc61480d1d05a976184d45099ef56) — command syntax signatures for all commands

### Secondary (MEDIUM confidence)

- [ZPL barcodedatalink manual 2023](https://www.barcodedatalink.com/wp-content/uploads/2023/09/ZPL_Manual_from_Barcode_Datalink.pdf) — parameter ordering for ^BC, ^B3, ^BE, ^BX, ^BQ
- [BinaryKits ZPL font issue #3](https://github.com/BinaryKits/ZPLUtility/issues/3) — pt→dots formula: `pt * dpi / 72`
- [Minisoft ZPL font support](https://minisoft.com/support/index.php/zebra-font-support/) — dot size reference table

### Tertiary (LOW confidence)

- WebSearch result summaries for ^BQ QR prefix `MA,` — cross-referenced with simple-zpl2 `fd_switches='M,A'` default (MEDIUM after cross-ref)

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — no new dependencies; Vitest confirmed running at v4.1.0
- Coordinate conversion: HIGH — formula verified across multiple independent sources
- ZPL command syntax: HIGH — confirmed via official Zebra docs + simple-zpl2 reference implementation
- QR `MA,` prefix: MEDIUM — confirmed by simple-zpl2 default `fd_switches='M,A'` and ZPL II pg description
- GS1 DataMatrix FNC1: LOW — behavior depends on printer firmware; needs real-device testing

**Research date:** 2026-03-18
**Valid until:** 2026-09-18 (ZPL II spec is stable; labelary.com confirms no breaking changes since 2018)
