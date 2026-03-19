# Roadmap: Progress Platform — Printing v2

## Overview

Four independently shippable phases complete the printing subsystem. Phase 1 builds the template string plugin that enables composite text fields in the pdfme designer. Phase 2 implements the pure-JS ZPL transpiler that converts pdfme templates into printer-ready ZPL strings. Phase 3 ships the on-prem FastAPI TCP relay service and its Docker deployment. Phase 4 wires everything together in the print dialog, warehouse app, and documentation — delivering the one-button direct-to-printer experience.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Template String Plugin** - pdfme plugin + designer + dialog support for `{{variable}}` composite text fields (completed 2026-03-12)
- [x] **Phase 2: ZPL Generator** - Pure-JS transpiler converting pdfme template schemas + resolved inputs into valid ZPL strings (completed 2026-03-18)
- [x] **Phase 3: Print Service** - SSE-subscriber print service + main API print endpoints + Docker Compose deployment (completed 2026-03-18)
- [ ] **Phase 4: Full Integration** - Print dialog "Send to Printer" action, printer type field, warehouse app migration, and documentation

## Phase Details

### Phase 1: Template String Plugin
**Goal**: Designers can create composite text fields using `{{variable}}` syntax in the pdfme template designer, and the print dialog resolves those expressions against live production data
**Depends on**: Nothing (first phase)
**Requirements**: TMPL-01, TMPL-02, TMPL-03, TMPL-04, TMPL-05
**Success Criteria** (what must be TRUE):
  1. A user can add a "template string" field to a pdfme template via a toolbar button in the designer
  2. The designer property panel shows a `templateExpression` textarea with variable reference, and field labels are human-readable (decoded) while editing
  3. Saving the template persists encoded expressions; reloading restores them correctly in the designer
  4. In the print dialog, `template_expression` link types are resolved with live values (e.g., `Product: ABC - Qty: 10 pcs`) before PDF generation
**Plans**: 5 plans

Plans:
- [x] 01-01-PLAN.md — Install vitest and create failing test scaffold (RED state)
- [x] 01-02-PLAN.md — Implement templateResolver.js (slugify, encode, decode, resolve) via TDD
- [x] 01-03-PLAN.md — Implement linkedTemplateString.js plugin and register in buildPlugins()
- [x] 01-04-PLAN.md — Wire plugin into PrintTemplateDesigner: toolbar button + decode-on-load + encode-on-save
- [x] 01-05-PLAN.md — Wire resolveExpression into PrintDialog + backend slug uniqueness validation

### Phase 2: ZPL Generator
**Goal**: A `generateZpl()` function converts any pdfme template and resolved inputs into a valid, printer-ready ZPL string supporting text, barcodes, and QR codes
**Depends on**: Phase 1
**Requirements**: ZPL-01, ZPL-02, ZPL-03, ZPL-04, ZPL-05
**Success Criteria** (what must be TRUE):
  1. `generateZpl(template, inputs, { dpi, quantity })` returns a complete ZPL string with `^XA ... ^PQ{quantity} ^XZ` envelope
  2. Text fields, QR codes, code128, code39, EAN-13, and GS1 DataMatrix fields all produce correct ZPL commands at the right coordinates
  3. pdfme mm coordinates map accurately to ZPL dots at configurable DPI (default 203)
  4. Image fields are silently skipped with a console warning and do not break generation
**Plans**: 1 plan

Plans:
- [x] 02-01-PLAN.md — TDD: Export prereqs, implement generateZpl with all field types (text, barcodes, image skip, envelope)

### Phase 3: Print Service
**Goal**: Browser submits print jobs to the main API, which relays them via SSE to an on-prem print service that forwards raw bytes over TCP to LAN printers and reports results back
**Depends on**: Phase 2
**Requirements**: SVC-01, SVC-02, SVC-03, SVC-04, SVC-05
**Success Criteria** (what must be TRUE):
  1. `POST /api/print-job` accepts a valid payload, generates a uuid4 job_id in memory (no DB collection), and enqueues an SSE event on the "print-jobs" subtopic; `GET /api/print-jobs/stream` delivers jobs to the print service subscriber
  2. The print service subscribes to the SSE stream, sends data over TCP to `printer_host:printer_port`, and POSTs the result back to `/api/print-jobs/{id}/result` which enqueues a "print-result" SSE event
  3. The service runs in Docker via `deploy/compose/print.yaml` with `traefik.enable=false` and no inbound port requirements
  4. Both ZPL (ASCII-encoded) and PDF (base64-decoded) formats are accepted; TCP errors are classified as `connection_refused`, `timeout`, or `send_error`
**Plans**: 2 plans

Plans:
- [x] 03-01-PLAN.md — Add PrintJob models and print job endpoints (POST /print-job, SSE stream, result callback) to main API
- [x] 03-02-PLAN.md — Create standalone print service (SSE subscriber + TCP sender), Dockerfile, and Docker Compose deployment

### Phase 4: Full Integration
**Goal**: Factory operators can print labels directly to any configured printer from the main app print dialog and the warehouse app, with real-time success/error feedback via SSE, replacing all hardcoded ZPL and `/pstprint` dependencies
**Depends on**: Phase 3
**Requirements**: DIAL-01, DIAL-02, DIAL-03, DIAL-04, DIAL-05, DIAL-06, SSE-01, SSE-02, WH-01, WH-02, WH-03, DOC-01
  - `SSE-01`: Frontend subscribes to `/notification/print-result` SSE stream after submitting a print job
  - `SSE-02`: Frontend filters "print-result" events by `job_id` to display success or error feedback for the originating request
**Success Criteria** (what must be TRUE):
  1. When user has a printer configured in preferences, the print dialog step 3 shows a "Send to [printer name]" action alongside the existing "Download PDF" button
  2. Selecting a ZPL printer triggers `generateZpl()` → send ZPL; selecting a PDF printer triggers `generate()` → base64 → send PDF
  3. After submitting a print job, the frontend subscribes to the `/notification/print-result` SSE stream, filters events by the returned `job_id`, and displays a success toast or error message to the user
  4. Admins can configure which pdfme template is used per warehouse label type (product label, position label) in main app settings
  5. Warehouse app operators click print and labels come out — workflow is identical to before, but no longer depends on Zebra-specific `/pstprint` or hardcoded ZPL
  6. `km/print-templates.md` covers all new capabilities: template string syntax, ZPL transpiler, print service deployment, printer type field, and warehouse template assignment
**Plans**: 4 plans

Plans:
- [ ] 04-01-PLAN.md — Printer type/timeout fields + sendToPrintService/waitForPrintResult lib functions
- [ ] 04-02-PLAN.md — PrintDialog "Send to Printer" button with ZPL/PDF routing and SSE feedback
- [ ] 04-03-PLAN.md — Warehouse settings template selectors + warehouse print function replacement
- [ ] 04-04-PLAN.md — Documentation: km/print-templates.md update

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Template String Plugin | 5/5 | Complete   | 2026-03-13 |
| 2. ZPL Generator | 1/1 | Complete   | 2026-03-18 |
| 3. Print Service | 2/2 | Complete   | 2026-03-18 |
| 4. Full Integration | 0/4 | Planning complete | - |
