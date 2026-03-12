/**
 * Template String schema plugin for pdfme.
 * Defines the `template_string` field type — a text field with a fixed linkType
 * of `template_expression` and a `templateExpression` field in the propPanel.
 * The expression is evaluated at print time by templateResolver.js.
 */
import { text } from '@pdfme/schemas';

// Simple "T{}" style icon indicating a template expression field
const templateStringIcon =
  '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><text x="2" y="18" font-size="14" font-family="monospace" fill="currentColor">T{}</text></svg>';

/**
 * @param {Array<{ _key: string; name?: string; default_label?: string }>} [customFields]
 * @returns {import('@pdfme/common').Plugin}
 */
export function createLinkedTemplateString(customFields = []) {
  return {
    pdf: text.pdf,
    ui: text.ui,
    icon: templateStringIcon,
    propPanel: {
      schema: (props) => ({
        templateExpression: {
          title: 'Expression',
          type: 'string',
          span: 24,
          props: {
            placeholder: 'e.g. Product: {{product.code}} - Qty: {{serial.qt}} pcs',
          },
        },
        ...(typeof text.propPanel.schema === 'function'
          ? text.propPanel.schema(props)
          : text.propPanel.schema),
      }),
      widgets: text.propPanel.widgets || {},
      defaultSchema: {
        ...text.propPanel.defaultSchema,
        type: 'template_string',
        linkType: 'template_expression',
        linkValue: '',
        extraPath: '',
        templateExpression: '',
        content: '',
      },
    },
  };
}
