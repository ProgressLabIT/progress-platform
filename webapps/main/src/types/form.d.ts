export type CustomFieldType =
  | 'text'
  | 'number'
  | 'boolean'
  | 'ternary'
  | 'choice'
  | 'date'
  | 'time'
  | 'files';

export interface CustomField {
  _key: string;
  type: CustomFieldType;
  name: string;
  default_label: string;
  default_hint: string;
  use_in_serial: boolean;
}

export interface FormField {
  _key: string;
  custom_field_key: string;
  multiple: boolean;
  mandatory?: boolean;
  label?: string;
  hint?: string;
  required: boolean;

  /**
   * Client-side only
   */
  value?: any;

  // default?: string;
  // hidden?: boolean;
}
