---
slug: remove-warehouse-legacy-print
status: complete
branch: DEV
committed: false
---

# Summary — Remove dead legacy print path from warehouse app

Implementation complete; **not committed** (user requested hold).

## Changed
- **Deleted** `webapps/warehouse/src/components/print/PrintLabelForm.vue` (+ empty `print/` dir) — browserprint-es based, stubbed (exported a test PDF), dead code.
- **`AppFooter.vue`** — removed all PrintLabelForm wiring: template section, import, components entry, `show_print_label`/`print_templates`/`product`/`supplier` data, the never-emitted `show-print-templates` `$bus` handler, and clean() resets. Promoted the create-container `v-else-if` → `v-if`. `hasSecondaryContent` now returns `this.show_create_container`.
- **`package.json`** — removed `browserprint-es` dependency.
- **`i18n/en.js` + `i18n/it.js`** — removed orphaned keys: `loading_printers`, `print_success`, `loading_template`, `alerts.print_error`, `alerts.template_error`. Kept flat `print_label` (used elsewhere).

## Verification
- `node` parse: package.json valid JSON; both i18n modules import cleanly (en 132 keys, it 135).
- grep: no remaining refs to `PrintLabelForm` / `browserprint` / `show-print-templates` / removed i18n keys (only pre-existing commented dead lines in `CreateContainerForm.vue`).
- `yarn lint` could NOT run — pre-existing env breakage: `.eslintrc.js` fails to load `vue` (ESM/CJS), independent of this change.

## Notes
- Active warehouse printing (product/position labels) already uses the print service (`lib/print/index.js` → `POST /print-job` → NATS → print-service). This change only removed the obsolete leftover.
- Follow-up: `yarn install` to drop browserprint-es from the lockfile before/at commit time.
