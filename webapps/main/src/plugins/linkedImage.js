/**
 * Image schema plugin with link configuration (preset/custom field) in the Designer propPanel.
 */
import { image } from '@pdfme/schemas';
import { linkPropPanelFields, linkDefaults } from './linkConfig.js';

export const linkedImage = {
  pdf: image.pdf,
  ui: image.ui,
  propPanel: {
    schema: {
      ...image.propPanel.schema,
      ...linkPropPanelFields,
    },
    defaultSchema: {
      ...image.propPanel.defaultSchema,
      ...linkDefaults,
    },
  },
};
