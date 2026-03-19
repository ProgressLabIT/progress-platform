# Phase 4: Full Integration - Research

**Researched:** 2026-03-19
**Domain:** Vue 3 + Quasar (print dialog), Pinia stores, SSE (EventSource), FastAPI (config), warehouse app migration
**Confidence:** HIGH

## Summary

Phase 4 wires the print pipeline end-to-end. The backend API and print service infrastructure are done (Phase 3). This phase adds the "Send to Printer" button to `PrintDialog.vue`, extends the printer model with `type` and `timeout_seconds`, unhides the label template assignment UI in `WarehouseSettings.vue`, and replaces the hardcoded ZPL + `/pstprnt` calls in the warehouse app with new implementations that call `generateZpl()` + `POST /api/print-job`. SSE feedback loops via the existing `/notification/print-result` pattern.

The most important discovery is that the config layer already has `productLabelTemplate` and `positionLabelTemplate` fields in both the main app config store (`useConfigStore`) and the warehouse config store, with corresponding API mappings (`product_label_template`, `position_label_template`). The warehouse settings view already has the template selector UI commented out. The backend `PATCH /config` endpoint is a schemaless key-value store — any key can be sent as a string value. This means WH-01 requires only uncommenting/enabling existing code, not building new backend endpoints.

The second key discovery is the printer preference shape: `user.preferences.printer` stores a `"host:port"` string (e.g. `"192.168.1.10:9100"`), not a printer key or full object. The "Send to Printer" button must resolve the full printer object from `config.printers` by matching `"${printer.host}:${printer.port}"` — this enables accessing `printer.name` for the button label, `printer.type` for ZPL vs PDF path, and `printer.timeout_seconds` for SSE timeout calculation.

**Primary recommendation:** Implement all five work areas in order — (1) DIAL-02 printer model fields, (2) DIAL-05/06 print lib + dialog wiring, (3) SSE-01/SSE-02 feedback, (4) WH-01 settings, (5) WH-02/WH-03 warehouse lib replacement, then DOC-01.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**"Send to Printer" visibility & trigger**
- "Send to Printer" button is visible in print dialog step 3 when the user has a printer configured in their Pinia store preferences — no appConfig.js flag needed
- The button resolves the printer silently from user preferences — no printer selector dropdown in the dialog
- Button label: "Send to [printer name]" (show the configured printer name)
- DIAL-01 (printServerURL in appConfig.js) is superseded — do not implement it

**Print result feedback UX**
- After clicking "Send to Printer": dialog stays open with a spinner (printing in-progress state)
- Dialog waits for the `print-result` SSE event filtered by `job_id`
- Timeout: `printer.timeout_seconds + 5 seconds` — accounts for TCP timeout on service side plus async round-trip latency
- On result arrival (success or error): dialog closes and shows a Quasar notify() toast — success toast (positive) or error toast (negative) with the error detail
- If timeout is reached before result: close dialog and show a timeout error toast

**Printer type + timeout UI**
- `type` field: required, no default — admin must explicitly select `zpl` or `pdf` when adding a printer
- `timeout_seconds` field: configurable per printer in `PrinterNew.vue` (numeric input, default value 5)
- `PrintersTable.vue`: show all columns — name, host, port, type, timeout
- `printer.timeout_seconds` is passed through the `PrintJobRequest` payload

**Warehouse template field mapping**
- Template fields use the existing link system (`linkType`/`linkValue` presets) — same mechanism as the main app print dialog
- Warehouse label types become new preset contexts: `product` context provides `product.code` and `product.description`; position context provides `position.code`
- Position label: `position.code` is sufficient for v1
- Warehouse app builds a minimal context object at print time from available Pinia store data and passes it to `resolveExpression` / `getPresetValue`

**Warehouse settings (WH-01)**
- Template assignment per label type lives in main app warehouse settings (a new section within the existing warehouse settings area)
- Two label types: `product_label` and `position_label`
- Each label type has: a template selector (dropdown from existing print templates) and no other config needed

**Warehouse app print flow (WH-02/WH-03)**
- `printProductLabel()` and `printPositionLabel()` in `webapps/warehouse/src/lib/print/index.js` are replaced — new implementations call `generateZpl()` with resolved inputs from the configured template, then POST to `/api/print-job`
- Warehouse app fetches the configured template for the label type at print time (or caches via Pinia)
- Operator UX is unchanged — same button, same click-to-print behavior, no new steps
- `BrowserPrint` and `browserprint-es` dependency is removed from the warehouse app

### Claude's Discretion
- Exact Pinia store shape for the warehouse label template config (how WH-01 settings are stored/loaded)
- Whether the warehouse app subscribes to the print-result SSE for result feedback, or shows a simple loading spinner only
- Structure of the minimal preset context object built in the warehouse app for `resolveExpression`
- Exact i18n keys for new strings

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DIAL-01 | printServerURL in appConfig.js — SUPERSEDED, do not implement | n/a |
| DIAL-02 | Printer model `type` + `timeout_seconds` fields; PrinterNew.vue + PrintersTable.vue updated | PrinterNew.vue is Options API / `<script setup>` Vue3; both emit-based; field add is mechanical |
| DIAL-03 | Print dialog step 3 "Send to Printer" action — superseded UX from DIAL-01; actual decision is button visible when user has configured printer | PrintDialog.vue step 2 (`activeStep === 2`) has the "Save" button in `q-stepper-navigation`; add alongside it |
| DIAL-04 | "Download PDF" button (existing "Save" button) preserved | Already exists; must not be removed |
| DIAL-05 | `sendToPrintService({ data, printer, format, copies })` in `lib/print/index.js` | `api` axios is already imported; `POST /api/print-job` contract confirmed in print.py |
| DIAL-06 | PrintDialog OK handler: type=zpl → generateZpl() → send; type=pdf → generate() → base64 → send | Both generation paths exist; `generateZpl()` in zpl.js, `generate()` from @pdfme/generator |
| SSE-01 | Frontend subscribes to `/notification/print-result` SSE after submitting print job | EventSource pattern confirmed in MessageThread.vue; print-result subtopic in print.py |
| SSE-02 | Frontend filters "print-result" events by `job_id` | PrintJobResult payload includes `job_id`; filter in handler |
| WH-01 | Main app settings: configure pdfme template per warehouse label type | WarehouseSettings.vue has commented-out template selectors; config store already has `productLabelTemplate` / `positionLabelTemplate`; PATCH /config supports string keys |
| WH-02 | Warehouse app uses configured templates + print service instead of hardcoded ZPL + /pstprnt | `printProductLabel()` / `printPositionLabel()` in warehouse lib/print/index.js to be replaced; `generateZpl()` from main app zpl.js usable in node environment |
| WH-03 | Warehouse operator UX unchanged — click-to-print behavior identical | Same function signatures; callers not modified |
| DOC-01 | `km/print-templates.md` updated with all new capabilities | File exists at `km/domains/printing/print-templates.md`; needs sections on ZPL transpiler, print service, printer type, template assignment |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Quasar (q-btn, Notify, useDialogPluginComponent) | existing | Dialog controls, toast notifications | Already used throughout PrintDialog.vue |
| Pinia (useConfigStore, session Vuex store) | existing | Config + user preferences | Printers in config.printers; user printer pref in session.user.preferences.printer |
| EventSource (browser native) | native | SSE subscription to /notification/print-result | Pattern established in MessageThread.vue |
| @pdfme/generator generate() | existing | PDF generation for PDF-type printers | Already used in PrintDialog.vue |
| generateZpl() from zpl.js | existing | ZPL generation for ZPL-type printers | Completed in Phase 2; takes (template, inputs, { dpi, quantity }) |
| api (Axios) from boot/axios | existing | POST /api/print-job | Imported in both main and warehouse apps |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| resolveExpression() from templateResolver.js | existing | Resolve template_expression fields in warehouse context | Building minimal context object for warehouse print |
| cloneDeep (lodash) | existing | Safe copy of config for reactive editing | Already used in WarehouseSettings.vue and PrintersLibrary.vue |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Native EventSource | Axios streaming | EventSource is browser-native and matches existing pattern exactly |
| Computed `selectedPrinter` in dialog | Props drilling | Computed from config.printers + session.user.preferences.printer is cleaner, no prop changes needed |

**Installation:** No new packages required. All dependencies already present.

## Architecture Patterns

### Recommended Project Structure
No new directories required. Changes are contained to:
```
webapps/main/src/
├── components/
│   ├── PrintDialog.vue           # Add "Send to Printer" button + spinner state
│   └── settings/printers/
│       ├── PrinterNew.vue        # Add type (required select) + timeout_seconds (numeric input)
│       └── PrintersTable.vue     # Add type + timeout columns
├── lib/print/
│   └── index.js                  # Add sendToPrintService(), resolvePrinterFromPreference()
└── views/settings/warehouse/
    └── WarehouseSettings.vue     # Uncomment template selectors; save to config

webapps/warehouse/src/
└── lib/print/
    └── index.js                  # Replace printProductLabel(), printPositionLabel(), remove postZPL()

km/domains/printing/
└── print-templates.md            # Add ZPL/print service/printer type/template assignment sections
```

### Pattern 1: Resolve Printer Object from Preference String
**What:** `user.preferences.printer` stores `"host:port"` (e.g. `"192.168.1.10:9100"`). Match against `config.printers` array to get the full object including `name`, `type`, and `timeout_seconds`.
**When to use:** In PrintDialog.vue `computed` to derive `selectedPrinter`; in warehouse lib to fetch the user's configured printer.
**Example:**
```javascript
// In PrintDialog.vue (script setup context - use Vuex store + useConfigStore)
import { useStore } from 'vuex';
import { useConfigStore } from '@/stores/config';
import { computed } from 'vue';

const store = useStore();
const { config } = useConfigStore();

const selectedPrinter = computed(() => {
  const prefValue = store.state.session.user.preferences?.printer; // "host:port"
  if (!prefValue) return null;
  return config.printers.find(p => `${p.host}:${p.port}` === prefValue) ?? null;
});
```

### Pattern 2: SSE Subscribe + job_id Filter + Timeout
**What:** Open EventSource on `/notification/print-result`, listen for events, filter by `job_id`, close on first match or timeout.
**When to use:** After `POST /api/print-job` returns `{ job_id }` in PrintDialog step 3.
**Example:**
```javascript
// Source: print.py print_job_result handler + MessageThread.vue EventSource pattern
function waitForPrintResult(jobId, timeoutMs) {
  return new Promise((resolve) => {
    const url = api.defaults.baseURL + '/notification/print-result';
    const source = new EventSource(url, { withCredentials: false });
    const timer = setTimeout(() => {
      source.close();
      resolve({ ok: false, error: 'timeout', detail: null });
    }, timeoutMs);

    source.addEventListener('print-result', (event) => {
      const data = JSON.parse(event.data);
      if (data.job_id === jobId) {
        clearTimeout(timer);
        source.close();
        resolve({ ok: data.ok, error: data.error, detail: data.detail });
      }
    });
  });
}
```

### Pattern 3: PrintDialog "Send to Printer" State Machine
**What:** Step 3 has three visual states: default (show "Save" + "Send to [name]"), printing (spinner, buttons hidden), result (handled by dialog close + toast).
**When to use:** Manage with a `isPrinting` ref inside PrintDialog.vue.
**Example:**
```javascript
const isPrinting = ref(false);

async function sendToPrinter() {
  isPrinting.value = true;
  try {
    const { job_id } = await sendToPrintService({ ... });
    const timeoutMs = (selectedPrinter.value.timeout_seconds + 5) * 1000;
    const result = await waitForPrintResult(job_id, timeoutMs);
    onDialogHide(); // close dialog first
    if (result.ok) {
      Notify.create({ type: 'positive', message: t('printDialog.sendToPrinter.success') });
    } else {
      Notify.create({ type: 'negative', message: result.detail || result.error });
    }
  } catch (err) {
    onDialogHide();
    Notify.create({ type: 'negative', message: err.message });
  } finally {
    isPrinting.value = false;
  }
}
```

### Pattern 4: Warehouse Minimal Context Object
**What:** Build a minimal context object implementing `getPresetValue()` so `resolveExpression()` can resolve `product.code`, `product.description`, `position.code` tokens.
**When to use:** In `printProductLabel()` and `printPositionLabel()` in warehouse lib/print/index.js.
**Example:**
```javascript
// Warehouse product context
function buildProductContext(product) {
  return {
    getPresetValue(key) {
      if (key === 'product.code') return product.code;
      if (key === 'product.description') return product.description;
      return undefined;
    },
    getCustomFieldValue() { return undefined; },
  };
}

// Warehouse position context
function buildPositionContext(position) {
  return {
    getPresetValue(key) {
      if (key === 'position.code') return position.code ?? position;
      return undefined;
    },
    getCustomFieldValue() { return undefined; },
  };
}
```

### Pattern 5: generateZpl() Inputs Preparation for Warehouse
**What:** Resolve all field values from template + context, pass as flat inputs array (one object per page).
**When to use:** After fetching template details in warehouse print functions.
**Example:**
```javascript
import { resolveExpression } from '@/lib/print/templateResolver.js'; // relative import
// generateZpl takes (template, inputs, { dpi, quantity })
// inputs must be array of { fieldName: resolvedValue } per page

function prepareWarehouseInputs(template, context) {
  return template.template.schemas.map(pageSchema => {
    const fields = normalizePageSchema(pageSchema);
    return Object.fromEntries(
      fields.map(field => {
        let value = '';
        if (field.linkType === 'preset' && field.linkValue) {
          value = context.getPresetValue(field.linkValue) ?? '';
        } else if (field.linkType === 'template_expression' && field.templateExpression) {
          value = resolveExpression(field.templateExpression, context, []) ?? '';
        }
        return [field.name, String(value)];
      })
    );
  });
}
```

### Pattern 6: WH-01 Config Wiring — Already Partially Built
**What:** `WarehouseSettings.vue` has the template selector UI commented out. `useConfigStore` (main app) and `useConfigStore` (warehouse app) already have `productLabelTemplate` and `positionLabelTemplate` fields. `updateAppConfig()` already sends `product_label_template` and `position_label_template` to `PATCH /config`. Backend stores string values by key.
**When to use:** Implementing WH-01 — primarily uncomment + wire the two selectors.
**Key gap:** The warehouse app's `config.js` store maps `product_label_template` and `position_label_template` from the API, but `updateAppConfig()` does NOT currently send them. The main app's config store does. The main app's `WarehouseSettings.vue` save function already includes them in the update object.

### Anti-Patterns to Avoid
- **Opening EventSource before POST completes:** The `job_id` is needed to filter; subscribe only after the POST returns.
- **Not closing EventSource on component unmount or timeout:** Memory/connection leak. Always close in the timeout handler and the success/error path.
- **Printer type check on undefined:** `selectedPrinter` may be null (user has no printer configured); guard before showing "Send to Printer" button.
- **Passing `printer.host:printer.port` string to the Vuex dispatch for preferences:** The preference stores `"host:port"` as a raw string. Resolving back to the full object is a lookup, not a parse.
- **Keeping BrowserPrint import in warehouse:** After replacing the lib, also remove `BrowserPrint` from `PrintLabelForm.vue` — it has its own `loadPrinters()` call using BrowserPrint.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Toast notifications | Custom alert/modal | Quasar `Notify.create({ type: 'positive'|'negative', message })` | Already used throughout the app |
| PDF generation | Custom renderer | `generate()` from `@pdfme/generator` with `buildPlugins([])` | Phase 1/2 output; handles all field types |
| ZPL generation | Custom ZPL string builder | `generateZpl(template, inputs, { dpi, quantity })` in `lib/print/zpl.js` | Phase 2 output; handles all supported field types |
| Template expression resolution | Custom parser | `resolveExpression()` from `templateResolver.js` | Phase 1 output; handles `{{token}}` syntax |
| Print job submission | Direct TCP from browser | `POST /api/print-job` via Axios | Phase 3 output; main API relays via SSE to print service |
| SSE event routing | Custom WebSocket | Native `EventSource` | Browser native; established pattern in codebase |

**Key insight:** All the building blocks exist. Phase 4 is integration work — wiring existing pieces together, not building new infrastructure.

## Common Pitfalls

### Pitfall 1: PrintersTable.vue is Options API
**What goes wrong:** Implementing `type` and `timeout_seconds` columns with `<script setup>` syntax inside an Options API component causes an error.
**Why it happens:** `PrintersTable.vue` uses `export default { ... }` (Options API), not `<script setup>`.
**How to avoid:** Keep using Options API patterns when modifying `PrintersTable.vue`. `PrinterNew.vue` is already `<script setup>` — that one can stay.
**Warning signs:** Missing `this.` prefix on data/methods, missing `components:` registration.

### Pitfall 2: Printer preference is "host:port" string, not a printer key
**What goes wrong:** Looking for `config.printers.find(p => p._key === preference)` returns nothing.
**Why it happens:** `AppBar.vue` stores `${printer.host}:${printer.port}` as the preference value (confirmed in AppBar.vue line 283).
**How to avoid:** Match with `` `${p.host}:${p.port}` === prefValue ``.
**Warning signs:** `selectedPrinter` always null despite user having a printer set.

### Pitfall 3: SSE topic name is "print-result", not the URL path segment
**What goes wrong:** Subscribing to `addEventListener('print-jobs', ...)` instead of `addEventListener('print-result', ...)`.
**Why it happens:** The URL is `/notification/print-result` but the SSE event type comes from the `subtopic` field in the enqueued payload (`"subtopic": "print-result"`).
**How to avoid:** Use `source.addEventListener('print-result', handler)` — the event type matches the subtopic, not the full URL path.
**Warning signs:** SSE connection opens but no events are received.

### Pitfall 4: PrintDialog.vue uses `useStore()` (Vuex), not Pinia for session
**What goes wrong:** Importing `useSessionStore` from Pinia (doesn't exist) instead of `useStore()` from Vuex.
**Why it happens:** The main app uses Vuex for session (`store.state.session.user.preferences`) but Pinia for config (`useConfigStore()`). Both coexist.
**How to avoid:** `const store = useStore()` for session/user preferences; `const { config } = useConfigStore()` for printers list.
**Warning signs:** `useSessionStore is not a function` or undefined preferences.

### Pitfall 5: generateZpl() in warehouse app has no Vue/Quasar dependencies
**What goes wrong:** Importing `generateZpl` from a path that transitively imports Vue/Quasar causes Vitest failures or build errors.
**Why it happens:** `zpl.js` was intentionally kept free of Vue/Quasar imports (Phase 2 decision). The warehouse app must import it directly, not via `index.js` which has Quasar imports.
**How to avoid:** In the warehouse app, import from `@/lib/print/zpl.js` (or the equivalent relative path to zpl.js) not from `@/lib/print/index.js` if index.js has Vue/Quasar boot dependencies.
**Warning signs:** `Cannot resolve module 'quasar'` in warehouse build.

### Pitfall 6: WarehouseSettings.vue template selectors are commented inside `v-if="configModel.enableInventoryManagement"`
**What goes wrong:** Uncommented template selectors are invisible when `enableInventoryManagement` is false.
**Why it happens:** The existing commented-out code is inside the `<template v-if="configModel.enableInventoryManagement">` block.
**How to avoid:** Move the template selectors OUTSIDE the `v-if` block — label template config is independent of the inventory management feature toggle.
**Warning signs:** Template dropdowns don't appear in warehouse settings even after uncommenting.

### Pitfall 7: Warehouse app does not have zpl.js
**What goes wrong:** Trying to use `generateZpl()` without access to the function.
**Why it happens:** `zpl.js` lives in the main app at `webapps/main/src/lib/print/zpl.js`. The warehouse app is a separate Quasar project.
**How to avoid:** Copy `zpl.js` and its dependency `templateResolver.js` (for `resolveExpression`) to the warehouse app under `webapps/warehouse/src/lib/print/`. The warehouse app already has `webapps/warehouse/src/lib/print/` containing `index.js`. Alternatively, use a shared package — but copying is simpler given the existing file layout.

## Code Examples

Verified patterns from existing code:

### EventSource subscription (from MessageThread.vue, line 135-142)
```javascript
// Source: webapps/main/src/components/MessageThread.vue
onMounted(() => {
  let eventURL = api.defaults.baseURL + '/notification/global-notification';
  events.value = new EventSource(eventURL, { withCredentials: false });
  events.value.addEventListener('global-notification', (event) => {
    handleMessage(event);
  });
});
onUnmounted(() => {
  if (events.value) { events.value.close(); }
});
```

### PrintJobRequest API contract (from backend/api/models/print_job.py)
```python
class PrintJobRequest(BaseModel):
    printer_host: str
    printer_port: int = 9100
    format: PrintFormat         # "zpl" or "pdf"
    data: str                   # ZPL text or base64-encoded PDF
    copies: int = 1
    timeout_seconds: float = 5.0
```

### POST /print-job response (from backend/api/endpoints/print.py line 199-208)
```python
# POST /print-job returns { "job_id": "uuid-string" }
# PrintJobResult SSE payload (subtopic "print-result"):
{
  "subtopic": "print-result",
  "job_id": "uuid-string",
  "ok": true,
  "error": null,     # "connection_refused" | "timeout" | "send_error" | null
  "detail": null     # human-readable detail string or null
}
```

### Config PATCH — storing label template keys (from config.py)
```python
# PATCH /config with dict body; string values stored as { _key: key, value: value }
# e.g. { "product_label_template": "abc123", "position_label_template": "def456" }
# Retrieved via GET /config which returns { product_label_template: "abc123", ... }
```

### generateZpl() signature (from zpl.js)
```javascript
// Source: webapps/main/src/lib/print/zpl.js
// generateZpl(template, inputs, options)
// template: pdfme template object ({ basePdf, schemas })
// inputs: array of { fieldName: value } objects, one per page
// options: { dpi?: number, quantity?: number }
// returns: ZPL string
```

### Quasar notify pattern (established usage)
```javascript
// Source: existing usage throughout main app
Notify.create({ type: 'positive', message: t('printDialog.sendToPrinter.success') });
Notify.create({ type: 'negative', message: errorDetail || t('printDialog.sendToPrinter.error') });
```

### PDF to base64 for print service
```javascript
// generate() returns Uint8Array; must convert to base64 string for PrintJobRequest.data
const pdfBytes = await generate({ template: cleanTemplate, inputs, plugins: pdfmePlugins });
const base64 = btoa(String.fromCharCode(...pdfBytes));
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded ZPL + /pstprnt (BrowserPrint) in warehouse | generateZpl() + POST /api/print-job | Phase 4 | Removes Zebra proprietary dependency; printer-agnostic |
| No type field on printer model | `type: 'zpl' | 'pdf'` required field | Phase 4 | Enables ZPL vs PDF routing in print dialog |
| No timeout on printer model | `timeout_seconds` per printer (default 5) | Phase 4 | Correct SSE wait time per printer TCP characteristics |
| Browser calls print service directly | Browser → main API → SSE → print service | Phase 3 pivot | Printer auth/firewall resolved; all traffic via main API |

**Deprecated/outdated:**
- `browserprint-es` import in warehouse app: to be removed from `PrintLabelForm.vue` and `lib/print/index.js`
- `postZPL()` function in warehouse `lib/print/index.js`: to be deleted (used `/pstprnt` endpoint)
- `sendZplToPrinter()` and `sendPdfToPrinter()` via BrowserPrint device: to be deleted
- DIAL-01 (`printServerURL` in appConfig.js): superseded by Phase 3 pivot, never implement

## Open Questions

1. **BaseAutocompleteTemplate component availability in WarehouseSettings.vue**
   - What we know: `WarehouseSettings.vue` has commented-out `<BaseAutocompleteTemplate>` component with full props. The import is also commented out.
   - What's unclear: Whether `BaseAutocompleteTemplate.vue` exists in the main app and is ready to use, or was never built.
   - Recommendation: Before implementing WH-01, verify the component exists at `@/components/BaseAutocompleteTemplate.vue`. If it doesn't exist, implement as a simple `q-select` populated from `api.get('print-template')`.

2. **Warehouse app access to main app's zpl.js and templateResolver.js**
   - What we know: Both files are in `webapps/main/src/lib/print/`. The warehouse app is a separate Quasar project with its own `src/lib/print/index.js`.
   - What's unclear: Whether there is a shared package mechanism or if files need to be duplicated.
   - Recommendation: Copy `zpl.js` and `templateResolver.js` to `webapps/warehouse/src/lib/print/`. Check for any absolute path imports that need adjustment. This is the simplest path given prior Phase 2 precedent (zpl.js was kept import-clean for exactly this reason).

3. **Warehouse app SSE feedback — simple spinner vs full SSE subscription**
   - What we know: Claude's discretion per CONTEXT.md. The warehouse app has `api` axios and could open an EventSource.
   - What's unclear: Whether the warehouse app has the SSE infrastructure (EventSource URL derivation from `api.defaults.baseURL`).
   - Recommendation: Implement a simple loading state (spinner) in warehouse app while the print job is in-flight, without SSE subscription. Rationale: warehouse operators need fast feedback; a fire-and-forget with optimistic success notification is simpler and the operator can re-try if the label doesn't come out.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest (node environment) |
| Config file | `webapps/main/vitest.config.js` |
| Quick run command | `cd webapps/main && yarn vitest run` |
| Full suite command | `cd webapps/main && yarn vitest run` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DIAL-05 | `sendToPrintService()` builds correct payload and POSTs to /print-job | unit | `cd webapps/main && yarn vitest run src/lib/print/index.test.js` | ❌ Wave 0 |
| DIAL-06 | ZPL path: generateZpl() called for type=zpl; PDF path: generate() + base64 for type=pdf | unit | `cd webapps/main && yarn vitest run src/lib/print/index.test.js` | ❌ Wave 0 |
| SSE-01/SSE-02 | waitForPrintResult() resolves on matching job_id, rejects on timeout | unit | `cd webapps/main && yarn vitest run src/lib/print/index.test.js` | ❌ Wave 0 |
| WH-02 | printProductLabel() calls generateZpl() + POST /print-job with correct data | unit | `cd webapps/warehouse && yarn vitest run src/lib/print/index.test.js` | ❌ Wave 0 |
| DIAL-02 | type/timeout_seconds pass through PrintJobRequest payload | manual | Inspect network tab | manual-only |
| WH-01 | Template keys stored in config after save | manual | Inspect /config GET response | manual-only |
| DOC-01 | Documentation completeness | manual | Read km/print-templates.md | manual-only |

### Sampling Rate
- **Per task commit:** `cd webapps/main && yarn vitest run`
- **Per wave merge:** `cd webapps/main && yarn vitest run`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `webapps/main/src/lib/print/index.test.js` — covers DIAL-05, DIAL-06, SSE-01/SSE-02
- [ ] `webapps/warehouse/src/lib/print/index.test.js` — covers WH-02
- [ ] Vitest config for warehouse app: check if `webapps/warehouse/vitest.config.js` exists; if not, may need to create it mirroring the main app config

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `webapps/main/src/components/PrintDialog.vue` — dialog structure, step 3, onDialogOK pattern
- Direct code inspection: `webapps/main/src/lib/print/index.js` — TemplateContext, generatePdf, existing hooks
- Direct code inspection: `webapps/main/src/components/AppBar.vue` — printer preference shape `"host:port"`, updatePreferences dispatch
- Direct code inspection: `webapps/main/src/stores/config.js` — printers array, productLabelTemplate/positionLabelTemplate fields, updateAppConfig
- Direct code inspection: `webapps/main/src/views/settings/warehouse/WarehouseSettings.vue` — commented-out template selectors, save function
- Direct code inspection: `backend/api/endpoints/print.py` — POST /print-job, print-result SSE payload structure
- Direct code inspection: `backend/api/models/print_job.py` — PrintJobRequest, PrintJobResult models
- Direct code inspection: `backend/api/endpoints/config.py` — schemaless PATCH /config
- Direct code inspection: `webapps/main/src/components/MessageThread.vue` — EventSource pattern
- Direct code inspection: `webapps/warehouse/src/lib/print/index.js` — current BrowserPrint-based implementation to replace
- Direct code inspection: `webapps/warehouse/src/stores/config.js` — productLabelTemplate/positionLabelTemplate already mapped from API

### Secondary (MEDIUM confidence)
- Direct code inspection: `webapps/main/src/i18n/en.js` — existing printDialog keys, preferences.printer keys for i18n naming convention
- Direct code inspection: `webapps/warehouse/src/i18n/en.js` — existing print/label keys for warehouse i18n naming

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries confirmed present via code inspection
- Architecture: HIGH — all integration points traced from source code
- Pitfalls: HIGH — all identified from direct code inspection of actual files
- Open questions: MEDIUM — BaseAutocompleteTemplate and warehouse Vitest config not verified

**Research date:** 2026-03-19
**Valid until:** 2026-04-19 (stable codebase, no external dependencies changing)
