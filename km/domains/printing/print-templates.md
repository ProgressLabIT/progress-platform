# Print Templates (pdfme v5)

Print templates define PDF layouts (text, images, barcodes) and how fields are linked to context data (presets or custom fields). The platform uses [pdfme](https://pdfme.com/) v5 with custom plugins for Progress-specific linking.

## Architecture

- **Designer**: [PrintTemplateDesigner.vue](webapps/main/src/components/PrintTemplateDesigner.vue) — toolbar with add-field buttons (no pdfme left sidebar), pdfme Designer for layout. Plugins built with `buildPlugins(customFields)` so the property panel can show Custom Field dropdowns. Link Type and Custom Field appear above graphical/formatting options in the prop panel. An unscoped CSS rule in the Designer raises Ant Design Select/Cascader dropdown z-index (`.ant-select-dropdown`, `.ant-cascader-dropdown` → 9999) so dropdowns are visible above the Quasar dialog (z-index ~6000).
- **Library card**: [PrintTemplateCard.vue](webapps/main/src/components/PrintTemplateCard.vue) — when `allowEdit` is set (e.g. [PrintTemplateLibrary.vue](webapps/main/src/views/PrintTemplateLibrary.vue)), a copy action loads the full template via `GET /print-template/{key}`, strips `_key` / `_id` / `_rev` (and UI-only fields), sets `name` to the original name plus a locale-specific “(COPY)” suffix, and creates a new document with `POST /print-template` (same payload shape as designer save). Template assignments (`can_use_print_template`) are not copied; the new template is global until linked elsewhere.
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
2. **Print dialog**: Template loaded → `getFieldNamesAndLinks()` collects all field names, link config (including `extraPath` combination), and `content` per field. Form model is filled from context for linked fields. Only non–read-only fields are rendered; required fields get an asterisk and are validated before preview.
3. **Generation**: `prepareInputs()` builds inputs for all fields (including read-only); `generate()` uses the same plugins (via `buildPlugins([])`).

### Field content fallback rule

When initialising field values (form model in PrintDialog, `resolveTemplateInputs` in warehouse):

- **`linkType === 'none'` or absent** → use `field.content` from the schema (the static value the designer embedded in the template). For PDF generation pdfme does this fallback internally; for ZPL it must be explicit.
- **`linkType` is set** (`preset`, `custom_field`, `template_expression`) but the resolved value is empty → **keep it empty**. The linked data source genuinely has no value and the designer's content must not mask that.

This rule applies to all field types (text, image, barcode). It ensures that a logo placed in the designer with no link prints correctly on ZPL, while a custom-field image that has no data does not accidentally show a stale placeholder.

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
| `datamatrix` | `^BXN` | DataMatrix ECC 200; freeform text content |
| `gs1datamatrix` | `^BXN` | DataMatrix ECC 200; strict GS1 AI format |
| `image` / `linkedImage` | `^GFA` | Graphic Field ASCII; image must be pre-processed into a `^GFA` hex string before calling `generateZpl` (see Image pre-processing below) |

Unknown field types are also skipped with `console.warn`.

### Image pre-processing

`generateZpl` is synchronous and expects image field values to already be `^GFA` command strings. The async conversion pipeline lives in `zplImage.js` (also copied verbatim to `webapps/warehouse/src/lib/print/zplImage.js`).

```js
import { processZplImageFields } from '@/lib/print/zplImage'

const zplInputs = await processZplImageFields(schemas, inputs, dpi)
const zpl = generateZpl(template, zplInputs, { dpi, quantity })
```

**`processZplImageFields(schemas, inputs, dpi)`** iterates over each image-type field and:

1. Uses the runtime input value if non-empty (linked image resolved from context).
2. Falls back to `field.content` from the schema **only when** `linkType` is `'none'` or absent (static image with no link). If the field has a link (`preset`, `custom_field`, `template_expression`) but the resolved value is empty, the empty value is kept — the linked data source genuinely has no value and it must not be masked by the designer's placeholder.
3. Converts the resolved data URL to a monochrome 1-bit bitmap via Canvas API (luminance threshold, transparent pixels become white).
4. Encodes the bitmap as `^GFA,{totalBytes},{totalBytes},{bytesPerRow},{hexData}`.

**`imageToZplGraphic(base64DataUrl, widthMm, heightMm, dpi)`** handles a single image. It resizes to the field's dot dimensions and returns the `^GFA` string, or `''` if the input is empty.

### Output envelope

Each label page is wrapped in a standard ZPL envelope:

```
^XA
^FO...^A0N...^FB...^FD...^FS
^FO...^BQN,...^FD...^FS
^FO...^GFA,...^FS
^PQ{quantity}
^XZ
```

---

## Print Service

The print service is a lightweight Python process that subscribes to NATS subjects for print job requests and sends ZPL or PDF data to printers over raw TCP. It uses NATS request/reply — the API sends a request, the print service processes the job and replies with the result, which the API returns synchronously to the browser.

### Architecture

```
Browser → POST /api/print-job → API → NATS request → Print Service → TCP → Printer
                                                            │
                                                      NATS reply ← result
                                                            │
                                  API ← NATS reply ← ──────┘
                                    │
Browser ← HTTP response ← ─────────┘
```

**Key constraints:**
- The browser never calls the print service directly. The print service only makes outbound connections — to NATS and to printers. No inbound ports are needed.
- Print jobs are synchronous from the browser's perspective — the HTTP response contains the result directly. There is no `PrintJob` database collection, no SSE, and no callback endpoints.

### Deployment

The print service is an optional on-prem add-on. The main API functions normally without it, but print jobs will fail with a `no_service` error when no print service is subscribed. It can be installed at initial setup or added later — provisioning is fully decoupled from the main Ansible playbook.

#### Installation

Prerequisites: the Progress Platform stack is running and the NATS broker is reachable on the `progress` Docker network.

Start the container:

```bash
cd /opt/progress/config && docker compose -f print.yaml up -d
```

No API credentials or setup scripts are needed — the print service connects directly to NATS, not to the API.

#### Compose file

`deploy/compose/print.yaml`:

```yaml
networks:
  progress:
    external: true

services:
  print-service:
    image: registry.gitlab.com/progresslab/progress-platform/print-service:${VERSION}
    restart: unless-stopped
    networks:
      - progress
    environment:
      PROGRESS_PRINT_SERVICE_NATS_URL: nats://broker:4222
    deploy:
      replicas: 1
      labels:
        - "traefik.enable=false"
```

The service has `traefik.enable=false` and exposes no inbound ports. It only needs outbound network access to NATS and to the local printer network.

### Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `PROGRESS_PRINT_SERVICE_NATS_URL` | Yes | `nats://broker:4222` | NATS server URL |
| `PROGRESS_PRINT_SERVICE_NON_ASCII` | No | `replace` | How to handle non-ASCII characters in ZPL: `replace` or `error` |
| `PROGRESS_PRINT_SERVICE_RECONNECT_DELAY` | No | `5.0` | Seconds between NATS reconnect attempts |
| `PROGRESS_PRINT_SERVICE_PRINTER_KEY` | No | *(all printers)* | Optional printer key filter — when set, the service subscribes only to `progress.print.jobs.{key}` instead of `progress.print.jobs.*` |

### API contract

**Submit a print job (browser → main API → NATS → print service):**

```
POST /api/print-job
Content-Type: application/json

{
  "printer_host": "192.168.1.100",
  "printer_port": 9100,
  "format": "zpl",
  "data": "^XA^FO50,50^FDHello^FS^XZ",
  "copies": 1,
  "timeout_seconds": 5,
  "printer_key": "zebra-warehouse"
}
```

| Field | Type | Default | Description |
|---|---|---|---|
| `printer_host` | string | — | IP address or hostname of the printer |
| `printer_port` | integer | `9100` | TCP port (Zebra printers default to 9100) |
| `format` | `"zpl"` \| `"pdf"` | — | Data format |
| `data` | string | — | ZPL text string, or base64-encoded PDF bytes |
| `copies` | integer | `1` | Number of copies to print |
| `timeout_seconds` | float | `5.0` | TCP connection/send timeout per copy |
| `printer_key` | string | — | Printer name, used as the NATS subject suffix (`progress.print.jobs.{printer_key}`) |

**Success response:** `{ "ok": true }`

**Error response:** `{ "ok": false, "error": "<code>", "detail": "<message>" }`

| Error code | Cause |
|---|---|
| `no_service` | No print service is subscribed to the NATS subject (service not running) |
| `timeout` | Print service did not respond within the NATS request timeout |
| `connection_refused` | Print service could not connect to the printer |
| `send_error` | TCP send to printer failed (encoding error, unknown format, etc.) |
| `internal` | Unexpected error in the API or print service |

**NATS timeout calculation:** The API sets the NATS request timeout to `(timeout_seconds × copies) + 5` seconds — enough to cover the TCP send time for each copy plus a buffer for network latency.

### Health check

The print service exposes a health endpoint at `:8200` using a minimal HTTP server. The endpoint returns `{ "status": "ok", "nats_connected": true }` when the NATS connection is active, or `"nats_connected": false` when disconnected.

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

- The print service waits `timeout_seconds` for the TCP connection and data send to complete per copy.
- The API sets the NATS request timeout to `(timeout_seconds × copies) + 5` seconds. If the print service doesn't reply within this window, the API returns a `timeout` error to the browser.
- The browser simply `await`s the HTTP response — there is no separate frontend timeout.

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
3. `sendToPrintService()` POSTs to `POST /api/print-job` and awaits the HTTP response (the API forwards to the print service via NATS request/reply and returns the result synchronously)
4. On response: spinner clears; toast appears. The dialog **closes only on success** so the user can fix data or retry after printer errors or timeouts.

### Toast outcomes

| Outcome | Toast type | Message |
|---|---|---|
| Success (`ok: true`) | Positive (green) | "Label sent to printer"; dialog closes |
| No service / internal error | Negative (red) | "Print service is not running"; dialog stays open |
| Connection refused | Negative (red) | Printer connection error detail; dialog stays open |
| Timeout | Negative (red) | "No response from printer"; dialog stays open |
| Other error | Negative (red) | Generic error message; dialog stays open |

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
