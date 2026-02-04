import { barcodes } from '@pdfme/schemas';
import { linkPropPanelFields, linkDefaults } from './linkConfig.js';

function wrapBarcode(barcodeSchema) {
  return {
    pdf: barcodeSchema.pdf,
    ui: barcodeSchema.ui,
    propPanel: {
      schema: { ...barcodeSchema.propPanel.schema, ...linkPropPanelFields },
      defaultSchema: { ...barcodeSchema.propPanel.defaultSchema, ...linkDefaults },
    },
  };
}

export const linkedBarcodes = {
  qrcode: wrapBarcode(barcodes.qrcode),
  ean13: wrapBarcode(barcodes.ean13),
  code39: wrapBarcode(barcodes.code39),
  code128: wrapBarcode(barcodes.code128),
  gs1datamatrix: wrapBarcode(barcodes.gs1datamatrix),
  japanpost: wrapBarcode(barcodes.japanpost),
  nw7: wrapBarcode(barcodes.nw7),
  itf14: wrapBarcode(barcodes.itf14),
  upca: wrapBarcode(barcodes.upca),
  upce: wrapBarcode(barcodes.upce),
};
