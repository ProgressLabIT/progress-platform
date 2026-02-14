import { text } from '@pdfme/schemas';
import { linkPropPanelFields, linkDefaults } from './linkConfig.js';

export const linkedText = {
  pdf: text.pdf,
  ui: text.ui,
  propPanel: {
    schema: { ...text.propPanel.schema, ...linkPropPanelFields },
    defaultSchema: { ...text.propPanel.defaultSchema, ...linkDefaults },
  },
};
