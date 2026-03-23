---
phase: 01-template-string-plugin
plan: "05"
subsystem: ui
tags: [vue, vuex, pdfme, template-expression, python, fastapi, arangodb]

# Dependency graph
requires:
  - phase: 01-template-string-plugin
    plan: "02"
    provides: "resolveExpression() function in templateResolver.js"
  - phase: 01-template-string-plugin
    plan: "03"
    provides: "linkedTemplateString plugin with template_expression linkType"

provides:
  - "PrintDialog.vue handles template_expression link type via resolveExpression() with live context values"
  - "store.dispatch('getCustomFields') called in selectTemplate() to ensure custom fields available"
  - "form.py slugify() helper matching JS implementation"
  - "create_field endpoint: HTTP 409 on slug collision"
  - "replace_field_metadata endpoint: HTTP 409 on slug collision (excluding current field)"

affects:
  - print-pipeline
  - custom-field-management

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "PrintDialog reads store.state.form.customFields after dispatching getCustomFields() — idempotent fetch"
    - "getFieldNamesAndLinks() forwards templateExpression onto link object for use in selectTemplate()"
    - "template_expression branch inserted BEFORE preset check in formModel population loop"
    - "Python slugify mirrors JS slugify: strip parens, non-alnum→underscore, trim underscores"
    - "Slug uniqueness: Python-side comparison (fetch all, slugify, compare) avoids AQL REGEX_REPLACE dependency"

key-files:
  created: []
  modified:
    - "webapps/main/src/components/PrintDialog.vue — template_expression case + resolveExpression import + getCustomFields dispatch + 409 notification"
    - "backend/api/endpoints/form.py — slugify() helper + HTTP 409 uniqueness checks in create and update endpoints"
    - "backend/api/models/form.py — FieldSpec extra='allow' + template_expression LinkType"

key-decisions:
  - "Python-side slug comparison used in form.py instead of AQL REGEX_REPLACE — avoids ArangoDB version dependency"
  - "templateExpression forwarded via getFieldNamesAndLinks() link object rather than passing full field object through separate map"
  - "getCustomFields dispatch placed at start of formModel building (before the map loop) so allCustomFields is available for all template_expression fields"
  - "FieldSpec models use extra='allow' so barcode plugin fields (bgColor, fontColor, opacity, content) survive round-trips"
  - "409 slug collision shown as user-friendly toast notification in custom field save handler"

patterns-established:
  - "Link object augmented pattern: getFieldNamesAndLinks() adds extra properties (templateExpression) to link object for downstream use"
  - "Pydantic FieldSpec models with extra='allow' for plugin-specific field preservation"

requirements-completed:
  - TMPL-05

# Metrics
duration: 2min
completed: 2026-03-12
---

# Phase 01 Plan 05: PrintDialog template_expression wiring + backend slug validation Summary

**resolveExpression() wired into PrintDialog.vue Fill Data step for live template_expression resolution, plus HTTP 409 slug uniqueness enforcement in the custom field create/update endpoints**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-03-12T15:51:40Z
- **Completed:** 2026-03-13
- **Tasks:** 2 automated + 1 human checkpoint (approved)
- **Files modified:** 3

## Accomplishments

- `PrintDialog.vue` now imports `resolveExpression` and `useStore`; `selectTemplate()` dispatches `getCustomFields()` then resolves `template_expression` fields against live context before showing the Fill Data step
- `getFieldNamesAndLinks()` augmented to forward `templateExpression` from the schema field onto the link object
- `form.py` gains a `slugify()` Python helper (identical algorithm to JS) and HTTP 409 responses in both `create_field` and `replace_field_metadata` when a slug collision is detected
- All 13 vitest tests remain GREEN after all changes
- Human verification passed: PrintDialog correctly pre-populates template_expression fields with resolved values; slug uniqueness returns 409 with user-facing notification; barcode fields (code128, qrcode, datamatrix) resolve and render correctly after re-saving the template

## Task Commits

Each task was committed atomically:

1. **Task 1: wire resolveExpression into PrintDialog.vue** — `39bf76a9` (feat)
2. **Task 2: slug uniqueness validation in form.py** — `ca9dc41d` (feat)
3. **Task 3: human verify checkpoint** — APPROVED (verification fixes applied during checkpoint):
   - `dd505e26` fix: add template_string FieldSpec and template_expression LinkType to backend model
   - `64a341a9` fix: allow extra fields on FieldSpec models so barcode properties are persisted
   - `6ae62b0c` feat: show notification on 409 slug conflict when saving custom fields

## Files Created/Modified

- `webapps/main/src/components/PrintDialog.vue` — added resolveExpression import, useStore, getCustomFields dispatch, template_expression branch in selectTemplate(), 409 notification on slug conflict
- `backend/api/endpoints/form.py` — added `import re`, `slugify()` helper, uniqueness checks with HTTP 409 in create_field and replace_field_metadata
- `backend/api/models/form.py` — FieldSpec models updated with extra='allow' so barcode plugin properties (bgColor, fontColor, opacity, content) survive round-trips; template_expression added as valid LinkType

## Decisions Made

- Used Python-side slug comparison in form.py (fetch all fields, slugify names in Python, compare) rather than AQL `REGEX_REPLACE` — avoids ArangoDB version dependency and is straightforward
- `getFieldNamesAndLinks()` augmentation pattern: forward `templateExpression` from the schema field into the link object, keeping the selectTemplate() mapping loop clean
- `getCustomFields` dispatch placed before the `formModel` map construction (not inside each iteration) — one fetch per template selection, not per field

## Deviations from Plan

### Auto-fixed Issues (found during human verification checkpoint)

**1. [Rule 2 - Missing Critical] Added template_string FieldSpec and template_expression LinkType to backend model**
- **Found during:** Task 3 (human verification) — schema save failing for template_expression fields
- **Issue:** Backend Pydantic models did not define FieldSpec for template_string fields or template_expression as a valid LinkType, causing validation errors on save
- **Fix:** Added template_string FieldSpec variant and template_expression to the LinkType enum in backend/api/models/form.py
- **Files modified:** `backend/api/models/form.py`
- **Committed in:** dd505e26

**2. [Rule 1 - Bug] Fixed FieldSpec models to allow extra fields so barcode properties are persisted**
- **Found during:** Task 3 (human verification) — barcode fields (code128, qrcode, datamatrix) not rendering after template re-save
- **Issue:** Pydantic FieldSpec models had strict field definitions; barcode plugin properties (bgColor, fontColor, opacity, content) were silently stripped on schema save round-trips, breaking canvas rendering
- **Fix:** Added `extra='allow'` to FieldSpec models in backend/api/models/form.py
- **Files modified:** `backend/api/models/form.py`
- **Committed in:** 64a341a9

**3. [Rule 2 - Missing Critical] Added 409 notification to custom field save handler**
- **Found during:** Task 3 (human verification) — 409 was returned correctly but UI gave no user feedback
- **Issue:** The custom field save handler did not handle 409 responses, so slug collisions were detected server-side but silently ignored in the UI
- **Fix:** Added a toast notification displayed on 409 status in the save handler
- **Files modified:** `webapps/main/src/components/PrintDialog.vue` (or custom field editor)
- **Committed in:** 6ae62b0c

---

**Total deviations:** 3 auto-fixed (1 missing model definition, 1 data persistence bug, 1 missing user feedback)
**Impact on plan:** All three fixes required for correctness and usability. Directly caused by the plan's changes — no scope creep.

## Issues Encountered

- Barcode rendering failure was only visible after re-saving and reopening the PDF — silent data loss from FieldSpec strict mode. Fixed by setting extra='allow' on FieldSpec models.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Template expression fields fully wired end-to-end: designer sets expression → DB stores encoded form → PrintDialog resolves to live values → user can override → PDF generated
- Backend slug enforcement prevents ambiguous custom field lookups caused by name collisions
- Phase 1 (Template String Plugin) is complete — all 5 plans executed and verified
- Phase 2 (ZPL Output) can begin; it may reference custom fields by slug which are now guaranteed unique

---
*Phase: 01-template-string-plugin*
*Completed: 2026-03-13*
