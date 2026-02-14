/**
 * Barcode schema plugins with link configuration (preset/custom field) in the Designer propPanel.
 * Factory: pass customFields so Custom Field dropdown is populated.
 */
import { barcodes } from '@pdfme/schemas';
import { createLinkSchema, linkDefaults } from './linkConfig.js';

/**
 * @param {import('@pdfme/schemas').Plugin} barcodeSchema
 * @param {Array<{ _key: string; name?: string; default_label?: string }>} [customFields]
 * @returns {import('@pdfme/common').Plugin}
 */
function wrapBarcode(barcodeSchema, customFields = []) {
  return {
    pdf: barcodeSchema.pdf,
    ui: barcodeSchema.ui,
    propPanel: {
      schema: (props) => ({
        ...createLinkSchema(customFields, props.activeSchema),
        ...(typeof barcodeSchema.propPanel.schema === 'function'
          ? barcodeSchema.propPanel.schema(props)
          : barcodeSchema.propPanel.schema),
      }),
      widgets: barcodeSchema.propPanel.widgets || {},
      defaultSchema: {
        ...barcodeSchema.propPanel.defaultSchema,
        ...linkDefaults,
      },
    },
  };
}

/**
 * @param {Array<{ _key: string; name?: string; default_label?: string }>} [customFields]
 * @returns {Record<string, import('@pdfme/common').Plugin>}
 */
export function createLinkedBarcodes(customFields = []) {
  return {
    qrcode: wrapBarcode(barcodes.qrcode, customFields),
    ean13: wrapBarcode(barcodes.ean13, customFields),
    code39: wrapBarcode(barcodes.code39, customFields),
    code128: wrapBarcode(barcodes.code128, customFields),
    gs1datamatrix: wrapBarcode(barcodes.gs1datamatrix, customFields),
    japanpost: wrapBarcode(barcodes.japanpost, customFields),
    nw7: wrapBarcode(barcodes.nw7, customFields),
    itf14: wrapBarcode(barcodes.itf14, customFields),
    upca: wrapBarcode(barcodes.upca, customFields),
    upce: wrapBarcode(barcodes.upce, customFields),
  };
}
