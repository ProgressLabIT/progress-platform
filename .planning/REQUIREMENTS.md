# Requirements: Progress Platform — Printing v2

**Defined:** 2026-03-12
**Core Value:** Factory operators can print labels directly to any ZPL printer by pressing one button — no manual downloads, no proprietary endpoints.

## v1 Requirements

### Template String Plugin

- [x] **TMPL-01**: Designer can add a "template string" field that supports `{{variable}}` syntax for composite text (e.g. `Product: {{product.code}} - Qty: {{serial.qt}} pcs`)
- [x] **TMPL-02**: `templateResolver.js` provides `decodeExpression` (keys → labels for Designer display), `encodeExpression` (labels → keys for save), and `resolveExpression` (replaces `{{...}}` with live values)
- [x] **TMPL-03**: `linkedTemplateString.js` pdfme plugin wraps base `text` schema and exposes `templateExpression` textarea + variable reference in the property panel
- [ ] **TMPL-04**: PrintTemplateDesigner decodes expressions on load and encodes on save; toolbar has a button to add a template string field
- [ ] **TMPL-05**: PrintDialog resolves `template_expression` link type via `resolveExpression` during field linking

### ZPL Generator

- [ ] **ZPL-01**: `generateZpl(template, inputs, { dpi, quantity })` transpiles a pdfme template + resolved inputs into a valid ZPL string
- [ ] **ZPL-02**: Coordinate mapping: pdfme mm → ZPL dots at configurable DPI (default 203)
- [ ] **ZPL-03**: Supported field types: `text` (`^FO^A0N^FB^FD^FS`), `qrcode` (`^BQN`), `code128` (`^BCN`), `code39` (`^B3N`), `ean13` (`^BEN`), `gs1datamatrix` (`^BXN`)
- [ ] **ZPL-04**: Image fields log a console warning and are skipped (deferred to v3)
- [ ] **ZPL-05**: Output wraps fields with `^XA ... ^PQ{quantity} ^XZ`

### Print Service

- [ ] **SVC-01**: `backend/print-service/main.py` FastAPI app with `GET /health` and `POST /print` endpoints
- [ ] **SVC-02**: `POST /print` accepts `printer_host`, `printer_port` (default 9100), `format` (`zpl`|`pdf`), `data` (ZPL text or base64 PDF), `copies`; opens raw TCP socket, sends data, closes
- [ ] **SVC-03**: CORS origins configurable via `PRINT_SERVICE_CORS_ORIGINS` env var
- [ ] **SVC-04**: Dockerfile (`python:3.11-slim`, port 8200, uvicorn)
- [ ] **SVC-05**: `deploy/compose/print.yaml` following existing compose patterns; `traefik.enable=false` (browser calls LAN IP directly)

### Print Dialog Integration

- [ ] **DIAL-01**: `printServerURL` option added to `deploy/config/appConfig.js` (optional; enables direct printing when set)
- [ ] **DIAL-02**: Printer model has a `type` field (`zpl`|`pdf`); PrinterNew.vue and PrintersTable.vue updated accordingly
- [ ] **DIAL-03**: Print dialog step 3 adds "Send to Printer" action (only visible when `printServerURL` is configured): printer selector dropdown, quantity input, confirm button
- [ ] **DIAL-04**: "Download PDF" button (existing behavior) preserved alongside the new action
- [ ] **DIAL-05**: `sendToPrintService({ data, printer, format, copies })` implemented in `lib/print/index.js`
- [ ] **DIAL-06**: PrintDialog OK handler: `type === 'zpl'` → `generateZpl()` → send ZPL; `type === 'pdf'` → `generate()` → base64 → send PDF

### Warehouse App Integration

- [ ] **WH-01**: Main app settings section to configure which pdfme template is used per warehouse label type (product label, position label)
- [ ] **WH-02**: Warehouse app product/position label printing uses the configured pdfme templates + new print service instead of hardcoded ZPL + `/pstprint`
- [ ] **WH-03**: Warehouse app operator UX is unchanged — click-to-print behavior identical to current

### Documentation

- [ ] **DOC-01**: `km/print-templates.md` updated: template string field (syntax, storage format, resolution), ZPL transpiler (field mapping, coordinate conversion, supported types, image deferral), print service (deployment, endpoint contract, CORS), printer `type` field, `printServerURL` config

## v2 Requirements

### ZPL Images
- **ZIMG-01**: Image fields in ZPL output via `^GFA` bitmap conversion

## Out of Scope

| Feature | Reason |
|---------|---------|
| ZPL image fields in v2 | `^GFA` bitmap conversion is complex; text + barcodes cover 90% of label use cases |
| Auth on print service | Stateless LAN relay; no DB access; auth adds complexity without value for on-prem |
| Cloud/remote printing | On-prem LAN only; no tunneling or SaaS relay planned |
| Warehouse app UX changes | Operators' click-to-print workflow must not change |
| Separate ZPL template type | One pdfme template serves both PDF and ZPL output |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| TMPL-01 | Phase 1 | Complete |
| TMPL-02 | Phase 1 | Complete |
| TMPL-03 | Phase 1 | Complete |
| TMPL-04 | Phase 1 | Pending |
| TMPL-05 | Phase 1 | Pending |
| ZPL-01 | Phase 2 | Pending |
| ZPL-02 | Phase 2 | Pending |
| ZPL-03 | Phase 2 | Pending |
| ZPL-04 | Phase 2 | Pending |
| ZPL-05 | Phase 2 | Pending |
| SVC-01 | Phase 3 | Pending |
| SVC-02 | Phase 3 | Pending |
| SVC-03 | Phase 3 | Pending |
| SVC-04 | Phase 3 | Pending |
| SVC-05 | Phase 3 | Pending |
| DIAL-01 | Phase 4 | Pending |
| DIAL-02 | Phase 4 | Pending |
| DIAL-03 | Phase 4 | Pending |
| DIAL-04 | Phase 4 | Pending |
| DIAL-05 | Phase 4 | Pending |
| DIAL-06 | Phase 4 | Pending |
| WH-01 | Phase 4 | Pending |
| WH-02 | Phase 4 | Pending |
| WH-03 | Phase 4 | Pending |
| DOC-01 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 25 total
- Mapped to phases: 25
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-12*
*Last updated: 2026-03-12 after initial definition*
