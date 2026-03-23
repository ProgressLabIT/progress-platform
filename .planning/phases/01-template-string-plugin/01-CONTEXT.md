# Phase 1: Template String Plugin - Context

**Gathered:** 2026-03-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a `template_expression` field type to the pdfme designer that lets designers compose text from `{{variable}}` syntax (e.g. `Product: {{product.code}} - Qty: {{serial.qt}} pcs`). Expressions are encoded for stable storage and resolved to live values when printing. This is a frontend-only plugin — no new backend collections, no changes to pdfme's rendering pipeline beyond wrapping the base `text` plugin.

</domain>

<decisions>
## Implementation Decisions

### Variable reference UI
- Textarea-only in the property panel — no reference list, no click-to-insert chips
- Label: "Expression" (or similar — Claude decides exact wording)
- Both preset keys (`product.code`, `serial.qt`, etc.) and custom field slugs (`cf::product_color`) are valid in expressions
- No autocomplete helper; users type variable syntax directly

### Token syntax
- Preset variables: `{{preset.key}}` — dot-notation, no prefix (e.g. `{{product.code}}`, `{{serial.qt}}`)
- Custom field variables: `{{cf::slug}}` — `cf::` prefix disambiguates from presets unambiguously
- Stored form uses `_key` for custom fields: `{{cf::abc123}}` (short `_key` only, NOT `_id` / no `CustomField/` prefix)
- Display/editing form uses slugified `name`: `{{cf::product_color}}`

### Encode / decode scope
- `encodeExpression(expr, customFields)`: scans for `{{cf::slug}}` tokens → replaces with `{{cf::_key}}`; preset tokens pass through unchanged
- `decodeExpression(expr, customFields)`: scans for `{{cf::_key}}` tokens → replaces with `{{cf::slugify(name)}}`; preset tokens pass through unchanged
- `resolveExpression(expr, context, customFields)`: replaces `{{cf::_key}}` with live custom field value via context, replaces `{{preset.key}}` via `context.getPresetValue()`
- All three functions live in `templateResolver.js`

### Slugification
- Algorithm: lowercase, replace spaces/special chars with `_`, remove content in parentheses (including the parens), collapse consecutive underscores, trim leading/trailing underscores
- Example: `"Product Color"` → `product_color`, `"Qty (pcs)"` → `qty`
- Uniqueness enforced on the **slugified form** of `name` — backend endpoint validates no two custom fields share the same slug at creation/edit time
- This is a prerequisite for `templateResolver.js` to work without conflicts; include in Phase 1 scope

### Custom field model clarification
- `CustomField.name` = stable, searchable identifier (slugified, unique-constrained)
- `CustomField.default_label` = display name shown to users (free text, may duplicate)
- `CustomField._key` = short ArangoDB ID (e.g. `abc123`); `_id` = `CustomField/abc123` — only `_key` is used in expressions

### Unresolved variable fallback
- Missing value (no context, empty field, deleted custom field) → empty string (silent omission)
- Consistent with how existing `getPresetValue()` returns `undefined` → `String('')` in PrintDialog

### PrintDialog step 2 behavior
- Template expression fields appear in the Fill Data step pre-resolved with live values (same as all other linked text fields)
- Field is editable — user can override the resolved value before generating PDF
- This is consistent with existing behavior: all text fields with `linkType !== 'none'` are pre-filled but editable; only `readOnly: true` schema fields are hidden

### Designer canvas preview
- Canvas shows the **decoded expression** (human-readable slug form) while editing
- `PrintTemplateDesigner.vue` decodes `templateExpression` values when loading a template into the Designer
- `saveTemplate()` encodes before sending to the API
- Working in-memory state always uses decoded form; encoded form only exists in the DB payload

### Plugin structure
- `linkedTemplateString.js` follows the same factory pattern as `linkedText.js`, `linkedImage.js`, `linkedBarcodes.js`
- Wraps pdfme base `text` schema
- Adds `templateExpression` (textarea) to `propPanel`
- `linkType` value for this field type: `template_expression`
- Register in `buildPlugins()` in `index.js` under a new key (e.g. `template_string`)
- Toolbar button added to `PrintTemplateDesigner.vue` custom left sidebar

### Claude's Discretion
- Exact textarea label wording (confirmed: "Expression" or similar)
- Icon for the toolbar button
- The `defaultSchema` values (position, size, font defaults)
- Exact slugification edge cases beyond the stated rules (consecutive underscores, leading/trailing)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `linkedText.js`: Exact pattern to follow — factory function `createLinkedText(customFields)`, wraps `text.pdf`, `text.ui`, `text.propPanel`, adds custom `propPanel.schema`
- `linkConfig.js` `createLinkSchema()`: Form-render schema builder — reuse this pattern for the `templateExpression` textarea widget
- `linkConfig.js` `presetOptions`: Complete list of valid preset keys; `resolveExpression` should recognize these
- `buildPlugins()` in `index.js`: Registry to add `template_string` plugin
- `TemplateContext.getPresetValue()`: Already resolves all preset keys to live values — call this in `resolveExpression`
- `TemplateContext.getCustomFieldValue()`: Resolves custom field `_key` to value — call this in `resolveExpression`

### Established Patterns
- Plugin registration: factory function exported from `lib/print/plugins/`, imported in `index.js`
- `PrintTemplateDesigner.vue` `addField(type)`: Reads `plugin.propPanel.defaultSchema` to initialize a new field — `linkedTemplateString` must expose a valid `defaultSchema`
- `PrintTemplateDesigner.vue` `saveTemplate()`: Calls `designer.getTemplate()` directly — encode step must be added here before the API call
- `PrintTemplateDesigner.vue` `initTemplate()`: Loads template into Designer — decode step must be added here
- `PrintDialog.vue` `getFieldNamesAndLinks()`: Reads `field.linkType` and `field.linkValue` from schema fields — `template_expression` link type needs to be handled here (pre-resolve the expression into `formModel`)
- `PrintDialog.vue` `selectTemplate()`: Populates `formModel` via `getLink(fieldName)` — `template_expression` case: call `resolveExpression` on the stored `templateExpression` value

### Integration Points
- `lib/print/plugins/index.js`: Add `template_string: createLinkedTemplateString(customFields)` to `buildPlugins()`
- `PrintTemplateDesigner.vue`: Add toolbar button + decode-on-load + encode-on-save
- `PrintDialog.vue`: Handle `linkType === 'template_expression'` in `selectTemplate()` — call `resolveExpression` to pre-populate `formModel`
- Backend `custom-field` endpoint: Add slug uniqueness validation on create/edit

</code_context>

<specifics>
## Specific Ideas

- Expression example from requirements: `Product: {{product.code}} - Qty: {{serial.qt}} pcs`
- Custom field token example: `{{cf::product_color}}` (display), `{{cf::abc123}}` (stored)
- The `cf::` prefix is the canonical way to tell apart custom field references from preset references — parse by prefix, not by lookup

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-template-string-plugin*
*Context gathered: 2026-03-12*
