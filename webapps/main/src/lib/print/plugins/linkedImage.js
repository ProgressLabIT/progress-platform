/**
 * Image schema plugin with link configuration (preset/custom field) in the Designer propPanel.
 * Factory: pass customFields so Custom Field dropdown is populated.
 */
import { image } from '@pdfme/schemas';
import { createLinkSchema, linkDefaults } from './linkConfig.js';

/**
 * @param {Array<{ _key: string; name?: string; default_label?: string }>} [customFields]
 * @returns {import('@pdfme/common').Plugin}
 */
export function createLinkedImage(customFields = []) {
  return {
    pdf: image.pdf,
    ui: image.ui,
    propPanel: {
      schema: (props) => ({
        ...createLinkSchema(customFields, props.activeSchema),
        ...(typeof image.propPanel.schema === 'function'
          ? image.propPanel.schema(props)
          : image.propPanel.schema),
      }),
      widgets: image.propPanel.widgets || {},
      defaultSchema: {
        ...image.propPanel.defaultSchema,
        ...linkDefaults,
      },
    },
  };
}
