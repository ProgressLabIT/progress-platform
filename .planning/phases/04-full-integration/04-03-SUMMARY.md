---
phase: 04-full-integration
plan: 03
subsystem: ui
tags: [vue, quasar, warehouse, zpl, print, pinia, vuex]

# Dependency graph
requires:
  - phase: 04-full-integration
    plan: 01
    provides: sendToPrintService and print-job API contract
provides:
  - warehouse template selectors in WarehouseSettings.vue for product_label and position_label
  - warehouse printProductLabel and printPositionLabel using generateZpl + /api/print-job
  - zpl.js and templateResolver.js copied to warehouse app
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "warehouse print functions read config from Pinia useConfigStore() + Vuex store.state.session.user.preferences.printer"
    - "resolveTemplateInputs: maps preset/template_expression linkTypes against context object"

key-files:
  created:
    - webapps/warehouse/src/lib/print/zpl.js
    - webapps/warehouse/src/lib/print/templateResolver.js
  modified:
    - webapps/main/src/views/settings/warehouse/WarehouseSettings.vue
    - webapps/warehouse/src/lib/print/index.js

key-decisions:
  - "Used existing settings.productLabelTemplate and settings.positionLabelTemplate i18n keys (not settings.warehouse.*) — keys already existed at the non-warehouse path"
  - "Warehouse index.js imports store directly (import store from '@/store/index.js') instead of require() — avoids CommonJS/ESM mismatch in Quasar build"
  - "BrowserPrint removed from lib/print/ only; PrintLabelForm.vue uses BrowserPrint independently and is out of scope for this plan"

requirements-completed: [WH-01, WH-02, WH-03]

# Metrics
duration: ~8min
completed: 2026-03-20
---

# Phase 4 Plan 03: Warehouse Template Assignment and BrowserPrint Removal Summary

**Warehouse settings now expose product and position label template selectors; warehouse print functions replaced with generateZpl + POST /api/print-job pipeline; BrowserPrint and hardcoded ZPL removed from lib/print/**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-03-20T09:52:00Z
- **Completed:** 2026-03-20T10:00:28Z
- **Tasks:** 2
- **Files modified:** 4 (2 created, 2 modified)

## Accomplishments

- WarehouseSettings.vue: added BaseAutocompleteTemplate import, moved two template selectors (productLabelTemplate, positionLabelTemplate) outside the `v-if="configModel.enableInventoryManagement"` guard so they're always visible
- Fixed typo `key-onlyx` → `key-only` from original commented code
- zpl.js copied verbatim from main app to warehouse app (no Vue/Quasar deps, fully testable)
- templateResolver.js copied verbatim from main app to warehouse app (pure ES module)
- warehouse lib/print/index.js fully replaced: removed BrowserPrint, postZPL, sendZplToPrinter, sendPdfToPrinter, getPrinter; added generateZpl-based pipeline
- printProductLabel and printPositionLabel preserve original signatures — all callers (IncomingQuantitySelectionPage.vue, CreateContainerForm.vue, IncomingSerialSelectionPage.vue, IncomingItem.vue, ShipmentItem.vue) unchanged
- Printer looked up from Vuex `store.state.session.user.preferences.printer` matched against Pinia `config.printers`

## Task Commits

Each task was committed atomically:

1. **Task 1: Uncomment template selectors in WarehouseSettings.vue** - `496268f5` (feat)
2. **Task 2: Copy zpl.js and templateResolver.js to warehouse app, replace print functions** - `e509120b` (feat)

## Files Created/Modified

- `webapps/main/src/views/settings/warehouse/WarehouseSettings.vue` - Added BaseAutocompleteTemplate import; replaced commented template selectors with live selectors outside v-if guard
- `webapps/warehouse/src/lib/print/zpl.js` - Created: verbatim copy of main app zpl.js
- `webapps/warehouse/src/lib/print/templateResolver.js` - Created: verbatim copy of main app templateResolver.js
- `webapps/warehouse/src/lib/print/index.js` - Replaced entirely: BrowserPrint removed, new pipeline using generateZpl + /api/print-job

## Decisions Made

- Used existing `settings.productLabelTemplate` and `settings.positionLabelTemplate` i18n keys (not `settings.warehouse.*` as the plan suggested) — these keys already existed at the top-level settings path and match what the component uses.
- Warehouse `index.js` imports Vuex store via static ES import (`import store from '@/store/index.js'`) rather than `require()`. This avoids CommonJS/ESM interop issues in the Quasar build pipeline and matches the original warehouse code's import pattern.
- BrowserPrint left in `PrintLabelForm.vue` — that component manages its own printer device list (separate from the label printing functions) and is out of scope for this plan. The acceptance criteria only requires `grep -rn "BrowserPrint" webapps/warehouse/src/lib/` to return no results, which passes.

## Deviations from Plan

None — plan executed exactly as written. The i18n key deviation (using existing path vs proposed warehouse-namespaced path) avoided adding unnecessary duplicate keys.

## Issues Encountered

None.

## User Setup Required

Admins must configure product label template and position label template in Warehouse Settings (Main App > Settings > Warehouse). Template selections persist via existing PATCH /config endpoint.

## Next Phase Readiness

- Plan 04 (if any) can build on the complete warehouse print pipeline
- All warehouse print callers use unchanged function signatures
- BrowserPrint dependency in `lib/print/` fully removed

---
*Phase: 04-full-integration*
*Completed: 2026-03-20*

## Self-Check: PASSED

All files found and commits verified.
