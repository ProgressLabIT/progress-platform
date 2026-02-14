/**
 * pdfme custom plugins with Progress field linking (preset/custom field) in the Designer propPanel.
 * Use factory functions with customFields when building Designer plugins; use buildPlugins([]) for Generator-only.
 */
export { presetOptions, createLinkSchema, linkDefaults } from './linkConfig.js';
export { createLinkedText } from './linkedText.js';
export { createLinkedImage } from './linkedImage.js';
export { createLinkedBarcodes } from './linkedBarcodes.js';

import { createLinkedText } from './linkedText.js';
import { createLinkedImage } from './linkedImage.js';
import { createLinkedBarcodes } from './linkedBarcodes.js';

/**
 * Build plugin map for Designer or Generator. Pass customFields from store when used in Designer.
 * @param {Array<{ _key: string; name?: string; default_label?: string }>} [customFields]
 * @returns {Record<string, import('@pdfme/common').Plugin>}
 */
export function buildPlugins(customFields = []) {
  const barcodes = createLinkedBarcodes(customFields);
  return {
    text: createLinkedText(customFields),
    image: createLinkedImage(customFields),
    qrcode: barcodes.qrcode,
    ean13: barcodes.ean13,
    code39: barcodes.code39,
    code128: barcodes.code128,
    gs1datamatrix: barcodes.gs1datamatrix,
    japanpost: barcodes.japanpost,
    nw7: barcodes.nw7,
    itf14: barcodes.itf14,
    upca: barcodes.upca,
    upce: barcodes.upce,
  };
}
