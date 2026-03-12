---
phase: 01-template-string-plugin
plan: "04"
subsystem: ui
tags: [pdfme, designer, template-string, encode, decode, i18n, vue]

# Dependency graph
requires:
  - phase: 01-template-string-plugin
    plan: "02"
    provides: "encodeExpression, decodeExpression, resolveExpression in templateResolver.js"
  - phase: 01-template-string-plugin
    plan: "03"
    provides: "template_string plugin registered in buildPlugins()"

provides:
  - "PrintTemplateDesigner.vue toolbar button calling addField('template_string')"
  - "decodeTemplateExpressions() helper: sets field.content to human-readable form on load"
  - "encodeTemplateExpressions() helper: encodes for storage on save (never mutates working state)"
  - "i18n keys field_type_template_string in en.js and it.js"

affects:
  - 01-template-string-plugin/05
  - print-pipeline

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Decode-on-load / encode-on-save pattern: templateExpression decoded to content for canvas; re-encoded from fresh designer.getTemplate() before API call"
    - "Deep-clone before encoding: cloneDeep(templateFromDesigner) protects workingTemplate.value from mutation"

key-files:
  created: []
  modified:
    - webapps/main/src/components/PrintTemplateDesigner.vue
    - webapps/main/src/i18n/en.js
    - webapps/main/src/i18n/it.js

key-decisions:
  - "encodeTemplateExpressions() receives an already-cloned template (cloneDeep at call site) and works on template.schemas directly — not template.template.schemas — since designer.getTemplate() returns a flat pdfme Template object"
  - "Icon mdi-text-box-outline chosen for template_string toolbar button (visually distinct from mdi-format-text used for plain text)"

patterns-established:
  - "Toolbar button pattern: flat dense square q-btn with mdi icon + q-tooltip (no :label prop — icon-only with tooltip)"

requirements-completed:
  - TMPL-01
  - TMPL-04

# Metrics
duration: 2min
completed: 2026-03-12
---

# Phase 1 Plan 04: PrintTemplateDesigner Integration Summary

**Encode/decode round-trip wired into PrintTemplateDesigner: toolbar button adds template_string fields, initTemplate() decodes on load, saveTemplate() encodes fresh copy before API call — i18n in en+it**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-12T15:47:27Z
- **Completed:** 2026-03-12T15:49:12Z
- **Tasks:** 2 automated + 1 human-verify checkpoint
- **Files modified:** 3

## Accomplishments

- Added `decodeTemplateExpressions()` and `encodeTemplateExpressions()` helpers to `PrintTemplateDesigner.vue`
- `initTemplate()` now decodes all `template_expression` fields before setting `workingTemplate.value` (canvas shows slug form)
- `saveTemplate()` encodes a fresh `designer.getTemplate()` copy before the API request (`workingTemplate.value` stays decoded)
- Added `mdi-text-box-outline` toolbar button calling `addField('template_string')` with tooltip
- Added `field_type_template_string` key to both `en.js` and `it.js`
- All 13 vitest tests remain green

## Task Commits

Each task was committed atomically:

1. **Task 1: Add decode-on-load and encode-on-save** - `d2ee0a21` (feat)
2. **Task 2: Add toolbar button and i18n keys** - `183e8162` (feat)

## Files Created/Modified

- `webapps/main/src/components/PrintTemplateDesigner.vue` - Added import, two helpers, decode call in initTemplate, encode call in saveTemplate, toolbar button
- `webapps/main/src/i18n/en.js` - Added `field_type_template_string: 'Template String'`
- `webapps/main/src/i18n/it.js` - Added `field_type_template_string: 'Stringa Template'`

## Decisions Made

- `encodeTemplateExpressions()` receives the already-cloned pdfme Template (flat object with `.schemas`) rather than the full workingTemplate wrapper (which has `.template.schemas`). This matches what `designer.getTemplate()` returns.
- Used `mdi-text-box-outline` icon for the toolbar button (available in the app's MDI icon set, visually distinct from the plain text `mdi-format-text`).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Toolbar button, decode-on-load, and encode-on-save are complete and tested
- Human verification checkpoint (Task 3) pending — user must confirm toolbar button works and encode/decode round-trip is correct in the running app
- After human approval, plan 01-05 (print-time resolveExpression integration) can proceed

## Self-Check: PASSED

- `webapps/main/src/components/PrintTemplateDesigner.vue` — FOUND (modified)
- `webapps/main/src/i18n/en.js` — FOUND (contains field_type_template_string)
- `webapps/main/src/i18n/it.js` — FOUND (contains field_type_template_string)
- Commit `d2ee0a21` — FOUND in git log
- Commit `183e8162` — FOUND in git log

---
*Phase: 01-template-string-plugin*
*Completed: 2026-03-12*
