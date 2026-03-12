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
    - "webapps/main/src/components/PrintDialog.vue — template_expression case + resolveExpression import + getCustomFields dispatch"
    - "backend/api/endpoints/form.py — slugify() helper + HTTP 409 uniqueness checks in create and update endpoints"

key-decisions:
  - "Python-side slug comparison used in form.py instead of AQL REGEX_REPLACE — avoids ArangoDB version dependency"
  - "templateExpression forwarded via getFieldNamesAndLinks() link object rather than passing full field object through separate map"
  - "getCustomFields dispatch placed at start of formModel building (before the map loop) so allCustomFields is available for all template_expression fields"

patterns-established:
  - "Link object augmented pattern: getFieldNamesAndLinks() adds extra properties (templateExpression) to link object for downstream use"

requirements-completed:
  - TMPL-05

# Metrics
duration: 2min
completed: 2026-03-12
---

# Phase 01 Plan 05: PrintDialog template_expression wiring + backend slug validation Summary

**resolveExpression() wired into PrintDialog.vue Fill Data step for live template_expression resolution, plus HTTP 409 slug uniqueness enforcement in the custom field create/update endpoints**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-12T15:51:40Z
- **Completed:** 2026-03-12T15:53:15Z
- **Tasks:** 2 automated + 1 human checkpoint pending
- **Files modified:** 2

## Accomplishments

- `PrintDialog.vue` now imports `resolveExpression` and `useStore`; `selectTemplate()` dispatches `getCustomFields()` then resolves `template_expression` fields against live context before showing the Fill Data step
- `getFieldNamesAndLinks()` augmented to forward `templateExpression` from the schema field onto the link object
- `form.py` gains a `slugify()` Python helper (identical algorithm to JS) and HTTP 409 responses in both `create_field` and `replace_field_metadata` when a slug collision is detected
- All 13 vitest tests remain GREEN after all changes

## Task Commits

Each task was committed atomically:

1. **Task 1: wire resolveExpression into PrintDialog.vue** — `39bf76a9` (feat)
2. **Task 2: slug uniqueness validation in form.py** — `ca9dc41d` (feat)
3. **Task 3: human verify checkpoint** — awaiting user verification

## Files Created/Modified

- `webapps/main/src/components/PrintDialog.vue` — added resolveExpression import, useStore, getCustomFields dispatch, template_expression branch in selectTemplate()
- `backend/api/endpoints/form.py` — added `import re`, `slugify()` helper, uniqueness checks with HTTP 409 in create_field and replace_field_metadata

## Decisions Made

- Used Python-side slug comparison in form.py (fetch all fields, slugify names in Python, compare) rather than AQL `REGEX_REPLACE` — avoids ArangoDB version dependency and is straightforward
- `getFieldNamesAndLinks()` augmentation pattern: forward `templateExpression` from the schema field into the link object, keeping the selectTemplate() mapping loop clean
- `getCustomFields` dispatch placed before the `formModel` map construction (not inside each iteration) — one fetch per template selection, not per field

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Template expression fields now fully wired end-to-end: designer sets expression → DB stores encoded form → PrintDialog resolves to live values → user can override → PDF generated
- Backend slug enforcement prevents ambiguous custom field lookups caused by name collisions
- Awaiting human checkpoint verification (Task 3) before marking plan fully complete

## Self-Check: PASSED

- `webapps/main/src/components/PrintDialog.vue` — FOUND
- `backend/api/endpoints/form.py` — FOUND
- Commit `39bf76a9` — FOUND
- Commit `ca9dc41d` — FOUND

---
*Phase: 01-template-string-plugin*
*Completed: 2026-03-12*
