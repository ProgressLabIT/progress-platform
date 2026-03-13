# Print Templates (pdfme v5)

Print templates define PDF layouts (text, images, barcodes) and how fields are linked to context data (presets or custom fields). The platform uses [pdfme](https://pdfme.com/) v5 with custom plugins for Progress-specific linking.

## Architecture

- **Designer**: [PrintTemplateDesigner.vue](webapps/main/src/components/PrintTemplateDesigner.vue) — toolbar with add-field buttons (no pdfme left sidebar), pdfme Designer for layout. Plugins built with `buildPlugins(customFields)` so the property panel can show Custom Field dropdowns. Link Type and Custom Field appear above graphical/formatting options in the prop panel. An unscoped CSS rule in the Designer raises Ant Design Select/Cascader dropdown z-index (`.ant-select-dropdown`, `.ant-cascader-dropdown` → 9999) so dropdowns are visible above the Quasar dialog (z-index ~6000).
- **Fill & generate**: [PrintDialog.vue](webapps/main/src/components/PrintDialog.vue) shows only editable fields, validates required fields, and uses `buildPlugins([])` for PDF generation. [print.js](webapps/main/src/lib/print.js) uses `buildPlugins([])` for programmatic `generatePdf()`.
- **Plugins**: [webapps/main/src/lib/print/plugins/](webapps/main/src/lib/print/plugins/) — `createLinkedText`, `createLinkedImage`, `createLinkedBarcodes` (factory functions taking `customFields`), and `createDataMatrixPlugin`. Link configuration is form-render format with `props.options` for selects and boolean `hidden` from `activeSchema`.

## Field properties (v5)

Each schema field in a template can carry:

| Property       | Type    | Meaning |
|----------------|---------|--------|
| `readOnly`     | boolean | If true, the field is not shown in the print dialog form (auto-filled from link, not editable). |
| `required`     | boolean | If true, the field is mandatory; label shows a red asterisk and preview is blocked until filled. |
| `linkType`     | string  | `'none'`, `'preset'`, or `'custom_field'`. |
| `linkValue`    | string  | Preset key when `linkType === 'preset'` (e.g. `job.key`, `serial.extra`). |
| `extraPath`    | string  | When preset is an `.extra` preset (e.g. `serial.extra`), this is the nested path (e.g. `one.two`). Resolved as `linkValue + '.' + extraPath`. |
| `customFieldKey` | string | Custom field `_key` when `linkType === 'custom_field'`. |

Backend models: [backend/api/models/print.py](backend/api/models/print.py) — `TextFieldSpec` and `VisualFieldSpec` include `readOnly`, `required`, `extraPath`, and link fields so they pass through the API.

## Link configuration

- **Presets**: Fixed keys (e.g. `current_date`, `job.key`, `serial.code`, `serial.extra`) resolved by [print.js](webapps/main/src/lib/print.js) `TemplateContext.getPresetValue()` / `getExtraValue()`.
- **Custom fields**: Resolved by context-specific `getCustomFieldValue(customFieldKey)` (e.g. serial/product/step/issue data).
- **Extra path**: For presets whose key ends with `.extra`, the Designer shows an "Extra Attribute Path" field; at runtime the full path is `linkValue + '.' + extraPath` (e.g. `serial.extra.customAttr`).

## Data flow

1. **Designer**: User adds fields via toolbar, configures link type/value/extra path and editable/required in the pdfme property panel. Template is saved with schemas in v5 format (array of arrays, each field has `name`).
2. **Print dialog**: Template loaded → `getFieldNamesAndLinks()` collects all field names and link config (including `extraPath` combination). Form model is filled from context for linked fields. Only non–read-only fields are rendered; required fields get an asterisk and are validated before preview.
3. **Generation**: `prepareInputs()` builds inputs for all fields (including read-only); `generate()` uses the same plugins (via `buildPlugins([])`).

## Barcode types

| Plugin key       | bwip-js bcid       | Validation | Notes |
|------------------|--------------------|------------|-------|
| `datamatrix`     | `datamatrix`       | Any non-empty string | Custom plugin (`customDataMatrix.js`). Use for free-form text. |
| `gs1datamatrix`  | `gs1datamatrix`    | Strict GS1 AI format: must contain `(01)` + valid GTIN (8/12/13/14 digits with check digit), max 52 chars | pdfme built-in. Use only when encoding GS1-compliant data. |
| `qrcode`         | `qrcode`           | Up to 500 chars | pdfme built-in. |
| Other 1D codes   | Same as key (except `nw7` → `rationalizedCodabar`) | Type-specific (digits, check digits, character sets) | pdfme built-in. |

**Backward compatibility**: At generation time, `PrintDialog.vue` and `generatePdf()` automatically migrate `gs1datamatrix` fields to `datamatrix` when the runtime input value doesn't match GS1 AI format. This ensures existing templates created before the plain DataMatrix plugin was added continue to work.
