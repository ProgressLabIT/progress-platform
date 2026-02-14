/**
 * Text schema plugin with link configuration (preset/custom field) in the Designer propPanel.
 * Factory: pass customFields so Custom Field dropdown is populated.
 */
import { text } from '@pdfme/schemas';
import { createLinkSchema, linkDefaults } from './linkConfig.js';

/**
 * @param {Array<{ _key: string; name?: string; default_label?: string }>} [customFields]
 * @returns {import('@pdfme/common').Plugin}
 */
export function createLinkedText(customFields = []) {
  return {
    pdf: text.pdf,
    ui: text.ui,
    propPanel: {
      schema: (props) => ({
        ...createLinkSchema(customFields, props.activeSchema),
        ...(typeof text.propPanel.schema === 'function'
          ? text.propPanel.schema(props)
          : text.propPanel.schema),
      }),
      widgets: text.propPanel.widgets || {},
      defaultSchema: {
        ...text.propPanel.defaultSchema,
        ...linkDefaults,
      },
    },
  };
}
