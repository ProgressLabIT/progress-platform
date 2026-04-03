/**
 * ZPL II transpiler for pdfme templates.
 *
 * Converts a pdfme v5 template + resolved field inputs into a ZPL string
 * ready to send directly to a Zebra label printer.
 *
 * Supported field types:
 *   text, template_string → ^A0N (scalable font) + ^FB (field block)
 *   qrcode               → ^BQN (QR Code, model 2)
 *   code128              → ^BCN (Code 128)
 *   code39               → ^B3N (Code 39)
 *   ean13                → ^BEN (EAN-13; caller must pass 12 numeric digits)
 *   gs1datamatrix        → ^BXN (DataMatrix ECC 200)
 *   image / linkedImage  → ^GFA (pre-processed by zplImage.js into ^GFA hex)
 *
 * @module zpl
 */

// ---------------------------------------------------------------------------
// Schema normalization helpers (mirrors index.js; inlined to avoid Vue/Quasar
// framework imports that make index.js untestable in Vitest node environment)
// ---------------------------------------------------------------------------

/**
 * Normalise a pdfme page schema to a flat array of field objects.
 * Handles both v5 array format and legacy object-map format.
 * @param {any} pageSchema
 * @returns {object[]}
 */
function normalizePageSchema(pageSchema) {
  if (!pageSchema) return [];
  if (Array.isArray(pageSchema)) return pageSchema;
  return Object.entries(pageSchema).map(([fieldName, fieldSpec]) => ({ ...fieldSpec, name: fieldName }));
}

/**
 * Normalise all pages in a pdfme `schemas` array.
 * @param {any} schemas
 * @returns {object[][]}
 */
function schemasToV5(schemas) {
  if (!schemas || !Array.isArray(schemas)) return [];
  return schemas.map(normalizePageSchema);
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const DEFAULT_DPI = 203;

/** pdfme alignment → ZPL ^FB justification character */
const ALIGN_MAP = { left: 'L', center: 'C', right: 'R' };

/** Regex to detect image field types (case-insensitive) */
const IMAGE_TYPE_RE = /image/i;

// ---------------------------------------------------------------------------
// Coordinate helpers
// ---------------------------------------------------------------------------

/**
 * Convert millimetres to ZPL dots at the given DPI.
 * Formula: dots = mm * (dpi / 25.4) — one inch is 25.4 mm.
 * @param {number} mm
 * @param {number} dpi
 * @returns {number}
 */
function mmToDots(mm, dpi) {
  return Math.round(mm * dpi / 25.4);
}

/**
 * Convert typographic points to ZPL dots at the given DPI.
 * Formula: dots = pt * (dpi / 72) — one inch is 72 points.
 * @param {number} pt
 * @param {number} dpi
 * @returns {number}
 */
function ptToDots(pt, dpi) {
  return Math.round(pt * dpi / 72);
}

// ---------------------------------------------------------------------------
// Field renderers
// ---------------------------------------------------------------------------

/**
 * Render a text or template_string field.
 * Uses ^A0N (Font 0, normal rotation) for scalable sizing and ^FB for
 * field width / alignment.
 * @param {object} field
 * @param {string} value
 * @param {number} dpi
 * @returns {string}
 */
function renderText(field, value, dpi) {
  const x = mmToDots(field.position.x, dpi);
  const y = mmToDots(field.position.y, dpi);
  const fontH = ptToDots(field.fontSize ?? 10, dpi);
  const fieldW = Math.max(1, mmToDots(field.width ?? 50, dpi));
  const align = ALIGN_MAP[field.alignment] ?? 'L';
  return `^FO${x},${y}^A0N,${fontH},${fontH}^FB${fieldW},1,0,${align},0^FD${value}^FS`;
}

/**
 * Render a QR code field.
 * Magnification is derived from field height so the QR fills the designer
 * intent; clamped to ZPL valid range 1–10.
 * Data prefix MA, = manual input, automatic character selection (required by ZPL ^BQ).
 * @param {object} field
 * @param {string} value
 * @param {number} dpi
 * @returns {string}
 */
function renderQr(field, value, dpi) {
  const x = mmToDots(field.position.x, dpi);
  const y = mmToDots(field.position.y, dpi);
  const mag = Math.max(1, Math.min(10, Math.round(mmToDots(field.height ?? 20, dpi) / 22)));
  return `^FO${x},${y}^BQN,2,${mag}^FDMA,${value}^FS`;
}

/**
 * Render a Code 128 barcode field.
 * ^BCN,{h},Y,N,N — Normal rotation, height in dots, HRI below, no text above, no UCC.
 * @param {object} field
 * @param {string} value
 * @param {number} dpi
 * @returns {string}
 */
function renderCode128(field, value, dpi) {
  const x = mmToDots(field.position.x, dpi);
  const y = mmToDots(field.position.y, dpi);
  const h = mmToDots(field.height ?? 10, dpi);
  return `^FO${x},${y}^BCN,${h},Y,N,N^FD${value}^FS`;
}

/**
 * Render a Code 39 barcode field.
 * ^B3N,N,{h},Y,N — Normal rotation, no check digit, height in dots, print text, not above.
 * @param {object} field
 * @param {string} value
 * @param {number} dpi
 * @returns {string}
 */
function renderCode39(field, value, dpi) {
  const x = mmToDots(field.position.x, dpi);
  const y = mmToDots(field.position.y, dpi);
  const h = mmToDots(field.height ?? 10, dpi);
  return `^FO${x},${y}^B3N,N,${h},Y,N^FD${value}^FS`;
}

/**
 * Render an EAN-13 barcode field.
 * ^BEN,{h},Y,N — Normal rotation, height in dots, print HRI, not above.
 * Note: caller must pass exactly 12 numeric digits; the 13th check digit is
 * computed by the printer.
 * @param {object} field
 * @param {string} value
 * @param {number} dpi
 * @returns {string}
 */
function renderEan13(field, value, dpi) {
  const x = mmToDots(field.position.x, dpi);
  const y = mmToDots(field.position.y, dpi);
  const h = mmToDots(field.height ?? 10, dpi);
  return `^FO${x},${y}^BEN,${h},Y,N^FD${value}^FS`;
}

/**
 * Render a GS1 DataMatrix barcode field.
 * ^BXN,{cellSize},200 — Normal rotation, cell height in dots, ECC 200 quality.
 * @param {object} field
 * @param {string} value
 * @param {number} dpi
 * @returns {string}
 */
function renderDataMatrix(field, value, dpi) {
  const x = mmToDots(field.position.x, dpi);
  const y = mmToDots(field.position.y, dpi);
  const h = Math.max(2, Math.round(mmToDots(field.height ?? 8, dpi) / 22));
  return `^FO${x},${y}^BXN,${h},200^FD${value}^FS`;
}

/**
 * Render an image field whose value has already been converted to a ^GFA
 * command string by processZplImageFields() in zplImage.js.
 * @param {object} field
 * @param {string} value - pre-computed ^GFA command string, or empty
 * @param {number} dpi
 * @returns {string}
 */
function renderImage(field, value, dpi) {
  if (!value) return '';
  if (!value.startsWith('^GFA')) {
    console.warn(`[generateZpl] Image field "${field.name}" has unexpected value format (expected ^GFA)`);
    return '';
  }
  const x = mmToDots(field.position.x, dpi);
  const y = mmToDots(field.position.y, dpi);
  return `^FO${x},${y}${value}^FS`;
}

// ---------------------------------------------------------------------------
// Field dispatcher
// ---------------------------------------------------------------------------

/**
 * Dispatch a single field to the appropriate renderer based on field.type.
 * Unknown types are skipped with a console.warn.
 * @param {object} field
 * @param {string} value
 * @param {number} dpi
 * @returns {string}
 */
function renderField(field, value, dpi) {
  if (IMAGE_TYPE_RE.test(field.type)) {
    return renderImage(field, value, dpi);
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
    case 'datamatrix':
    case 'gs1datamatrix':
      return renderDataMatrix(field, value, dpi);
    default:
      console.warn(`[generateZpl] Unknown field type "${field.type}" skipped`);
      return '';
  }
}

// ---------------------------------------------------------------------------
// Page renderer
// ---------------------------------------------------------------------------

/**
 * Render a single label page as a complete ^XA...^PQ...^XZ block.
 * @param {object[]} fields  - Normalised field array for this page
 * @param {object}   inputValues - { [fieldName]: resolvedValue } for this page
 * @param {number}   dpi
 * @param {number}   quantity
 * @returns {string}
 */
function renderPage(fields, inputValues, dpi, quantity) {
  const fieldLines = fields
    .map(f => renderField(f, inputValues[f.name] ?? '', dpi))
    .filter(Boolean);
  return `^XA\n${fieldLines.join('\n')}\n^PQ${quantity}\n^XZ`;
}

// ---------------------------------------------------------------------------
// Main export
// ---------------------------------------------------------------------------

/**
 * Generate a ZPL string from a pdfme template and resolved inputs.
 *
 * @param {object}  template          - pdfme template ({ basePdf, schemas })
 * @param {object[]} inputs           - Array of per-page input objects, e.g. [{ fieldName: value }]
 * @param {object}  [options]
 * @param {number}  [options.dpi=203] - Printer DPI (203 or 300)
 * @param {number}  [options.quantity=1] - ^PQ print quantity per label
 * @returns {string} ZPL string, one ^XA...^XZ block per template page, joined with newlines
 */
export function generateZpl(template, inputs, { dpi = DEFAULT_DPI, quantity = 1 } = {}) {
  const pages = schemasToV5(template.schemas);
  return pages
    .map((fields, pageIndex) => renderPage(fields, inputs?.[pageIndex] ?? {}, dpi, quantity))
    .join('\n');
}
