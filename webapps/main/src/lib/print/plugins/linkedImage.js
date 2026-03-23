/**
 * Image schema plugin with link configuration (preset/custom field) in the Designer propPanel.
 * Factory: pass customFields so Custom Field dropdown is populated.
 */
import { image } from '@pdfme/schemas';
import { createLinkSchema, linkDefaults } from './linkConfig.js';

// Custom icon matching mdi-image used in sidebar
const imageIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M8.5,13.5L11,16.5L14.5,12L19,18H5M21,19V5C21,3.89 20.1,3 19,3H5A2,2 0 0,0 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19Z"/></svg>';

/**
 * @param {Array<{ _key: string; name?: string; default_label?: string }>} [customFields]
 * @returns {import('@pdfme/common').Plugin}
 */
export function createLinkedImage(customFields = []) {
  return {
    pdf: image.pdf,
    ui: image.ui,
    icon: imageIcon,
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
