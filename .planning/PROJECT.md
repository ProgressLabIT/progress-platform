# Progress Platform — Printing v2

## What This Is

A brownfield milestone that completes the platform's printing subsystem. The main webapp has flexible, template-driven direct-to-printer output (PDF and ZPL) via a lightweight on-prem relay service. The warehouse app's hardcoded Zebra label printing has been replaced with the same unified system, removing the proprietary `/pstprint` dependency and enabling any ZPL-compatible printer.

## Core Value

Factory operators can print labels directly to any ZPL printer by pressing one button — no manual file downloads, no proprietary endpoints, no per-site workarounds.

## Requirements

### Validated

- ✓ pdfme v5 template designer in main app — existing
- ✓ PDF generation and download from print dialog — existing
- ✓ Field linking from production context in print dialog — existing
- ✓ Warehouse app product/position label printing (via hardcoded Zebra `/pstprint`) — existing (replaced)
- ✓ Template string (`{{variable}}`) field type in pdfme designer for composite text labels — v1.0
- ✓ ZPL transpiler: pdfme template schemas + resolved inputs → valid ZPL strings (text, barcodes, QR; images deferred) — v1.0
- ✓ On-prem print service: SSE-subscriber Python process that forwards ZPL or PDF bytes to LAN printer — v1.0
- ✓ Print dialog step 3: "Download PDF" (existing) + "Send to [printer name]" button — v1.0
- ✓ Printer model gets `type` (zpl/pdf) and `timeout_seconds` fields in settings UI — v1.0
- ✓ Main app settings: configure product label template and position label template for warehouse app — v1.0
- ✓ Warehouse app print flow uses new print service + configured templates instead of hardcoded ZPL + `/pstprint` — v1.0
- ✓ Docker Compose service definition for print service (`deploy/compose/print.yaml`) — v1.0

### Active

*(Next milestone requirements go here)*

### Out of Scope

- ZPL image fields (`^GFA` bitmap conversion) — complex, not blocking for v2; deferred to v3
- Warehouse app UX changes — click-to-print behavior stays identical; only the backend pathway changes
- Auth on the print service — stateless LAN relay, no DB access; auth would add complexity without value
- Cloud/remote printing — on-prem LAN only; no tunneling or SaaS relay

## Context

**Current state (after v1.0):**
- Main webapp: pdfme v5 designer + PDF download + direct ZPL/PDF printing via on-prem relay service
- Warehouse app: configurable pdfme templates + print service; hardcoded ZPL and Zebra `/pstprint` removed
- Print service: standalone Docker Compose service, SSE-subscriber, raw TCP relay, health on :8200
- 38 vitest tests (templateResolver + zpl) + 8 pytest unit tests (tcp_sender)
- Known tech debt: `linkedTemplateString.js` orphaned from `buildPlugins()`, port default 80→9100 (fixed), warehouse config store latent gap, `verify_print_service_token` auth context semantics

**Architecture:**
- One design surface (pdfme designer), two output paths: `generate() → PDF` and `generateZpl() → ZPL string`
- Print service is a LAN-only SSE-subscriber: subscribes to main API `/print-jobs/stream`, sends bytes via TCP, POSTs result back
- Browser never calls print service directly; `traefik.enable=false`
- Printer config (host, port, type, timeout) stored in app settings; user sets printer preference

**Tech stack (relevant):**
- Frontend: Vue3 + Quasar, pdfme v5 for template designer
- Backend: FastAPI (Python), ArangoDB
- Warehouse app: Quasar + Capacitor (mobile/tablet)
- Print service: Python asyncio + httpx-sse, raw TCP sockets, Docker

## Constraints

- **Portability**: Print service must work with any ZPL-compatible printer (not just Zebra), so no vendor-specific protocols
- **No backend model changes**: pdfme template schema is the single source of truth for both PDF and ZPL
- **Warehouse UX unchanged**: Operators' click-to-print workflow must not change — only the implementation behind it changes
- **LAN-only relay**: Print service is a server-side SSE subscriber — browser never calls it directly

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| One pdfme template → two output paths (PDF + ZPL) | Avoids maintaining a separate ZPL editor or template type | ✓ Validated — v1.0 |
| Stateless TCP relay (SSE subscriber, not a spooler) | Keeps service ~100 lines, no DB, no auth, easy to deploy on-prem | ✓ Validated — v1.0 |
| `traefik.enable=false` for print service | Print service is an outbound SSE client; no inbound ports needed | ✓ Validated — v1.0 |
| ZPL images deferred | `^GFA` bitmap conversion is complex; text + barcodes cover 90% of label use cases | — Pending (deferred to v3) |
| Warehouse template config in main app (not warehouse app) | Admins configure templates, not operators; main app is the admin surface | ✓ Validated — v1.0 |
| "Send to Printer" uses user preference (no dialog dropdown) | Simpler UX — one button per user's configured printer | ✓ Validated — v1.0 |
| `template_expression` as linkType on text fields (not a separate plugin) | Avoids unregistered pdfme widget errors; integrates with existing propPanel system | ⚠ Revisit — `linkedTemplateString.js` left orphaned; plugin registration in buildPlugins() deferred |
| Subscribe-before-submit SSE pattern | Eliminates race condition where print result arrives before listener is attached | ✓ Validated — v1.0 |
| Chunked btoa (8192-byte slices) for PDF encoding | Avoids V8 stack overflow on 50-500KB PDFs spread as function arguments | ✓ Validated — v1.0 |

---
*Last updated: 2026-03-21 after v1.0 milestone*
