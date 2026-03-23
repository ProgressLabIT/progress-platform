/**
 * Text schema plugin with link configuration (preset/custom field) in the Designer propPanel.
 * Factory: pass customFields so Custom Field dropdown is populated.
 */
import { text } from '@pdfme/schemas';
import { createLinkSchema, linkDefaults } from './linkConfig.js';

// Custom icon matching mdi-format-text used in sidebar
const textIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M18.5,4L19.66,8.35L18.7,8.61C18.25,7.74 17.79,6.87 17.26,6.43C16.73,6 16.11,6 15.5,6H13V16.5C13,17 13,17.5 13.33,17.75C13.67,18 14.33,18 15,18V19H9V18C9.67,18 10.33,18 10.67,17.75C11,17.5 11,17 11,16.5V6H8.5C7.89,6 7.27,6 6.74,6.43C6.21,6.87 5.75,7.74 5.3,8.61L4.34,8.35L5.5,4H18.5Z"/></svg>';

/**
 * @param {Array<{ _key: string; name?: string; default_label?: string }>} [customFields]
 * @returns {import('@pdfme/common').Plugin}
 */
export function createLinkedText(customFields = []) {
  return {
    pdf: text.pdf,
    ui: text.ui,
    icon: textIcon,
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
