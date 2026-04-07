/**
 * Shared link configuration for print template field plugins.
 * Used by linkedText, linkedImage, and linkedBarcodes to add preset/custom field linking
 * in the pdfme Designer propPanel. Uses form-render format: props.options for selects,
 * boolean hidden derived from activeSchema.
 */

export const presetOptions = [
  'current_date',
  'current_time',
  'current_user',

  'job.key',
  'job.qt_planned',
  'job.qt_completed',
  'job.phase_alias',
  'job.start_date',
  'job.start_time',
  'job.end_date',
  'job.end_time',
  'job.notes',
  'job.extra',

  'project.code',

  'work_order.code',
  'work_order.qt_planned',
  'work_order.qt_completed',
  'work_order.start_date',
  'work_order.start_time',
  'work_order.end_date',
  'work_order.end_time',
  'work_order.notes',
  'work_order.extra',

  'product.code',
  'product.description',

  'position.code',

  'issue.id',
  'issue.open_date',
  'issue.open_time',
  'issue.open_user',
  'issue.close_date',
  'issue.close_time',
  'issue.close_user',
  'issue.status',

  'serial.code',
  'serial.qt',
  'serial.create_date',
  'serial.create_time',
  'serial.release_date',
  'serial.release_time',
  'serial.extra',
];

/**
 * Creates form-render schema for link configuration. Must be called with activeSchema
 * so hidden state is correct (preset/custom_field/extraPath visibility).
 * @param {Array<{ _key: string; name: string }>} customFields - Custom fields for dropdown
 * @param {{ linkType?: string; linkValue?: string } | undefined} activeSchema - Current field schema
 * @returns {Record<string, import('form-render').Schema>}
 */
export function createLinkSchema(customFields = [], activeSchema = {}) {
  const isPreset = activeSchema?.linkType === 'preset';
  const isCustomField = activeSchema?.linkType === 'custom_field';
  const isNone = !activeSchema?.linkType || activeSchema?.linkType === 'none';

  // Determine options based on link type
  let linkValueOptions = [];
  let linkValueTitle = 'Link Value';
  let linkValueProps = {};

  if (isPreset) {
    linkValueTitle = 'Preset Field';
    linkValueOptions = presetOptions.map((p) => ({ label: p, value: p }));
  } else if (isCustomField) {
    linkValueTitle = 'Custom Field';
    linkValueOptions = (customFields || []).map((cf) => ({
      label: cf.name ?? cf.default_label ?? cf._key,
      value: cf._key,
    }));
    linkValueProps = {
      showSearch: true,
      optionFilterProp: 'label',
      filterOption: true,
    };
  }

  // Check if current linkValue is valid for the current linkType
  // If not valid or linkType is none, set to empty string
  const currentValue = activeSchema?.linkValue || '';
  const isValueValid = linkValueOptions.some(opt => opt.value === currentValue);
  const effectiveValue = (isNone || !isValueValid) ? '' : currentValue;

  // Also clear extraPath if linkValue is being cleared
  const needsExtraPath = isPreset && effectiveValue && effectiveValue.endsWith('.extra');

  const isTemplateExpression = activeSchema?.linkType === 'template_expression';
  const isComputed = activeSchema?.linkType === 'computed';

  const expressionPlaceholder = isComputed
    ? 'e.g. {{field::Quantity}} * {{field::UnitPrice}}\nFunctions: IF, CONCAT, SPLIT, UPPER, LOWER, ROUND, ABS, CEIL, FLOOR, NOW, DATE, FORMAT_DATE, DATE_ADD, DAYS_BETWEEN, YEAR, MONTH, DAY, WEEK\nOperators: + - * / == != < > <= >='
    : 'e.g. {{product.code}}-{{serial.qt}}';

  return {
    linkType: {
      title: 'Link Type',
      type: 'string',
      widget: 'select',
      props: {
        options: [
          { label: 'None', value: 'none' },
          { label: 'Preset', value: 'preset' },
          { label: 'Custom Field', value: 'custom_field' },
          { label: 'Template Expression', value: 'template_expression' },
          { label: 'Computed', value: 'computed' },
        ],
      },
    },
    templateExpression: {
      title: isComputed ? 'Computed Expression' : 'Expression',
      type: 'string',
      widget: 'FormulaEditor',
      span: 24,
      hidden: !isTemplateExpression && !isComputed,
      props: {
        placeholder: expressionPlaceholder,
      },
    },
    linkValue: {
      title: linkValueTitle,
      type: 'string',
      widget: 'select',
      disabled: isNone,
      hidden: isTemplateExpression || isComputed,
      default: effectiveValue,
      props: {
        options: linkValueOptions,
        ...linkValueProps,
      },
    },
    extraPath: {
      title: 'Extra Attribute Path',
      type: 'string',
      span: 24,
      hidden: !needsExtraPath,
      default: needsExtraPath ? activeSchema?.extraPath : '',
    },
  };
}

export const linkDefaults = {
  linkType: 'none',
  linkValue: '',
  extraPath: '',
  templateExpression: '',
};
