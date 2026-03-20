# Print Templates (pdfme v5)

Print templates define PDF layouts (text, images, barcodes) and how fields are linked to context data (presets or custom fields). The platform uses [pdfme](https://pdfme.com/) v5 with custom plugins for Progress-specific linking.

## Architecture

- **Designer**: [PrintTemplateDesigner.vue](webapps/main/src/components/PrintTemplateDesigner.vue) — toolbar with add-field buttons (no pdfme left sidebar), pdfme Designer for layout. Plugins built with `buildPlugins(customFields)` so the property panel can show Custom Field dropdowns. Link Type and Custom Field appear above graphical/formatting options in the prop panel. An unscoped CSS rule in the Designer raises Ant Design Select/Cascader dropdown z-index (`.ant-select-dropdown`, `.ant-cascader-dropdown` → 9999) so dropdowns are visible above the Quasar dialog (z-index ~6000).
- **Fill & generate**: [PrintDialog.vue](webapps/main/src/components/PrintDialog.vue) shows only editable fields, validates required fields, and uses `buildPlugins([])` for PDF generation. [print.js](webapps/main/src/lib/print.js) uses `buildPlugins([])` for programmatic `generatePdf()`.
- **Plugins**: [webapps/main/src/lib/print/plugins/](webapps/main/src/lib/print/plugins/) — `createLinkedText`, `createLinkedImage`, `createLinkedBarcodes` (factory functions taking `customFields`), and `createDataMatrixPlugin`. Link configuration is form-render format with `props.options` for selects and boolean `hidden` from `activeSchema`.

## Field properties (v5)

Each schema field in a template can carry:

| Property       | Type    | Meaning |
|----------------|---------|--------|
| `readOnly`     | boolean | If true, the field is not shown in the print dialog form (auto-filled from link, not editable). |
| `required`     | boolean | If true, the field is mandatory; label shows a red asterisk and preview is blocked until filled. |
| `linkType`     | string  | `'none'`, `'preset'`, `'custom_field'`, or `'template_expression'`. |
| `linkValue`    | string  | Preset key when `linkType === 'preset'` (e.g. `job.key`, `serial.extra`). |
| `extraPath`    | string  | When preset is an `.extra` preset (e.g. `serial.extra`), this is the nested path (e.g. `one.two`). Resolved as `linkValue + '.' + extraPath`. |
| `customFieldKey` | string | Custom field `_key` when `linkType === 'custom_field'`. |

Backend models: [backend/api/models/print.py](backend/api/models/print.py) — `TextFieldSpec` and `VisualFieldSpec` include `readOnly`, `required`, `extraPath`, and link fields so they pass through the API.

## Link configuration

- **Presets**: Fixed keys (e.g. `current_date`, `job.key`, `serial.code`, `serial.extra`) resolved by [print.js](webapps/main/src/lib/print.js) `TemplateContext.getPresetValue()` / `getExtraValue()`.
- **Custom fields**: Resolved by context-specific `getCustomFieldValue(customFieldKey)` (e.g. serial/product/step/issue data).
- **Extra path**: For presets whose key ends with `.extra`, the Designer shows an "Extra Attribute Path" field; at runtime the full path is `linkValue + '.' + extraPath` (e.g. `serial.extra.customAttr`).

## Data flow

1. **Designer**: User adds fields via toolbar, configures link type/value/extra path and editable/required in the pdfme property panel. Template is saved with schemas in v5 format (array of arrays, each field has `name`).
2. **Print dialog**: Template loaded → `getFieldNamesAndLinks()` collects all field names and link config (including `extraPath` combination). Form model is filled from context for linked fields. Only non–read-only fields are rendered; required fields get an asterisk and are validated before preview.
3. **Generation**: `prepareInputs()` builds inputs for all fields (including read-only); `generate()` uses the same plugins (via `buildPlugins([])`).

## Barcode types

| Plugin key       | bwip-js bcid       | Validation | Notes |
|------------------|--------------------|------------|-------|
| `datamatrix`     | `datamatrix`       | Any non-empty string | Custom plugin (`customDataMatrix.js`). Use for free-form text. |
| `gs1datamatrix`  | `gs1datamatrix`    | Strict GS1 AI format: must contain `(01)` + valid GTIN (8/12/13/14 digits with check digit), max 52 chars | pdfme built-in. Use only when encoding GS1-compliant data. |
| `qrcode`         | `qrcode`           | Up to 500 chars | pdfme built-in. |
| Other 1D codes   | Same as key (except `nw7` → `rationalizedCodabar`) | Type-specific (digits, check digits, character sets) | pdfme built-in. |

**Backward compatibility**: At generation time, `PrintDialog.vue` and `generatePdf()` automatically migrate `gs1datamatrix` fields to `datamatrix` when the runtime input value doesn't match GS1 AI format. This ensures existing templates created before the plain DataMatrix plugin was added continue to work.

---

## Template String Fields

Template string fields allow composite text values built from multiple data tokens, written in `{{variable}}` syntax directly in the pdfme designer.

### Syntax

In the Designer, an operator enters an expression like:

```
Product: {{product.code}} - {{product.description}}
```

Any token in `{{...}}` is replaced at print time with the corresponding live value. Tokens follow these conventions:

| Token form | Source | Example |
|---|---|---|
| `{{preset.key}}` | Preset value (job, serial, date, etc.) | `{{serial.code}}`, `{{current_date}}` |
| `{{cf::slug}}` | Custom field (display form, in Designer) | `{{cf::batch_number}}` |
| `{{cf::_key}}` | Custom field (storage form, in database) | `{{cf::1234567890}}` |
| `{{product.code}}` | Warehouse preset context | `{{product.code}}`, `{{position.code}}` |

### Storage format

The Designer works with human-readable slugs (`{{cf::batch_number}}`), but the database stores ArangoDB `_key` references (`{{cf::1234567890}}`). This round-trip is transparent to the user:

- **On designer load** (`decodeExpression`): stored `_key` tokens are replaced by readable slugs.
- **On save** (`encodeExpression`): display slugs are replaced by stable `_key` values.
- **Preset tokens** (`{{preset.key}}`) pass through both directions unchanged.

### Resolution at print time

`resolveExpression(expr, context, customFields)` in `webapps/main/src/lib/print/templateResolver.js` replaces all `{{tokens}}` with live data values:

```js
import { resolveExpression } from '@/lib/print/templateResolver'

const resolved = resolveExpression(
  '{{product.code}} / {{cf::_key123}}',
  {
    getPresetValue: (key) => presetLookup[key],
    getCustomFieldValue: (key) => customFieldLookup[key],
  },
  customFields
)
```

Missing values resolve to an empty string. The function is a pure ES module with no framework dependencies.

### Link type

To create a template string field in the Designer, select **Link Type → `template_expression`** in the field property panel. The input shows a textarea where the expression is authored.

---

## ZPL Transpiler

The ZPL transpiler converts a pdfme template and resolved field values into a ZPL II string ready to send to a Zebra label printer over TCP.

**Location:** `webapps/main/src/lib/print/zpl.js` (also copied verbatim to `webapps/warehouse/src/lib/print/zpl.js`)

### Function signature

```js
import { generateZpl } from '@/lib/print/zpl'

const zplString = generateZpl(template, inputs, { dpi, quantity })
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `template` | `object` | — | pdfme template object (`{ basePdf, schemas }`) |
| `inputs` | `object[]` | — | Array of per-page input objects, e.g. `[{ fieldName: resolvedValue }]` |
| `options.dpi` | `number` | `203` | Printer DPI (203 or 300) |
| `options.quantity` | `number` | `1` | Copies to print (sets `^PQ` per label) |

Returns a ZPL string. For multi-page templates, each page produces one `^XA...^XZ` block; blocks are joined with newlines.

### Coordinate conversion

pdfme uses millimetres; ZPL uses dots. The conversion formula:

```
dots = mm * (dpi / 25.4)
```

One inch is 25.4 mm. Font sizes are converted from typographic points using:

```
dots = pt * (dpi / 72)
```

Default DPI is 203 (standard Zebra label printer). Use 300 for high-resolution printers.

### Supported field types

| Field type | ZPL command | Notes |
|---|---|---|
| `text` | `^A0N` + `^FB` | Scalable font, field block for width/alignment |
| `template_string` | `^A0N` + `^FB` | Same as `text`; expression already resolved before `generateZpl` is called |
| `qrcode` | `^BQN` | QR Code model 2; magnification derived from field height |
| `code128` | `^BCN` | Code 128 with HRI below |
| `code39` | `^B3N` | Code 39, no check digit |
| `ean13` | `^BEN` | EAN-13; pass 12 digits — printer computes the 13th check digit |
| `gs1datamatrix` | `^BXN` | DataMatrix ECC 200 |
| `image` / `linkedImage` | (skipped) | Silently skipped with `console.warn`; deferred to v3 |

Unknown field types are also skipped with `console.warn`.

### Output envelope

Each label page is wrapped in a standard ZPL envelope:

```
^XA
^FO...^A0N...^FB...^FD...^FS
^FO...^BQN,...^FD...^FS
^PQ{quantity}
^XZ
```

---

## Print Service

The print service is a lightweight Python process that subscribes to the main API's SSE stream, receives print jobs, and sends ZPL or PDF data to printers over raw TCP.

### Architecture

```
Browser
  ├─► EventSource GET /api/print-result/stream  (opened first, one-shot)
  └─► POST /api/print-job  ──►  Main API
                                  │
                                  ├─► SSE stream (GET /api/print-jobs/stream)
                                  │         ▲
                                  │    Print Service subscribes (outbound)
                                  │         │
                                  │         └─► TCP ──► Printer
                                  │                        │
                                  │    POST /api/print-jobs/{id}/result ◄─┘
                                  │         │
                                  │         └─► enqueue → print-result SSE ──► Browser toast
```

**Key constraints:**
- The browser never calls the print service directly. The print service only makes outbound connections — to the main API and to printers. No inbound ports are needed.
- Print jobs are fire-and-forget — there is no `PrintJob` database collection. The result callback (`POST /print-jobs/{id}/result`) enqueues an SSE event for the browser and returns immediately.

### Deployment

Deploy the print service using `deploy/compose/print.yaml`. It is an optional on-prem service; the main API functions normally without it (the print job will stay pending in the database until a service picks it up).

**compose file:** `deploy/compose/print.yaml`

```yaml
services:
  print-service:
    image: registry.gitlab.com/progresslab/progress-platform/print-service:${VERSION}
    restart: unless-stopped
    environment:
      PRINT_SERVICE_API_URL: ${PRINT_SERVICE_API_URL}
      PRINT_SERVICE_NON_ASCII: replace
    secrets:
      - source: print_service_pwd
        target: api_password
    deploy:
      labels:
        - "traefik.enable=false"
```

The service has `traefik.enable=false` and exposes no inbound ports. It only needs outbound network access to the main API and to the local printer network.

### Environment variables

| Variable | Required | Description |
|---|---|---|
| `PRINT_SERVICE_API_URL` | Yes | Main API base URL including `/api` path, e.g. `https://progress.example.com/api` |
| `PRINT_SERVICE_API_PASSWORD` | Yes | Password for the `print_service` service account (stored in Docker secret `print_service_pwd`, mounted at `/run/secrets/api_password`) |
| `PRINT_SERVICE_NON_ASCII` | No | How to handle non-ASCII characters in ZPL: `replace` (default) or `error` |
| `PRINT_SERVICE_RECONNECT_DELAY` | No | Seconds between SSE reconnect attempts (default `5.0`) |

The service authenticates to the main API using the `print_service` user account. The account must exist and have print permissions. No JWT management is needed — the service logs in on startup with username/password.

### API contract

**Submit a print job (browser → main API):**

```
POST /api/print-job
Content-Type: application/json

{
  "printer_host": "192.168.1.100",
  "printer_port": 9100,
  "format": "zpl",
  "data": "^XA^FO50,50^FDHello^FS^XZ",
  "copies": 1,
  "timeout_seconds": 5
}
```

Response: `{ "job_id": "abc123" }`

| Field | Type | Default | Description |
|---|---|---|---|
| `printer_host` | string | — | IP address or hostname of the printer |
| `printer_port` | integer | `9100` | TCP port (Zebra printers default to 9100) |
| `format` | `"zpl"` \| `"pdf"` | — | Data format |
| `data` | string | — | ZPL text string, or base64-encoded PDF bytes |
| `copies` | integer | `1` | Number of copies to print |
| `timeout_seconds` | float | `5.0` | TCP connection/send timeout in seconds |

**SSE stream (print service → main API):**

```
GET /api/print-jobs/stream
```

The print service subscribes to this endpoint after login and receives new print jobs as SSE events. Authentication uses session cookies from the login step.

**Result callback (print service → main API):**

```
POST /api/print-jobs/{job_id}/result
Content-Type: application/json

{ "ok": true, "error": null, "detail": null }
```

On failure: `{ "ok": false, "error": "connection_refused", "detail": "Connection refused by 192.168.1.100:9100" }`

Error codes: `connection_refused`, `timeout`, `send_error`.

**SSE notification (main API → browser):**

After the result callback is received, the main API enqueues an SSE event on the `print-result` topic via `ServerEventManager.enqueue()`:

- Endpoint: `GET /api/print-result/stream` (dedicated one-shot SSE stream; the generator uses `max_events=1` and self-terminates after delivering one event)
- Event type: `print-result`
- Payload: `{ "job_id": "abc123", "ok": true, "error": null, "detail": null }`

The browser opens an `EventSource` to this endpoint before submitting the print job, then filters by `job_id` to match the event to the originating request. The server-side generator exits after one event; the HTTP connection closes within a few seconds via `sse_starlette` cleanup.

### Health check

The print service exposes a health endpoint at `:8200` using a raw TCP server (not HTTP). The endpoint returns `ok` when the SSE subscription is active, or an error state when disconnected.

---

## Printer Type Field

Each printer record now carries two additional fields that control how print jobs are routed.

### Fields

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `type` | `"zpl"` \| `"pdf"` | Yes | — | Determines the print path (ZPL transpiler or PDF generator) |
| `timeout_seconds` | integer | No | `5` | How long the print service waits for a TCP response from the printer |

### Configuration

Printers are configured in **Settings > Printers**. When adding a new printer, the admin must select a type (no default) and may set a timeout.

The `type` field determines which code path is used at print time:

- **`zpl`**: `generateZpl(template, resolvedInputs, { dpi, quantity })` produces a ZPL string, sent as-is over TCP.
- **`pdf`**: `@pdfme/generator`'s `generate()` produces PDF bytes, base64-encoded, sent as a PDF payload.

### Timeout behavior

- The print service waits `timeout_seconds` for the TCP connection and data send to complete.
- The frontend waits `timeout_seconds + 5` seconds for the SSE result event before showing a timeout toast. The extra 5 seconds accounts for network round-trip latency between printer, print service, main API, and browser.

---

## Print Dialog: Send to Printer

The print dialog (step 3) provides a "Send to [printer name]" button alongside the existing "Download PDF" button.

### Visibility

The button is visible when the user has a printer configured in their account preferences (**Settings > Printers > select a default printer**). If no printer is configured, only the "Download PDF" button is shown. There is no printer selector dropdown in the dialog — the configured printer is used silently.

### Button label

The button shows the name of the configured printer: `"Send to [printer name]"`.

### Flow

1. User clicks "Send to [printer name]"
2. Both buttons are hidden; a centered spinner appears (printing in progress)
3. `sendToPrintService()` POSTs to `POST /api/print-job`
4. `waitForPrintResult()` opens an SSE stream to `GET /print-result/stream` (dedicated one-shot endpoint, closes after one event), filtered by `job_id`
5. On result or timeout: spinner clears; toast appears. The dialog **closes only on success** so the user can fix data or retry after printer errors or timeouts.
6. Toast notification appears (see table below)

### Toast outcomes

| Outcome | Toast type | Message |
|---|---|---|
| Success | Positive (green) | "Label sent to printer"; dialog closes |
| Error | Negative (red) | Error detail from print service; dialog stays open |
| Timeout | Negative (red) | "No response from printer"; dialog stays open |
| POST failure | Negative (red) | Dialog stays open, `isPrinting` reset; user can retry |

### Download PDF

The "Download PDF" button (existing behavior) is always preserved alongside the send-to-printer action. Both options are available independently.

---

## Warehouse Template Assignment

Warehouse label printing uses the new print service pipeline. Admins configure which pdfme template is used for each label type; operators' click-to-print behavior is unchanged.

### Configuration (main app)

Template assignment is in **Settings > Warehouse Settings**, in a dedicated label templates section (visible regardless of the Inventory Management toggle):

| Setting | Config key | Description |
|---|---|---|
| Product label template | `product_label_template` | pdfme template used for product labels |
| Position label template | `position_label_template` | pdfme template used for position/container labels |

These are saved to the warehouse config document via `PATCH /config`. The warehouse app reads them at print time.

### Preset contexts

Warehouse templates use the standard template link system. Two preset contexts are available for warehouse labels:

**Product label context:**

| Preset key | Value |
|---|---|
| `product.code` | Product code (e.g. `WIDGET-A`) |
| `product.description` | Product name/description |

**Position label context:**

| Preset key | Value |
|---|---|
| `position.code` | Position/container code (e.g. `A-01-03`) |

Templates can also use `template_expression` fields to compose values from these presets.


### Print flow (warehouse app)

The warehouse app's `printProductLabel()` and `printPositionLabel()` functions in `webapps/warehouse/src/lib/print/index.js` implement the new pipeline:

1. Fetch the configured template for the label type from Pinia config store
2. Build a context object from available Vuex session data
3. Resolve template fields using `resolveExpression()` from `templateResolver.js`
4. Call `generateZpl(template, resolvedInputs, { dpi, quantity })` to produce ZPL
5. POST to `POST /api/print-job` with the ZPL string

The function signatures are identical to the previous implementation -- all callers (`IncomingQuantitySelectionPage.vue`, `CreateContainerForm.vue`, etc.) are unchanged.

### BrowserPrint removal

The previous warehouse print implementation used BrowserPrint (Zebra's browser extension) and hardcoded ZPL strings sent to `/pstprnt`. Both have been removed from `webapps/warehouse/src/lib/print/`:

- `postZPL()` removed
- `sendZplToPrinter()` removed
- `sendPdfToPrinter()` removed
- `getPrinter()` removed
- BrowserPrint import removed

The `@pdfme/generator`, `zpl.js`, and `templateResolver.js` are the replacements.
