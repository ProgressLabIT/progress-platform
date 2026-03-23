# Phase 4: Full Integration - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire print dialog "Send to Printer" action, add printer `type` and `timeout_seconds` fields to the printer model and settings UI, configure which pdfme template is used per warehouse label type in main app warehouse settings, and migrate the warehouse app off hardcoded ZPL + `/pstprnt` (BrowserPrint) to the new print service. Also deliver `km/print-templates.md` documentation.

Browser calls the main API only (`POST /api/print-job`). The print service connects outbound — browser never calls it directly. `printServerURL` in `appConfig.js` is removed from scope (superseded by Phase 3 architectural pivot).

</domain>

<decisions>
## Implementation Decisions

### "Send to Printer" visibility & trigger

- "Send to Printer" button is visible in print dialog step 3 **when the user has a printer configured in their Pinia store preferences** — no appConfig.js flag needed
- The button resolves the printer silently from user preferences — **no printer selector dropdown** in the dialog
- Button label: `"Send to [printer name]"` (show the configured printer name)
- DIAL-01 (`printServerURL` in appConfig.js) is **superseded** — do not implement it

### Print result feedback UX

- After clicking "Send to Printer": **dialog stays open with a spinner** (printing in-progress state)
- Dialog waits for the `print-result` SSE event filtered by `job_id`
- **Timeout**: `printer.timeout_seconds + 5 seconds` — accounts for TCP timeout on service side plus async round-trip latency
- On result arrival (success or error): **dialog closes and shows a Quasar notify() toast** — success toast (positive) or error toast (negative) with the error detail
- If timeout is reached before result: close dialog and show a timeout error toast

### Printer type + timeout UI

- `type` field: required, no default — admin must explicitly select `zpl` or `pdf` when adding a printer
- `timeout_seconds` field: **configurable per printer** in `PrinterNew.vue` (numeric input, default value 5)
- `PrintersTable.vue`: show **all columns** — name, host, port, type, timeout
- `printer.timeout_seconds` is passed through the `PrintJobRequest` payload so the print service uses the per-printer timeout

### Warehouse template field mapping

- Template fields use the **existing link system** (`linkType`/`linkValue` presets) — same mechanism as the main app print dialog
- Warehouse label types become new preset contexts: `product` context provides `product.code` and `product.description`; position context provides `position.code`
- **Position label**: `position.code` is sufficient for v1 — no additional fields needed
- Warehouse app builds a minimal context object at print time from available Pinia store data and passes it to `resolveExpression` / `getPresetValue`

### Warehouse settings (WH-01)

- Template assignment per label type lives in **main app warehouse settings** (a new section within the existing warehouse settings area)
- Two label types: `product_label` and `position_label`
- Each label type has: a template selector (dropdown from existing print templates) and no other config needed

### Warehouse app print flow (WH-02/WH-03)

- `printProductLabel()` and `printPositionLabel()` in `webapps/warehouse/src/lib/print/index.js` are **replaced** — new implementations call `generateZpl()` with resolved inputs from the configured template, then POST to `/api/print-job`
- Warehouse app fetches the configured template for the label type at print time (or caches via Pinia)
- Operator UX is unchanged — same button, same click-to-print behavior, no new steps
- `BrowserPrint` and `browserprint-es` dependency is removed from the warehouse app

### Claude's Discretion

- Exact Pinia store shape for the warehouse label template config (how WH-01 settings are stored/loaded)
- Whether the warehouse app subscribes to the print-result SSE for result feedback, or shows a simple loading spinner only
- Structure of the minimal preset context object built in the warehouse app for `resolveExpression`
- Exact i18n keys for new strings

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Print dialog (main app)
- `webapps/main/src/components/PrintDialog.vue` — existing 3-step stepper; step 3 is where "Send to Printer" action goes; `onDialogOK()` is the existing submit handler
- `webapps/main/src/lib/print/index.js` — `sendToPrintService()` goes here (DIAL-05)
- `webapps/main/src/lib/print/zpl.js` — `generateZpl()` signature for ZPL path
- `webapps/main/src/lib/print/templateResolver.js` — `resolveExpression()` for template_expression fields

### Printer settings (main app)
- `webapps/main/src/components/settings/printers/PrinterNew.vue` — add `type` (required select) and `timeout_seconds` (numeric input)
- `webapps/main/src/components/settings/printers/PrintersTable.vue` — add type + timeout columns

### API contract (Phase 3 output)
- `backend/api/endpoints/print.py` — `POST /print-job` endpoint; `GET /print-jobs/stream`; result callback
- `backend/api/models/print_job.py` — `PrintJobRequest` model: `printer_host`, `printer_port`, `format`, `data`, `copies`, `timeout_seconds`

### Warehouse app print (to replace)
- `webapps/warehouse/src/lib/print/index.js` — current `printProductLabel()`, `printPositionLabel()`, `postZPL()` — all to be replaced
- `webapps/warehouse/src/components/print/PrintLabelForm.vue` — BrowserPrint usage to be removed
- `webapps/warehouse/src/components/CreateContainerForm.vue` — calls `printPositionLabel(position.code)`
- `webapps/warehouse/src/components/incoming/quantity/IncomingQuantitySelectionPage.vue` — calls `printProductLabel(incoming.product.code, incoming.product.description)`

### Notification SSE pattern (main app)
- `webapps/main/src/components/MessageThread.vue` — reference EventSource pattern: `new EventSource(api.defaults.baseURL + '/notification/{topic}', { withCredentials: false })`

### Requirements
- `.planning/REQUIREMENTS.md` — DIAL-01 (superseded), DIAL-02 through DIAL-06, SSE-01, SSE-02, WH-01, WH-02, WH-03, DOC-01

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `resolveExpression()` / `getPresetValue()` / `getCustomFieldValue()` in `templateResolver.js` — existing field resolution logic reusable for warehouse context building
- `generateZpl()` in `zpl.js` — ready to use for ZPL path; takes `template`, `inputs`, `{ dpi, quantity }`
- `generate()` from `@pdfme/generator` — existing PDF generation for PDF path
- Quasar `Notify` — existing toast notification system; used throughout the app
- `api` (Axios) from `boot/axios` — exists in both main and warehouse apps; use for `POST /print-job`
- Pinia stores in `webapps/main/src/stores/` and `webapps/warehouse/src/stores/` — user preferences and session data already loaded

### Established Patterns
- `EventSource` subscription pattern: `new EventSource(url, { withCredentials: false })` with `addEventListener(topic, handler)` — used in 8+ components
- Print dialog uses `useDialogPluginComponent()` from Quasar — `onDialogOK()` / `onDialogCancel()` / `onDialogHide()` pattern
- Settings tables use `PrintersTable.vue` + `PrinterNew.vue` pattern (table + inline add form in dialog)
- Vue3 `<script setup>` Composition API for new components; Options API only if modifying existing Options API components

### Integration Points
- `PrintDialog.vue` step 3 stepper navigation — add "Send to Printer" button alongside existing "Save" (Download PDF) button
- `PrinterNew.vue` — add `type` required select + `timeout_seconds` numeric input to the form
- `PrintersTable.vue` — add type and timeout columns
- `webapps/warehouse/src/lib/print/index.js` — replace `printProductLabel`, `printPositionLabel`, `postZPL` implementations
- Main app warehouse settings view — add label template assignment section (two selectors: product_label, position_label)

</code_context>

<specifics>
## Specific Ideas

- Warehouse template assignment stored somewhere accessible to both the main app (for config) and the warehouse app (for consuming at print time) — likely a new or extended app settings document in the DB
- The commented-out `loadPrintTemplates()` code in `IncomingQuantitySelectionPage.vue` shows prior intent — the new implementation completes what was started there

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-full-integration*
*Context gathered: 2026-03-19*
