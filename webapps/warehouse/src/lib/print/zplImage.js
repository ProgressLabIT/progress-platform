/**
 * Image-to-ZPL conversion utilities.
 *
 * Converts base64 data-URL images into ZPL ^GFA (Graphic Field ASCII)
 * commands suitable for Zebra label printers. Uses the Canvas API for
 * resizing and monochrome thresholding — browser-only.
 *
 * @module zplImage
 */

const IMAGE_TYPE_RE = /image/i;

/**
 * Load a base64 data URL into an HTMLImageElement.
 * @param {string} dataUrl
 * @returns {Promise<HTMLImageElement>}
 */
function loadImageElement(dataUrl) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error('Failed to load image from data URL'));
    img.src = dataUrl;
  });
}

/**
 * Convert millimetres to dots at the given DPI.
 * @param {number} mm
 * @param {number} dpi
 * @returns {number}
 */
function mmToDots(mm, dpi) {
  return Math.round(mm * dpi / 25.4);
}

/**
 * Convert a base64 data-URL image to a ZPL ^GFA command string.
 *
 * Pipeline: data URL → Image element → Canvas (resize) → getImageData →
 * luminance threshold → 1-bit packed bytes → ASCII hex → ^GFA command.
 *
 * @param {string} base64DataUrl  - data:image/...;base64,... string
 * @param {number} widthMm        - target width in millimetres (from pdfme schema)
 * @param {number} heightMm       - target height in millimetres (from pdfme schema)
 * @param {number} [dpi=203]      - printer DPI
 * @returns {Promise<string>} ZPL ^GFA command, or '' if input is empty
 */
export async function imageToZplGraphic(base64DataUrl, widthMm, heightMm, dpi = 203) {
  if (!base64DataUrl || typeof base64DataUrl !== 'string') return '';

  const widthDots = Math.max(1, mmToDots(widthMm, dpi));
  const heightDots = Math.max(1, mmToDots(heightMm, dpi));

  const img = await loadImageElement(base64DataUrl);

  const canvas = document.createElement('canvas');
  canvas.width = widthDots;
  canvas.height = heightDots;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(img, 0, 0, widthDots, heightDots);

  const imageData = ctx.getImageData(0, 0, widthDots, heightDots);
  const pixels = imageData.data; // RGBA flat array

  const bytesPerRow = Math.ceil(widthDots / 8);
  const totalBytes = bytesPerRow * heightDots;
  let hex = '';

  for (let y = 0; y < heightDots; y++) {
    for (let byteIdx = 0; byteIdx < bytesPerRow; byteIdx++) {
      let byte = 0;
      for (let bit = 0; bit < 8; bit++) {
        const x = byteIdx * 8 + bit;
        if (x < widthDots) {
          const idx = (y * widthDots + x) * 4;
          const r = pixels[idx];
          const g = pixels[idx + 1];
          const b = pixels[idx + 2];
          const a = pixels[idx + 3];
          // BT.601 luminance; transparent pixels → white (no print)
          const gray = 0.299 * r + 0.587 * g + 0.114 * b;
          if (a > 128 && gray < 128) {
            byte |= (1 << (7 - bit));
          }
        }
      }
      hex += byte.toString(16).padStart(2, '0').toUpperCase();
    }
  }

  return `^GFA,${totalBytes},${totalBytes},${bytesPerRow},${hex}`;
}

/**
 * Pre-process template inputs for ZPL: convert image fields from base64
 * data URLs to ^GFA command strings.
 *
 * For each image-type field the data URL is resolved as follows:
 *  - If the input value is non-empty (linked image resolved at runtime), use it.
 *  - If linkType is 'none' or absent (static image), fall back to field.content
 *    (the base64 data URL the designer embedded in the template).
 *  - If linkType IS set but the resolved value is empty, keep it empty — the
 *    linked data source genuinely has no value and we must not mask that.
 *
 * Non-image values pass through untouched. Returns a new inputs array.
 *
 * `inputs` follows pdfme record semantics — each record holds every field
 * across all template pages (field names are unique template-wide). Image
 * fields from any page are therefore converted against each record directly,
 * not by page index.
 *
 * @param {object[][]} schemas  - pdfme v5 normalised schemas (array of page arrays)
 * @param {object[]}   inputs   - record objects, each holding all fields, e.g. [{ fieldName: value }]
 * @param {number}     [dpi=203]
 * @returns {Promise<object[]>} new inputs array with images converted to ^GFA strings
 */
export async function processZplImageFields(schemas, inputs, dpi = 203) {
  const result = inputs.map(record => ({ ...record }));
  const imageFields = schemas.flat().filter(f => f.name && IMAGE_TYPE_RE.test(f.type));

  for (const record of result) {
    for (const field of imageFields) {
      const runtimeValue = record[field.name];
      const isUnlinked = !field.linkType || field.linkType === 'none';
      const dataUrl = runtimeValue || (isUnlinked ? field.content : '') || '';

      if (!dataUrl) continue;

      try {
        record[field.name] = await imageToZplGraphic(dataUrl, field.width, field.height, dpi);
      } catch (err) {
        console.warn(`[processZplImageFields] Failed to convert image "${field.name}":`, err);
        record[field.name] = '';
      }
    }
  }

  return result;
}
