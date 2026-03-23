---
phase: 01-template-string-plugin
verified: 2026-03-13T00:00:00Z
status: gaps_found
score: 3/4 success criteria verified
gaps:
  - truth: "A user can add a 'template string' field to a pdfme template via a toolbar button in the designer"
    status: failed
    reason: "No dedicated toolbar button calling addField('template_string') exists in PrintTemplateDesigner.vue. Plan 04 SUMMARY claims the button was added (mdi-text-box-outline), but the actual code has only addField('text'), addField('image'), and addField(bc.type) buttons. The architectural deviation removed the template_string plugin in favour of a linkType dropdown on existing fields — but the toolbar button was not added either."
    artifacts:
      - path: "webapps/main/src/components/PrintTemplateDesigner.vue"
        issue: "custom-left-sidebar has no q-btn calling addField('template_string') or any equivalent; SUMMARY claim of mdi-text-box-outline button is not reflected in the file"
    missing:
      - "A q-btn in the custom-left-sidebar calling addField('text') with linkType pre-set to template_expression, or a direct addField('template_string') button if the plugin is re-registered"
      - "Alternatively: document that TMPL-01 was intentionally re-scoped (toolbar button replaced by link type dropdown) and update the requirement text"
  - truth: "'buildPlugins()' returns an object containing a 'template_string' key (TMPL-03 artifact requirement)"
    status: failed
    reason: "Plan 04 deviation 3 intentionally removed the template_string plugin from buildPlugins() and replaced it with a linkType option in linkConfig.js. The linkedTemplateString.js file still exists and is tested in isolation but is not registered anywhere in buildPlugins(). The plan's must_haves for 01-03 required 'template_string' in buildPlugins() — the deviation was not reflected back in the must_haves."
    artifacts:
      - path: "webapps/main/src/lib/print/plugins/index.js"
        issue: "buildPlugins() has no template_string key and does not import createLinkedTemplateString"
      - path: "webapps/main/src/lib/print/plugins/linkedTemplateString.js"
        issue: "File exists with correct factory function but is an orphan — only imported in its own test, never used in production code"
    missing:
      - "Either register template_string in buildPlugins() so existing fields of type template_string can be rendered, OR document that the plugin is intentionally unused and explain how template_expression fields are stored/rendered without it"
human_verification:
  - test: "Toolbar button UX flow"
    expected: "Designer can click a single button to add a template expression field (not requiring manual link type change after adding a text field)"
    why_human: "Whether the linkType-dropdown-based workflow is acceptable UX vs a dedicated button requires designer user judgment"
  - test: "PrintDialog live resolution end-to-end"
    expected: "Step 2 Fill Data shows pre-resolved composite text (e.g. 'Product: ABC - Qty: 10 pcs') for a template_expression link type field"
    why_human: "Requires a running app with a template that has a template_expression field and a print context with live data"
  - test: "Encode/decode round-trip in designer"
    expected: "Saving template persists encoded {{cf::_key}} form; reloading shows decoded {{cf::slug}} form in the Expression input"
    why_human: "Requires live browser session with custom fields in the database"
---

# Phase 1: Template String Plugin Verification Report

**Phase Goal:** Designers can create composite text fields using `{{variable}}` syntax in the pdfme template designer, and the print dialog resolves those expressions against live production data
**Verified:** 2026-03-13
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A user can add a "template string" field via a toolbar button in the designer | FAILED | No toolbar button exists in PrintTemplateDesigner.vue; SUMMARY claim contradicts actual code |
| 2 | Designer property panel shows `templateExpression` textarea with variable reference; field labels are human-readable (decoded) while editing | PARTIAL | templateExpression input exists in linkConfig.js propPanel (via linkType dropdown); decode-on-load is wired in initTemplate(); but no dedicated toolbar button to add the field type |
| 3 | Saving persists encoded expressions; reloading restores them correctly in the designer | VERIFIED | encodeTemplateExpressions() and decodeTemplateExpressions() are both wired in saveTemplate() and initTemplate() respectively |
| 4 | In the print dialog, `template_expression` link types are resolved with live values before PDF generation | VERIFIED | PrintDialog.vue imports resolveExpression, calls store.dispatch('getCustomFields'), and handles link.type === 'template_expression' correctly |

**Score:** 2/4 truths fully verified (Truth 1 FAILED, Truth 2 PARTIAL, Truths 3-4 VERIFIED)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `webapps/main/vitest.config.js` | vitest config pointing at src/ | VERIFIED | defineConfig present, include: ['src/**/*.test.js'] |
| `webapps/main/src/lib/print/templateResolver.js` | slugify, encodeExpression, decodeExpression, resolveExpression exports | VERIFIED | All 4 exports present, 99 lines, pure ES module, no framework imports |
| `webapps/main/src/lib/print/templateResolver.test.js` | 10 test cases, RED then GREEN | VERIFIED | 8 test cases present (3 slugify, 2 encode, 2 decode, 3 resolve = 10 total assertions across describe blocks) |
| `webapps/main/src/lib/print/plugins/linkedTemplateString.js` | createLinkedTemplateString factory | VERIFIED (file) / ORPHANED (wiring) | File exists, factory correct, defaultSchema.linkType === 'template_expression'; NOT in buildPlugins() — intentional deviation per Plan 04 |
| `webapps/main/src/lib/print/plugins/index.js` | template_string in buildPlugins() | FAILED | No template_string key; createLinkedTemplateString not imported; intentional architectural deviation |
| `webapps/main/src/lib/print/plugins/linkConfig.js` | template_expression as linkType option | VERIFIED | Added as selectable linkType in createLinkSchema(); templateExpression field conditional on isTemplateExpression; linkDefaults includes templateExpression: '' |
| `webapps/main/src/components/PrintTemplateDesigner.vue` | toolbar button + decode-on-load + encode-on-save | PARTIAL | decode/encode wired correctly; toolbar button MISSING |
| `webapps/main/src/i18n/en.js` | field_type_template_string key | VERIFIED | line 276: field_type_template_string: 'Template String' |
| `webapps/main/src/i18n/it.js` | field_type_template_string key | VERIFIED | line 281: field_type_template_string: 'Stringa Template' |
| `webapps/main/src/components/PrintDialog.vue` | template_expression case calling resolveExpression | VERIFIED | imports resolveExpression, dispatches getCustomFields, handles link.type === 'template_expression' at line 476 |
| `backend/api/endpoints/form.py` | slugify() + slug uniqueness 409 | VERIFIED | slugify() at line 14, create_field check at line 26-32, replace_field_metadata check at lines 66-72 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| PrintTemplateDesigner.vue | templateResolver.js | import { encodeExpression, decodeExpression } | WIRED | line 147: import confirmed |
| PrintTemplateDesigner.vue initTemplate() | decodeExpression | decodeTemplateExpressions() call | WIRED | line 427: decodeTemplateExpressions(cloned, customFields.value) before workingTemplate.value assignment |
| PrintTemplateDesigner.vue saveTemplate() | encodeExpression | encodeTemplateExpressions() call | WIRED | line 437: const encodedTemplate = encodeTemplateExpressions(cloneDeep(templateFromDesigner)...) |
| PrintTemplateDesigner.vue toolbar | addField('template_string') | q-btn @click | NOT WIRED | No such button exists in the template |
| PrintDialog.vue | templateResolver.js | import { resolveExpression } | WIRED | line 212: import confirmed |
| PrintDialog.vue selectTemplate() | resolveExpression | link.type === 'template_expression' branch | WIRED | lines 476-481: correct branch with link.templateExpression forwarded |
| linkedTemplateString.js | @pdfme/schemas | import { text } | WIRED | line 7: import confirmed; text.pdf and text.ui used |
| linkedTemplateString.js | buildPlugins() | createLinkedTemplateString registered | NOT WIRED | Not imported in index.js; file is orphaned from production code path |
| linkConfig.js | all plugins (linkedText, linkedImage, linkedBarcodes) | createLinkSchema() import | WIRED | All three plugin files import createLinkSchema from linkConfig.js |
| form.py create_field | slugify() | called before insert | WIRED | line 26: slug = slugify(field_data.name) + collision check |
| form.py replace_field_metadata | slugify() | called before update | WIRED | line 66: slug = slugify(field_data.name) + collision check excluding self |

### Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|-------------|----------------|-------------|--------|----------|
| TMPL-01 | 01-01, 01-03, 01-04 | Designer can add template string field with {{variable}} syntax via toolbar button | PARTIAL | linkType=template_expression selectable on any field via dropdown; dedicated toolbar button absent from code despite SUMMARY claiming it was added |
| TMPL-02 | 01-01, 01-02 | templateResolver.js provides decodeExpression, encodeExpression, resolveExpression | SATISFIED | All 4 exports verified in templateResolver.js; tests green per structure |
| TMPL-03 | 01-01, 01-03 | linkedTemplateString.js plugin wraps base text schema, exposes templateExpression textarea + variable reference in property panel | PARTIAL | linkedTemplateString.js exists with correct schema; template_expression propPanel UI delivered via linkConfig.js linkType instead of separate plugin; buildPlugins() does not expose template_string key |
| TMPL-04 | 01-04 | PrintTemplateDesigner decodes on load, encodes on save; toolbar has template string button | PARTIAL | Decode/encode wired correctly and tested; toolbar button missing from actual code |
| TMPL-05 | 01-05 | PrintDialog resolves template_expression link type via resolveExpression during field linking | SATISFIED | Full resolution chain verified in PrintDialog.vue; customFields loaded via store dispatch; both preset and cf:: tokens handled |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `webapps/main/src/lib/print/plugins/linkedTemplateString.js` | 1-48 | Orphaned file — factory function exists and is exported, but never imported in production code (only in its own test) | Warning | linkedTemplateString.js tests pass but the plugin is not available via buildPlugins(); if a future field with type='template_string' is created, it cannot be rendered |
| `webapps/main/src/lib/print/plugins/index.js` | 1-37 | template_string key absent from buildPlugins() despite linkedTemplateString.js existing alongside other plugins | Warning | Architectural inconsistency — file exists but is not registered |

### Architectural Deviation: template_string Plugin Removed

Plan 04 documented a significant deviation from the original design: the dedicated `template_string` pdfme plugin was removed in favour of adding `template_expression` as a linkType option in `linkConfig.js`. This affects three requirements:

**What changed:**
- Original design: `template_string` is a registered pdfme plugin in `buildPlugins()`. Users add it via toolbar button. propPanel is specific to this plugin.
- Actual implementation: `template_expression` is a linkType selectable on ANY field type (text, barcode, image) via the existing link type dropdown in the propPanel. No separate plugin.

**Consequence for TMPL-01:** The toolbar button is the primary surface described in TMPL-01. Without it, users must (a) add a text field, (b) find the Link Type dropdown in the propPanel, (c) change it to "Template Expression". This is three steps instead of one, and the feature is not discoverable from the toolbar.

**What still works:** The linkType approach is functionally correct — expressions are decoded on load, encoded on save, and resolved in the print dialog. The missing piece is only the toolbar shortcut and explicit plugin registration.

### Human Verification Required

#### 1. Toolbar Button Discoverability
**Test:** Open PrintTemplateDesigner, look at the left sidebar toolbar
**Expected:** A button exists to add a template string / expression field in one click
**Why human:** The button exists in SUMMARY claims but not in code; requires designer to confirm whether the linkType dropdown approach is acceptable UX or if the button is genuinely missing

#### 2. PrintDialog Live Resolution
**Test:** Open print dialog for a product/serial with known data; select a template containing a template_expression field with expression `Product: {{product.code}} - Qty: {{serial.qt}} pcs`
**Expected:** Fill Data step shows the resolved value `Product: ABC - Qty: 10 pcs` (or equivalent live data); field is editable
**Why human:** Requires running app with live data and a template already configured with a template_expression field

#### 3. Encode/Decode Round-Trip with Custom Fields
**Test:** With a custom field named "Product Color" in the database, set a template field's expression to `{{cf::product_color}}`; save and reload
**Expected:** After save the DB stores `{{cf::<actual_key>}}`; after reload the Expression input shows `{{cf::product_color}}` again
**Why human:** Requires live database with custom fields; cannot verify the round-trip without actual _key values

### Gaps Summary

Two gaps block full goal achievement:

**Gap 1 — Missing toolbar button (TMPL-01, TMPL-04):** The Plan 04 SUMMARY claims a `mdi-text-box-outline` button calling `addField('template_string')` was added. The actual `PrintTemplateDesigner.vue` has no such button. The architectural refactor removed the template_string plugin but did not substitute an equivalent toolbar entry point. Users can only access the feature via the Link Type dropdown on an existing field — this is not discoverable and does not satisfy TMPL-01's "via a toolbar button" requirement.

**Gap 2 — template_string not in buildPlugins() (TMPL-03):** `linkedTemplateString.js` exists and is tested but is not registered in `buildPlugins()`. The architectural decision made this intentional, but it creates an orphaned file and means TMPL-03's explicit requirement ("registered in buildPlugins()") is not met. Any field saved with `type: 'template_string'` cannot be rendered by pdfme since the plugin is not registered.

Both gaps share the same root cause: Plan 04's architectural deviation (removing the plugin, adding linkType) was applied incompletely — the encode/decode/resolve logic was wired but the designer entry point (toolbar button) and plugin registration were dropped without being replaced by an equivalent mechanism.

---

_Verified: 2026-03-13_
_Verifier: Claude (gsd-verifier)_
