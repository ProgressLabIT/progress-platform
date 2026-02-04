/**
 * Shared link configuration for print template field plugins.
 * Used by linkedText, linkedImage, and linkedBarcodes to add preset/custom field linking
 * in the pdfme Designer propPanel.
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

export const linkPropPanelFields = {
  linkType: {
    title: 'Link Type',
    type: 'string',
    widget: 'select',
    enum: ['none', 'preset', 'custom_field'],
    default: 'none',
  },
  linkValue: {
    title: 'Link Value',
    type: 'string',
    widget: 'select',
    enum: presetOptions,
    hidden: '{{formData.linkType !== "preset"}}',
  },
  customFieldKey: {
    title: 'Custom Field',
    type: 'string',
    hidden: '{{formData.linkType !== "custom_field"}}',
  },
};

export const linkDefaults = {
  linkType: 'none',
  linkValue: '',
  customFieldKey: '',
};
