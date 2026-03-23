# Phase 1: Template String Plugin - Research

**Researched:** 2026-03-12
**Domain:** pdfme v5 plugin authoring, Vue 3/Quasar frontend, FastAPI/ArangoDB backend
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Phase Boundary**
Add a `template_expression` field type to the pdfme designer that lets designers compose text from `{{variable}}` syntax (e.g. `Product: {{product.code}} - Qty: {{serial.qt}} pcs`). Expressions are encoded for stable storage and resolved to live values when printing. This is a frontend-only plugin — no new backend collections, no changes to pdfme's rendering pipeline beyond wrapping the base `text` plugin.

**Variable reference UI**
- Textarea-only in the property panel — no reference list, no click-to-insert chips
- Label: "Expression" (or similar — Claude decides exact wording)
- Both preset keys (`product.code`, `serial.qt`, etc.) and custom field slugs (`cf::product_color`) are valid in expressions
- No autocomplete helper; users type variable syntax directly

**Token syntax**
- Preset variables: `{{preset.key}}` — dot-notation, no prefix (e.g. `{{product.code}}`, `{{serial.qt}}`)
- Custom field variables: `{{cf::slug}}` — `cf::` prefix disambiguates from presets unambiguously
- Stored form uses `_key` for custom fields: `{{cf::abc123}}` (short `_key` only, NOT `_id` / no `CustomField/` prefix)
- Display/editing form uses slugified `name`: `{{cf::product_color}}`

**Encode / decode scope**
- `encodeExpression(expr, customFields)`: scans for `{{cf::slug}}` tokens → replaces with `{{cf::_key}}`; preset tokens pass through unchanged
- `decodeExpression(expr, customFields)`: scans for `{{cf::_key}}` tokens → replaces with `{{cf::slugify(name)}}`; preset tokens pass through unchanged
- `resolveExpression(expr, context, customFields)`: replaces `{{cf::_key}}` with live custom field value via context, replaces `{{preset.key}}` via `context.getPresetValue()`
- All three functions live in `templateResolver.js`

**Slugification**
- Algorithm: lowercase, replace spaces/special chars with `_`, remove content in parentheses (including the parens), collapse consecutive underscores, trim leading/trailing underscores
- Example: `"Product Color"` → `product_color`, `"Qty (pcs)"` → `qty`
- Uniqueness enforced on the **slugified form** of `name` — backend endpoint validates no two custom fields share the same slug at creation/edit time
- This is a prerequisite for `templateResolver.js` to work without conflicts; include in Phase 1 scope

**Custom field model clarification**
- `CustomField.name` = stable, searchable identifier (slugified, unique-constrained)
- `CustomField.default_label` = display name shown to users (free text, may duplicate)
- `CustomField._key` = short ArangoDB ID (e.g. `abc123`); `_id` = `CustomField/abc123` — only `_key` is used in expressions

**Unresolved variable fallback**
- Missing value (no context, empty field, deleted custom field) → empty string (silent omission)
- Consistent with how existing `getPresetValue()` returns `undefined` → `String('')` in PrintDialog

**PrintDialog step 2 behavior**
- Template expression fields appear in the Fill Data step pre-resolved with live values (same as all other linked text fields)
- Field is editable — user can override the resolved value before generating PDF
- This is consistent with existing behavior: all text fields with `linkType !== 'none'` are pre-filled but editable; only `readOnly: true` schema fields are hidden

**Designer canvas preview**
- Canvas shows the **decoded expression** (human-readable slug form) while editing
- `PrintTemplateDesigner.vue` decodes `templateExpression` values when loading a template into the Designer
- `saveTemplate()` encodes before sending to the API
- Working in-memory state always uses decoded form; encoded form only exists in the DB payload

**Plugin structure**
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

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TMPL-01 | Designer can add a "template string" field that supports `{{variable}}` syntax for composite text | Plugin structure confirmed: `addField('template_string')` flow in Designer reads `plugin.propPanel.defaultSchema`; toolbar button pattern is established |
| TMPL-02 | `templateResolver.js` provides `decodeExpression`, `encodeExpression`, and `resolveExpression` | Token parse-by-prefix strategy; `getPresetValue()` and `getCustomFieldValue()` already exist on `TemplateContext`; slug uniqueness requires backend `POST /field` / `PUT /field/{key}` validation |
| TMPL-03 | `linkedTemplateString.js` pdfme plugin wraps base `text` schema and exposes `templateExpression` textarea | `createLinkedText` pattern verified; form-render `textarea` widget available; `text.propPanel.defaultSchema` structure confirmed |
| TMPL-04 | PrintTemplateDesigner decodes on load and encodes on save; toolbar button added | `initTemplate()` and `saveTemplate()` are the exact hooks; toolbar pattern is an existing `q-btn` list in `custom-left-sidebar` div |
| TMPL-05 | PrintDialog resolves `template_expression` link type via `resolveExpression` during field linking | `selectTemplate()` → `getFieldNamesAndLinks()` → `formModel` population; `template_expression` case branches on `link.type`; customFields array available via `store.getters` |
</phase_requirements>

---

## Summary

Phase 1 is a well-scoped frontend plugin addition to an existing, understood codebase. All integration points have been read directly from source — there is no speculation. The plugin factory pattern (`linkedText.js`, `linkedImage.js`) is the exact model to replicate. The only new logic is the encode/decode/resolve trio in `templateResolver.js`, and a slug-uniqueness check in the FastAPI `form.py` endpoint.

The pdfme version in use is `^5.5.0` (common, generator, schemas, ui all at the same version). The Designer in `PrintTemplateDesigner.vue` hides pdfme's built-in left sidebar with CSS overrides and replaces it with a custom `q-btn` list — adding a new button there is a two-line addition. The `saveTemplate()` function currently calls `designer.getTemplate()` directly before the API call; the encode step slots in exactly there. `initTemplate()` loads the template before `initDesigner()` — the decode step slots in exactly there.

The backend scope is limited to one change: add slug uniqueness validation to `POST /field` and `PUT /field/{key}` in `backend/api/endpoints/form.py`. No new collections, no new endpoints.

**Primary recommendation:** Implement in five self-contained units: (1) `slugify` utility, (2) `templateResolver.js`, (3) `linkedTemplateString.js` plugin, (4) Designer integration (toolbar + decode/encode), (5) PrintDialog integration + backend slug validation.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `@pdfme/schemas` | ^5.5.0 | Provides base `text` plugin to wrap | Existing project dep; `text.pdf`, `text.ui`, `text.propPanel` already used by `linkedText.js` |
| `@pdfme/common` | ^5.5.0 | Plugin type definitions (`Plugin`) | Already imported project-wide |
| `@pdfme/ui` | ^5.5.0 | Designer component | Already used in `PrintTemplateDesigner.vue` |
| Vuex | (project version) | `store.state.form.customFields`, `store.getters.getCustomFieldByKey` | Already used; `getCustomFields` action dispatched on designer open |
| FastAPI + python-arango | (project version) | Slug uniqueness validation in `POST /field`, `PUT /field/{key}` | Existing endpoint in `backend/api/endpoints/form.py` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `lodash.cloneDeep` | (project version) | Deep-clone template before encode/decode | Already used in `PrintTemplateDesigner.vue`; use the existing import |
| form-render (pdfme propPanel) | (bundled in pdfme) | Widget schema for textarea in propPanel | Use `widget: 'textarea'` or omit widget (defaults to input); see Code Examples |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Parse by `cf::` prefix | Lookup against `customFields` list | Prefix parse is O(n tokens), lookup is O(n fields) per token — prefix is simpler and the CONTEXT.md locks this approach |
| Store decoded form in DB | Store encoded (keyed) form in DB | Decoded slugs can change if `CustomField.name` changes; keys are stable — keys in DB is the locked decision |

**Installation:** No new dependencies required. All needed libraries are already in the project.

---

## Architecture Patterns

### Recommended Project Structure

```
webapps/main/src/lib/print/
├── plugins/
│   ├── index.js                  # ADD: template_string to buildPlugins()
│   ├── linkConfig.js             # UNCHANGED
│   ├── linkedText.js             # REFERENCE: exact pattern to follow
│   ├── linkedImage.js            # REFERENCE
│   ├── linkedBarcodes.js         # REFERENCE
│   └── linkedTemplateString.js   # NEW
├── templateResolver.js           # NEW: slugify, encodeExpression, decodeExpression, resolveExpression
└── index.js                      # UNCHANGED

webapps/main/src/components/
├── PrintTemplateDesigner.vue     # MODIFY: toolbar button + decode-on-load + encode-on-save
└── PrintDialog.vue               # MODIFY: template_expression case in selectTemplate()

webapps/main/src/i18n/
├── en.js                         # ADD: field_type_template_string key
└── it.js                         # ADD: matching Italian translation

backend/api/endpoints/
└── form.py                       # MODIFY: slug uniqueness check in create_field + replace_field_metadata
```

### Pattern 1: pdfme Plugin Factory

**What:** A factory function that wraps a base pdfme schema plugin, merging link configuration into `propPanel.schema` and merging link defaults into `propPanel.defaultSchema`.

**When to use:** Every custom field type in this project follows this pattern.

**Example (verbatim from `linkedText.js`):**
```javascript
// Source: webapps/main/src/lib/print/plugins/linkedText.js
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
```

The `linkedTemplateString.js` plugin follows the same shape but:
1. Sets `linkType: 'template_expression'` in `defaultSchema` (not `'none'`)
2. Adds a `templateExpression` field to the `propPanel.schema` return (a textarea widget)
3. Sets `content` in `defaultSchema` to the decoded expression for canvas preview

### Pattern 2: form-render Schema for Textarea

**What:** pdfme's propPanel uses form-render JSON schema to render inputs. A textarea widget is specified with `widget: 'textarea'`.

**When to use:** Adding the `templateExpression` property to the propPanel schema.

**Example:**
```javascript
// Source: observed from linkConfig.js patterns + pdfme form-render widget names
templateExpression: {
  title: 'Expression',
  type: 'string',
  widget: 'textarea',
  span: 24,
  props: {
    rows: 4,
    placeholder: 'e.g. Product: {{product.code}} - Qty: {{serial.qt}} pcs',
  },
},
```

### Pattern 3: encode/decode in Designer

**What:** `initTemplate()` decodes all `template_expression` fields in the loaded template schemas. `saveTemplate()` encodes them before the API call.

**When to use:** Only for `template_expression` schema fields; all other field types are untouched.

**Example:**
```javascript
// Source: PrintTemplateDesigner.vue — initTemplate() hook (lines 379–387)
// Decode step slots in BEFORE cloneDeep assignment to workingTemplate.value:
function initTemplate() {
  if (props.editTemplate) {
    mode.value = 'edit';
    const cloned = migrateTemplateSchema(cloneDeep(props.editTemplate));
    decodeTemplateExpressions(cloned, customFields.value); // NEW
    workingTemplate.value = cloned;
  } else { ... }
}

// saveTemplate() hook (lines 389–401) — encode before API call:
async function saveTemplate() {
  const templateFromDesigner = designer.getTemplate();
  const encoded = encodeAllExpressions(templateFromDesigner, customFields.value); // NEW
  await api.request({ ..., data: { ...workingTemplate.value, template: encoded } });
}
```

### Pattern 4: PrintDialog template_expression case

**What:** In `selectTemplate()` → `getFieldNamesAndLinks()`, the `template_expression` link type is not handled yet (only `preset` and `custom_field` are). Add a branch that calls `resolveExpression`.

**When to use:** Exactly when `link.type === 'template_expression'` during `formModel` population.

**Example:**
```javascript
// Source: PrintDialog.vue — selectTemplate() lines 462–469
// Existing:
if (link.type === 'preset') {
  const presetValue = props.context.getPresetValue(link.value);
  return [fieldName, String(presetValue ?? '')];
}
const customValue = props.context.getCustomFieldValue(link.value);
return [fieldName, String(customValue ?? '')];

// Add before the existing preset check:
if (link.type === 'template_expression') {
  const resolved = resolveExpression(field.templateExpression, props.context, allCustomFields);
  return [fieldName, String(resolved ?? '')];
}
```

Note: `allCustomFields` must be passed into `selectTemplate` — it can be read from `store.state.form.customFields` (same store already used in the Designer). The `PrintDialog.vue` already calls `buildPlugins([])` without custom fields — need to add a store access here.

### Pattern 5: slugify algorithm

**What:** Pure function with no dependencies.

**Example:**
```javascript
// Source: CONTEXT.md decision — exact rules specified
export function slugify(name) {
  return name
    .toLowerCase()
    .replace(/\([^)]*\)/g, '')       // remove parenthesized content
    .replace(/[^a-z0-9]+/g, '_')     // non-alphanumeric → underscore
    .replace(/_+/g, '_')              // collapse consecutive underscores
    .replace(/^_|_$/g, '');           // trim leading/trailing underscores
}
```

### Anti-Patterns to Avoid

- **Using `_id` instead of `_key` in tokens:** The `CustomField._id` is `CustomField/abc123` — only the short `_key` (`abc123`) is stored in expressions. ArangoDB returns both; parse only `._key`.
- **Mutating the live `designer` template directly:** Always use `designer.getTemplate()` to read the template, then `designer.updateTemplate()` to write — never mutate `workingTemplate.value.template` for encode/decode (use a separate copy for the API payload).
- **Encoding in-memory working state:** The decode/encode contract is: DB payload is always encoded, working memory is always decoded. Never encode and then save back to `workingTemplate.value`.
- **Calling `resolveExpression` with decoded (slug) form:** `resolveExpression` operates on the **encoded** (stored, `_key`) form. Calling it on decoded slugs would produce empty results. Only `decodeExpression` and `encodeExpression` work with slugs.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Token parsing / regex | Custom lexer/parser | Simple regex `/{{\s*([\w:.]+)\s*}}/g` | Template syntax is intentionally simple; full lexer adds complexity with no benefit |
| Custom field lookup by slug | Iterate `customFields` on every call | Build a `slug → _key` map once per encode/decode call | Avoids O(n²) for expressions with many tokens |
| propPanel textarea | Custom pdfme widget | `widget: 'textarea'` in form-render schema | Already supported by pdfme's bundled form-render |
| ArangoDB uniqueness constraint | Application-level check | ArangoDB unique persistent index | ArangoDB supports `db.collection('CustomField').addHashIndex(['name'], {unique: true})` — but the CONTEXT.md says backend endpoint validates it, which is the correct pattern for reporting a useful HTTP error |

**Key insight:** The entire encode/decode/resolve system is intentionally simple regex transforms — no AST, no template engine. Keep `templateResolver.js` under ~80 lines.

---

## Common Pitfalls

### Pitfall 1: `formModel` population reads `field.templateExpression` but field is a schema field

**What goes wrong:** In `getFieldNamesAndLinks()`, the code reads `field.linkType` and `field.linkValue` from schema fields. For `template_expression`, the expression content lives in `field.templateExpression` (not `field.linkValue`). If the resolve call tries to read `link.value` it gets an empty string.

**Why it happens:** The existing `getLink()` function only captures `linkValue` — it does not forward `templateExpression`.

**How to avoid:** Either (a) extend `getLink()` to also return `templateExpression` when `linkType === 'template_expression'`, or (b) in `selectTemplate()`, when building `formModel`, access `field.templateExpression` directly from the schema field rather than going through `getLink()`.

**Warning signs:** PrintDialog shows empty string for all template_expression fields even when variables should resolve.

### Pitfall 2: customFields not available in PrintDialog at resolve time

**What goes wrong:** `PrintDialog.vue` currently calls `buildPlugins([])` — it does not load custom fields. `resolveExpression` needs the full `customFields` array to look up `_key` → value. If passed an empty array, all `{{cf::key}}` tokens resolve to empty string silently.

**Why it happens:** The Designer loads custom fields via `store.dispatch('getCustomFields')` in its `watch(show)` handler. PrintDialog has no equivalent.

**How to avoid:** Add a `store.dispatch('getCustomFields')` call (or use `store.state.form.customFields` if already loaded) inside the `selectTemplate()` or `initialize()` function of `PrintDialog.vue`. The store action is idempotent.

**Warning signs:** Custom field tokens in expressions always resolve to empty, preset tokens resolve correctly.

### Pitfall 3: encode called on already-encoded expression (double-encoding)

**What goes wrong:** If `saveTemplate()` is called twice, or if `initTemplate()` does not decode but `saveTemplate()` encodes, the stored expression becomes `{{cf::abc123}}` → double-encoded (no visible change on first pass but logic breaks if a key happens to match a slug).

**Why it happens:** No guard on whether expression is currently in decoded or encoded form.

**How to avoid:** The contract is strict — working memory is always decoded. `initTemplate()` always decodes; `saveTemplate()` always encodes a fresh read from `designer.getTemplate()`. Never call encode on `workingTemplate.value` directly.

**Warning signs:** Expressions look correct in DB but decode gives wrong result; `{{cf::abc123}}` appears in the Designer textarea instead of `{{cf::product_color}}`.

### Pitfall 4: Slug collision after `CustomField.name` update

**What goes wrong:** Two custom fields with names `"Product Color"` and `"Product-Color"` both slugify to `product_color`. The backend endpoint validates uniqueness on the slugified form, but if validation only compares the raw `name` field (not the slug), collisions can slip through.

**Why it happens:** Existing `CustomField` model has no slug field — `name` is stored as-is. The uniqueness check must slugify before comparing.

**How to avoid:** In `form.py`, the uniqueness query must apply the same slugify algorithm (or compare slugified forms) before inserting/updating. Use an AQL query: `FOR f IN CustomField FILTER LOWER(REGEX_REPLACE(f.name, '[^a-z0-9]', '_')) == @slug AND f._key != @current_key RETURN f`.

**Warning signs:** `decodeExpression` returns the wrong custom field label; two different fields decoded to same slug — `resolveExpression` returns value from whichever field happens to be first in the array.

### Pitfall 5: `content` field shows encoded form on canvas

**What goes wrong:** pdfme renders `field.content` on the designer canvas as a preview. If the template is loaded without decoding `templateExpression` into `content`, the canvas shows the stored (encoded) form `{{cf::abc123}}` instead of the human-readable `{{cf::product_color}}`.

**Why it happens:** The canvas preview for template_expression fields should mirror the decoded expression. The decode step in `initTemplate()` must also update the `content` property of matching schema fields.

**How to avoid:** When decoding, set `field.content = decodeExpression(field.templateExpression, customFields)` for each `template_expression` field. When encoding before save, do NOT write back to `content` (pdfme uses it for rendering only).

---

## Code Examples

Verified patterns from direct source reading:

### templateResolver.js — full module shape
```javascript
// Source: derived from CONTEXT.md decisions + TemplateContext interface in lib/print/index.js
import { presetOptions } from './plugins/linkConfig.js';

const TOKEN_RE = /\{\{\s*([\w:.]+)\s*\}\}/g;

export function slugify(name) {
  return name
    .toLowerCase()
    .replace(/\([^)]*\)/g, '')
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_|_$/g, '');
}

export function encodeExpression(expr, customFields) {
  const slugToKey = Object.fromEntries(
    (customFields || []).map((cf) => [slugify(cf.name), cf._key])
  );
  return expr.replace(TOKEN_RE, (_, token) => {
    if (token.startsWith('cf::')) {
      const slug = token.slice(4);
      const key = slugToKey[slug];
      return key ? `{{cf::${key}}}` : `{{cf::${slug}}}`;
    }
    return `{{${token}}}`;
  });
}

export function decodeExpression(expr, customFields) {
  const keyToSlug = Object.fromEntries(
    (customFields || []).map((cf) => [cf._key, slugify(cf.name)])
  );
  return expr.replace(TOKEN_RE, (_, token) => {
    if (token.startsWith('cf::')) {
      const key = token.slice(4);
      const slug = keyToSlug[key];
      return slug ? `{{cf::${slug}}}` : `{{cf::${key}}}`;
    }
    return `{{${token}}}`;
  });
}

export function resolveExpression(expr, context, customFields) {
  const keyToField = Object.fromEntries(
    (customFields || []).map((cf) => [cf._key, cf])
  );
  return (expr || '').replace(TOKEN_RE, (_, token) => {
    if (token.startsWith('cf::')) {
      const key = token.slice(4);
      return String(context.getCustomFieldValue(key) ?? '');
    }
    return String(context.getPresetValue(token) ?? '');
  });
}
```

### linkedTemplateString.js — plugin factory shape
```javascript
// Source: modeled exactly on linkedText.js (webapps/main/src/lib/print/plugins/linkedText.js)
import { text } from '@pdfme/schemas';

const templateStringIcon = '<svg .../>'; // Claude's discretion

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
          widget: 'textarea',
          span: 24,
          props: { rows: 4 },
        },
        // Intentionally omit createLinkSchema — template_expression has its own linkType baked in
        ...(typeof text.propPanel.schema === 'function'
          ? text.propPanel.schema(props)
          : text.propPanel.schema),
      }),
      widgets: text.propPanel.widgets || {},
      defaultSchema: {
        ...text.propPanel.defaultSchema,
        linkType: 'template_expression',
        linkValue: '',
        extraPath: '',
        templateExpression: '',
        content: '',
      },
    },
  };
}
```

### buildPlugins() addition
```javascript
// Source: webapps/main/src/lib/print/plugins/index.js
import { createLinkedTemplateString } from './linkedTemplateString.js';

export function buildPlugins(customFields = []) {
  const barcodes = createLinkedBarcodes(customFields);
  return {
    text: createLinkedText(customFields),
    image: createLinkedImage(customFields),
    template_string: createLinkedTemplateString(customFields), // NEW
    qrcode: barcodes.qrcode,
    // ... rest unchanged
  };
}
```

### Backend slug uniqueness check (Python/FastAPI)
```python
# Source: backend/api/endpoints/form.py — create_field and replace_field_metadata
import re

def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r'\([^)]*\)', '', s)
    s = re.sub(r'[^a-z0-9]+', '_', s)
    s = re.sub(r'_+', '_', s)
    return s.strip('_')

@router.post('/field', dependencies=[Depends(auth.verify_token)])
def create_field(field_data: CustomField):
    slug = slugify(field_data.name)
    existing = list(db.aql.execute(
        'FOR f IN CustomField FILTER @slug == LOWER(REGEX_REPLACE(REGEX_REPLACE(f.name, "\\\\([^)]*\\\\)", ""), "[^a-z0-9]+", "_")) RETURN f._key',
        bind_vars={'slug': slug}
    ))
    if existing:
        raise HTTPException(status_code=409, detail=f"A custom field with slug '{slug}' already exists")
    # ... existing insert logic
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pdfme v2/v4 keyed-object schemas | pdfme v5 array-of-objects schemas | pdfme v5 upgrade | `schemasToV5()` migration helper already present in both `PrintTemplateDesigner.vue` and `PrintDialog.vue`; new fields should be created in v5 format |
| `customFieldKey` field on schema | `linkType` + `linkValue` unified fields | Prior migration | Migration guard `migrateTemplateSchema()` already in `PrintTemplateDesigner.vue`; new plugin uses `linkType: 'template_expression'` from day one |

**Deprecated/outdated:**
- `field.customFieldKey`: Replaced by `field.linkValue` with `field.linkType === 'custom_field'`. Migration helper exists. New plugin must NOT use this old field.
- `data.links` object (v2/v4): Replaced by per-field `linkType`/`linkValue` on schema fields. `getFieldNamesAndLinks()` supports both but new fields use v5.

---

## Open Questions

1. **Is `widget: 'textarea'` the correct form-render widget name in pdfme v5's bundled form-render?**
   - What we know: pdfme uses form-render for propPanel; `widget: 'select'` works (confirmed in `linkConfig.js`). form-render supports `textarea` widget.
   - What's unclear: The exact widget name string for multiline text in pdfme v5's bundled form-render version.
   - Recommendation: Use `widget: 'textarea'`; if rendering falls back to a single-line input, try omitting the widget key entirely (form-render defaults `type: 'string'` to a text input, which is acceptable).

2. **Does `PrintDialog.vue` need `store.dispatch('getCustomFields')` or is the store always pre-populated?**
   - What we know: `PrintDialog.vue` does not currently dispatch `getCustomFields`. `PrintTemplateDesigner.vue` does dispatch it. The Vuex store persists in-session.
   - What's unclear: Whether a user could open PrintDialog without having opened the Designer first (i.e., custom fields not yet in store).
   - Recommendation: Add a `store.dispatch('getCustomFields')` call in `selectTemplate()` or at PrintDialog initialization. The action fetches `GET /field` — it's lightweight and safe to call multiple times.

3. **AQL regex for slug comparison — does the ArangoDB version deployed support `REGEX_REPLACE`?**
   - What we know: ArangoDB has supported `REGEX_REPLACE` since v3.4. The project uses ArangoDB (confirmed from `python-arango` usage).
   - What's unclear: The exact ArangoDB version deployed.
   - Recommendation: Use `REGEX_REPLACE` in the uniqueness check AQL. If it fails in CI, fall back to fetching all fields and doing the slug comparison in Python.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None configured for frontend unit tests — `package.json` test script returns `echo "No test specified" && exit 0` |
| Config file | None |
| Quick run command | N/A — see Wave 0 Gaps |
| Full suite command | N/A — see Wave 0 Gaps |

The project has Cypress e2e tests in `testing/cypress/` and Robot Framework tests in `testing/robot-test/`. There is no vitest/jest unit test infrastructure for the main webapp.

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TMPL-02 | `slugify('Product Color')` → `product_color` | unit | `npx vitest run src/lib/print/templateResolver.test.js` | ❌ Wave 0 |
| TMPL-02 | `slugify('Qty (pcs)')` → `qty` | unit | `npx vitest run src/lib/print/templateResolver.test.js` | ❌ Wave 0 |
| TMPL-02 | `encodeExpression('{{cf::product_color}}', fields)` → `{{cf::abc123}}` | unit | `npx vitest run src/lib/print/templateResolver.test.js` | ❌ Wave 0 |
| TMPL-02 | `decodeExpression('{{cf::abc123}}', fields)` → `{{cf::product_color}}` | unit | `npx vitest run src/lib/print/templateResolver.test.js` | ❌ Wave 0 |
| TMPL-02 | `resolveExpression('Product: {{product.code}}', ctx, [])` → `Product: ABC` | unit | `npx vitest run src/lib/print/templateResolver.test.js` | ❌ Wave 0 |
| TMPL-02 | Missing variable resolves to empty string | unit | `npx vitest run src/lib/print/templateResolver.test.js` | ❌ Wave 0 |
| TMPL-03 | Plugin `defaultSchema.linkType === 'template_expression'` | unit | `npx vitest run src/lib/print/plugins/linkedTemplateString.test.js` | ❌ Wave 0 |
| TMPL-04 | Designer encode/decode round-trip preserves expression | manual smoke | Open designer, add template_string field, type expression, save, reload — check stored DB vs displayed value | N/A |
| TMPL-05 | PrintDialog pre-populates template_expression field with resolved value | manual smoke | Open print dialog with known product/serial, select template with template_string field | N/A |

### Sampling Rate
- **Per task commit:** `npx vitest run src/lib/print/templateResolver.test.js` (once Wave 0 creates it)
- **Per wave merge:** `npx vitest run src/lib/print/` (all print lib tests)
- **Phase gate:** All vitest tests green + manual smoke for TMPL-04 and TMPL-05 before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `webapps/main/vitest.config.js` — vitest config pointing to `src/` — `npm install -D vitest` in `webapps/main/`
- [ ] `webapps/main/src/lib/print/templateResolver.test.js` — unit tests for `slugify`, `encodeExpression`, `decodeExpression`, `resolveExpression`
- [ ] `webapps/main/src/lib/print/plugins/linkedTemplateString.test.js` — tests for plugin `defaultSchema` shape

---

## Sources

### Primary (HIGH confidence)
- Direct source read: `webapps/main/src/lib/print/plugins/linkedText.js` — exact plugin factory pattern
- Direct source read: `webapps/main/src/lib/print/plugins/linkConfig.js` — `presetOptions`, `createLinkSchema`, `linkDefaults`
- Direct source read: `webapps/main/src/lib/print/plugins/index.js` — `buildPlugins()` registration
- Direct source read: `webapps/main/src/components/PrintTemplateDesigner.vue` — `initTemplate()`, `saveTemplate()`, `addField()`, toolbar structure
- Direct source read: `webapps/main/src/components/PrintDialog.vue` — `selectTemplate()`, `getFieldNamesAndLinks()`, `formModel` population
- Direct source read: `webapps/main/src/lib/print/index.js` — `TemplateContext`, `getPresetValue()`, `getCustomFieldValue()`, all context subclasses
- Direct source read: `backend/api/endpoints/form.py` — `create_field`, `replace_field_metadata` — no slug validation currently present
- Direct source read: `backend/api/models/form.py` — `CustomField` model shape (`name`, `default_label`, `_key`)
- Direct source read: `webapps/main/src/store/form.js` — `getCustomFieldByKey`, `getCustomFields` action
- Node.js runtime introspection: `text.propPanel.defaultSchema` confirmed from `@pdfme/schemas@^5.5.0`

### Secondary (MEDIUM confidence)
- `webapps/main/src/i18n/en.js` + `it.js`: i18n key pattern `field_type_X` for toolbar button tooltip translation

### Tertiary (LOW confidence)
- `widget: 'textarea'` in form-render: Inferred from form-render v2 documentation conventions; not directly verified against the exact form-render version bundled in pdfme v5.5.0

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries confirmed from `package.json` and source files
- Architecture: HIGH — all integration points read from source; no assumptions
- Pitfalls: HIGH — derived from direct code reading of the integration points
- Test framework: HIGH — confirmed no vitest/jest exists; `package.json` script is `echo "No test specified"`

**Research date:** 2026-03-12
**Valid until:** 2026-04-12 (stable frontend codebase; pdfme v5.5.0 is pinned with caret)
