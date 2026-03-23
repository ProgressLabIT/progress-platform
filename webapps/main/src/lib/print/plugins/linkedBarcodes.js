/**
 * Barcode schema plugins with link configuration (preset/custom field) in the Designer propPanel.
 * Factory: pass customFields so Custom Field dropdown is populated.
 */
import { barcodes } from '@pdfme/schemas';
import { createLinkSchema, linkDefaults } from './linkConfig.js';

// Custom icons matching mdi icons used in sidebar
const qrcodeIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M3,11H11V3H3M5,5H9V9H5M13,3V11H21V3M19,9H15V5H19M3,21H11V13H3M5,15H9V19H5M13,13H15V15H13M15,15H17V17H15M17,13H19V15H17M19,15H21V17H19M17,17H19V19H17M13,17H15V19H13M15,19H17V21H15M19,19H21V21H19"/></svg>';
const dataMatrixIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M2 2H6V4H4V6H2V2M8 2H10V4H8V2M20 2V4H22V6H20V8H22V10H20V12H22V14H20V16H22V20H20V18H18V20H14V18H16V16H14V18H12V20H10V18H8V16H10V14H12V12H10V14H8V12H6V14H4V12H6V10H4V8H2V20H4V22H2V24H6V22H8V24H10V22H12V24H14V22H16V24H22V22H20V20H22V16H20V14H18V16H16V14H14V16H12V14H14V12H16V14H18V12H16V10H18V8H16V6H18V4H16V2H20M14 2V4H12V2H14M12 4H14V6H12V4M6 6V8H8V10H6V12H4V10H2V8H4V6H6M10 6V8H8V6H10M12 6H14V8H12V6M16 8V10H14V8H16M6 10H8V12H6V10M10 10V12H12V10H10M16 10H18V12H16V10M4 14H6V16H4V14M10 16V18H8V16H10M12 16H14V18H12V16M16 16H18V18H16V16"/></svg>';
const barcodeIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M2,6H4V18H2V6M5,6H6V18H5V6M7,6H10V18H7V6M11,6H12V18H11V6M14,6H16V18H14V6M17,6H20V18H17V6M21,6H22V18H21V6Z"/></svg>';

/**
 * @param {import('@pdfme/schemas').Plugin} barcodeSchema
 * @param {Array<{ _key: string; name?: string; default_label?: string }>} [customFields]
 * @param {string} customIcon - Custom SVG icon string
 * @returns {import('@pdfme/common').Plugin}
 */
function wrapBarcode(barcodeSchema, customFields = [], customIcon = null) {
  return {
    pdf: barcodeSchema.pdf,
    ui: barcodeSchema.ui,
    icon: customIcon || barcodeSchema.icon,
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
    qrcode: wrapBarcode(barcodes.qrcode, customFields, qrcodeIcon),
    ean13: wrapBarcode(barcodes.ean13, customFields, barcodeIcon),
    code39: wrapBarcode(barcodes.code39, customFields, barcodeIcon),
    code128: wrapBarcode(barcodes.code128, customFields, barcodeIcon),
    gs1datamatrix: wrapBarcode(barcodes.gs1datamatrix, customFields, dataMatrixIcon),
    japanpost: wrapBarcode(barcodes.japanpost, customFields, barcodeIcon),
    nw7: wrapBarcode(barcodes.nw7, customFields, barcodeIcon),
    itf14: wrapBarcode(barcodes.itf14, customFields, barcodeIcon),
    upca: wrapBarcode(barcodes.upca, customFields, barcodeIcon),
    upce: wrapBarcode(barcodes.upce, customFields, barcodeIcon),
  };
}
