# Milestones

## v1.0 Printing v2 (Shipped: 2026-03-20)

**Phases completed:** 4 phases, 14 plans
**Timeline:** 2026-03-12 → 2026-03-20 (9 days)
**Files changed:** 117 files, 15,634 insertions

**Key accomplishments:**

- Template string `{{variable}}` composite text fields in pdfme designer with full encode/decode/resolve pipeline
- Pure-JS `generateZpl()` transpiler covering text, all 5 barcode types (QR/128/39/EAN-13/GS1), and image skipping at configurable DPI
- On-prem SSE-subscriber print service + raw TCP relay with Docker Compose deployment and health endpoint
- PrintDialog "Send to Printer" action with ZPL/PDF routing and real-time SSE feedback (no false positives)
- Warehouse app migrated from hardcoded Zebra `/pstprint` to unified print service + configurable pdfme templates
- Full documentation in `km/domains/printing/print-templates.md` covering all new capabilities

**Archive:** `.planning/milestones/v1.0-ROADMAP.md`

---
