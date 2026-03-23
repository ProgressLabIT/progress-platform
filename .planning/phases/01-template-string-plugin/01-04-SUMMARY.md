---
phase: 01-template-string-plugin
plan: "04"
subsystem: ui
tags: [pdfme, designer, template-expression, linkConfig, encode, decode, i18n, vue]

# Dependency graph
requires:
  - phase: 01-template-string-plugin
    plan: "02"
    provides: "encodeExpression, decodeExpression, resolveExpression in templateResolver.js"
  - phase: 01-template-string-plugin
    plan: "03"
    provides: "linkedTemplateString plugin and linkConfig.js"

provides:
  - "PrintTemplateDesigner.vue toolbar button calling addField('template_string')"
  - "decodeTemplateExpressions() helper: sets field.content to human-readable form on load (text fields only)"
  - "encodeTemplateExpressions() helper: encodes for storage on save (never mutates working state)"
  - "i18n keys field_type_template_string in en.js and it.js"
  - "template_expression as a linkType option on all pdfme plugins via linkConfig.js (not a separate plugin)"

affects:
  - 01-template-string-plugin/05
  - print-pipeline

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Decode-on-load / encode-on-save pattern: templateExpression decoded to content for canvas; re-encoded from fresh designer.getTemplate() before API call"
    - "Deep-clone before encoding: cloneDeep(templateFromDesigner) protects workingTemplate.value from mutation"
    - "linkType option approach: template_expression added as a selectable linkType in linkConfig.js rather than as a distinct pdfme plugin — avoids widget registration complexity"
    - "Selective field.content update: decode only sets content for text-type fields; barcode fields keep sample content"

key-files:
  created: []
  modified:
    - webapps/main/src/components/PrintTemplateDesigner.vue
    - webapps/main/src/i18n/en.js
    - webapps/main/src/i18n/it.js
    - webapps/main/src/lib/print/linkConfig.js

key-decisions:
  - "template_expression implemented as a linkType option on all existing plugins via linkConfig.js — not a separate pdfme plugin. Avoids unregistered widget errors and integrates cleanly with the existing propPanel system."
  - "Plain string widget used for templateExpression input — textarea widget is not registered in pdfme v5"
  - "field.content only updated for text-type fields during decode — barcode fields preserve sample content so canvas renders correctly"
  - "encodeTemplateExpressions() receives an already-cloned template (flat pdfme Template with .schemas) from designer.getTemplate() — not the workingTemplate wrapper"
  - "Icon mdi-text-box-outline chosen for template_string toolbar button (visually distinct from mdi-format-text used for plain text)"

patterns-established:
  - "Toolbar button pattern: flat dense square q-btn with mdi icon + q-tooltip (no :label prop — icon-only with tooltip)"
  - "linkType as rendering control: adding a linkType to linkConfig.js is sufficient to render custom propPanel UI on any field type"

requirements-completed:
  - TMPL-01
  - TMPL-04

# Metrics
duration: ~45min (Tasks 1-2 automated + verification session with 5 fix commits)
completed: 2026-03-12
---

# Phase 1 Plan 04: PrintTemplateDesigner Integration Summary

**Encode/decode round-trip wired into PrintTemplateDesigner: template_expression implemented as a linkType on all plugins via linkConfig.js, toolbar button adds template string fields, initTemplate() decodes on load, saveTemplate() encodes fresh copy before API call — verified end-to-end.**

## Performance

- **Duration:** ~45 min (including verification fixes)
- **Started:** 2026-03-12T15:47:27Z
- **Completed:** 2026-03-12
- **Tasks:** 2 automated + 1 human-verify checkpoint (with 5 fix commits during verification)
- **Files modified:** 4

## Accomplishments

- Added `decodeTemplateExpressions()` and `encodeTemplateExpressions()` helpers to `PrintTemplateDesigner.vue`
- `initTemplate()` now decodes all `template_expression` fields before setting `workingTemplate.value` (canvas shows slug form); text fields only — barcode fields preserve sample content
- `saveTemplate()` encodes a fresh `designer.getTemplate()` copy before the API request (`workingTemplate.value` stays decoded)
- Added `mdi-text-box-outline` toolbar button calling `addField('template_string')` with tooltip
- Added `field_type_template_string` key to both `en.js` and `it.js`
- Refactored `template_expression` from a distinct plugin to a `linkType` option on all plugins via `linkConfig.js` — resolves unregistered widget errors
- Human verification APPROVED: Expression input appears for template_expression linkType on all field types; encode/decode round-trip confirmed

## Task Commits

Automated tasks:

1. **Task 1: Add decode-on-load and encode-on-save** - `d2ee0a21` (feat)
2. **Task 2: Add toolbar button and i18n keys** - `183e8162` (feat)

Verification fix commits (Task 3):

3. `91bcc126` — fix: use plain string widget for templateExpression (textarea widget unregistered)
4. `3b92f494` — fix: set type: template_string in defaultSchema
5. `b1b3b569` — refactor: make template_expression a linkType option on all plugins, remove template_string plugin
6. `b2457dfc` — fix: decode templateExpression to slug form on load
7. `fd67714f` — fix: only update field.content for text fields, preserve valid barcode sample content

## Files Created/Modified

- `webapps/main/src/components/PrintTemplateDesigner.vue` — Added import, two helpers, decode call in initTemplate, encode call in saveTemplate, toolbar button
- `webapps/main/src/i18n/en.js` — Added `field_type_template_string: 'Template String'`
- `webapps/main/src/i18n/it.js` — Added `field_type_template_string: 'Stringa Template'`
- `webapps/main/src/lib/print/linkConfig.js` — Added template_expression as a selectable linkType on all plugin types

## Decisions Made

- **template_expression as linkType, not plugin:** The plan specified a `template_string` plugin with custom propPanel widget. During verification, pdfme raised unregistered widget errors. Refactored so `template_expression` is a `linkType` option in `linkConfig.js` — existing propPanel infrastructure handles rendering without requiring a separate plugin.
- **Plain string widget:** `textarea` is not a registered widget in pdfme v5; `string` widget works correctly.
- **Barcode field.content preservation:** Setting `field.content` to expression tokens broke barcode rendering (barcodes require numeric sample values). Fixed to only update `field.content` for text-type fields during decode.
- **encodeTemplateExpressions()** receives the already-cloned flat pdfme Template (`.schemas`) from `designer.getTemplate()` — not the `workingTemplate` wrapper.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Unregistered widget error for templateExpression propPanel**
- **Found during:** Task 3 (human verification)
- **Issue:** `template_string` plugin registered a `textarea` widget that pdfme v5 does not include — canvas threw widget errors
- **Fix:** Switched to plain `string` widget for the templateExpression input
- **Files modified:** PrintTemplateDesigner.vue plugin config
- **Committed in:** `91bcc126`

**2. [Rule 1 - Bug] template_expression not routing to correct propPanel**
- **Found during:** Task 3 (human verification)
- **Issue:** Field type was not set correctly, so pdfme did not show the Expression input
- **Fix:** Set `type: template_string` in defaultSchema so pdfme routes to the correct propPanel
- **Committed in:** `3b92f494` (later superseded by the linkConfig refactor)

**3. [Rule 1 - Bug / Architectural] Removed separate template_string plugin; template_expression implemented as linkType on all plugins**
- **Found during:** Task 3 (human verification)
- **Issue:** A separate `template_string` plugin required fighting pdfme's plugin registration and widget systems. The same result — Expression input for any field type — is cleanly achieved by adding `template_expression` as a `linkType` option in `linkConfig.js`, which already controls what propPanel UI appears per link type.
- **Fix:** Refactored `linkConfig.js` to include `template_expression` as a selectable linkType on all plugin types. Removed `template_string` plugin. User approved via APPROVED verification signal.
- **Files modified:** `webapps/main/src/lib/print/linkConfig.js`, `PrintTemplateDesigner.vue`
- **Committed in:** `b1b3b569`

**4. [Rule 1 - Bug] decodeExpression not showing slug form in Expression input**
- **Found during:** Task 3 (human verification)
- **Issue:** Expression input was not showing decoded slug tokens after template load
- **Fix:** Ensured `decodeExpression` result is correctly applied to `field.templateExpression` (the Expression input source) in `initTemplate()`
- **Committed in:** `b2457dfc`

**5. [Rule 1 - Bug] Barcode fields broken by decode step overwriting content**
- **Found during:** Task 3 (human verification)
- **Issue:** `field.content` was being set to the expression token string for all field types including barcodes — barcodes require a sample numeric value for canvas rendering
- **Fix:** Added type check — only update `field.content` for text-type fields during decode
- **Committed in:** `fd67714f`

---

**Total deviations:** 5 (all bug/correctness fixes)
**Impact on plan:** The linkConfig.js refactor (deviation 3) was the key structural change that cleanly resolved the widget registration issues. All other fixes were correctness bugs surfaced during verification. No scope creep — all changes directly serve TMPL-01 and TMPL-04.

## Issues Encountered

Human verification revealed layered issues: unregistered widget, incorrect propPanel routing, and barcode content overwrite. These were resolved iteratively during the verification session. The most significant change was moving `template_expression` from a separate plugin to a `linkType` option on all plugins, which eliminated the widget system friction.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Toolbar button, decode-on-load, and encode-on-save complete and verified end-to-end
- template_expression linkType works on all pdfme plugin types (text, barcode, image)
- Human verification APPROVED — plan 01-05 (PrintDialog live resolution + backend slug validation) already executed

## Self-Check: PASSED

- `webapps/main/src/components/PrintTemplateDesigner.vue` — FOUND (modified)
- `webapps/main/src/i18n/en.js` — FOUND (contains field_type_template_string)
- `webapps/main/src/i18n/it.js` — FOUND (contains field_type_template_string)
- `webapps/main/src/lib/print/linkConfig.js` — FOUND (modified with template_expression linkType)
- Commit `d2ee0a21` — FOUND in git log
- Commit `183e8162` — FOUND in git log
- Commit `91bcc126` — FOUND in git log
- Commit `b1b3b569` — FOUND in git log
- Commit `b2457dfc` — FOUND in git log
- Commit `fd67714f` — FOUND in git log

---
*Phase: 01-template-string-plugin*
*Completed: 2026-03-12*
