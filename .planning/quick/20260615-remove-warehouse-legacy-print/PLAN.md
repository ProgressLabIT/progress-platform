---
slug: remove-warehouse-legacy-print
created: 2026-06-15
branch: DEV
---

# Remove dead legacy print path from warehouse app

## Context
Warehouse already migrated product/position printing to the print service
(`lib/print/index.js` → `POST /print-job` → NATS → print-service over TCP/ZPL).
The only remaining non-migrated print code is `PrintLabelForm.vue`:
- uses `browserprint-es` (local BrowserPrint device discovery),
- has a broken/stubbed print path (generates a PDF then `exportFile('test-no-mime.pdf')`;
  the real `printer.device.sendFile(...)` is commented out),
- is dead code: its `show-print-templates` `$bus` event is never emitted anywhere.

User decision: remove it entirely (not rewrite).

## Changes
1. Delete `webapps/warehouse/src/components/print/PrintLabelForm.vue` (+ empty `print/` dir).
2. `webapps/warehouse/src/components/AppFooter.vue`: drop all PrintLabelForm wiring
   (template section, import, components entry, `show_print_label`/`print_templates`/
   `product`/`supplier` data, `show-print-templates` handler, clean() resets);
   promote the create-container `v-else-if` to `v-if`; `hasSecondaryContent` →
   `this.show_create_container`.
3. `webapps/warehouse/package.json`: remove `browserprint-es` dependency.
4. `webapps/warehouse/src/i18n/{en,it}.js`: remove now-orphaned keys
   `loading_printers`, `print_success`, `loading_template`, `alerts.print_error`,
   `alerts.template_error`. Keep flat `print_label` (used elsewhere).

## Verify
- `yarn lint` clean, no dangling references.
- grep confirms no remaining `PrintLabelForm` / `browserprint` / `show-print-templates` refs.
