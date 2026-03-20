# Progress Platform — Printing v2

## What This Is

A brownfield milestone that completes the platform's printing subsystem. The main webapp gets flexible, template-driven direct-to-printer output (PDF and ZPL) via a lightweight on-prem relay service. The warehouse app's hardcoded Zebra label printing is replaced with the same unified system, removing the proprietary `/pstprint` dependency and enabling any ZPL-compatible printer.

## Core Value

Factory operators can print labels directly to any ZPL printer by pressing one button — no manual file downloads, no proprietary endpoints, no per-site workarounds.

## Requirements

### Validated

- ✓ pdfme v5 template designer in main app — existing
- ✓ PDF generation and download from print dialog — existing
- ✓ Field linking from production context in print dialog — existing
- ✓ Warehouse app product/position label printing (via hardcoded Zebra `/pstprint`) — existing (to be replaced)

### Active

- [x] Template string (`{{variable}}`) field type in pdfme designer for composite text labels — Validated in Phase 1: Template String Plugin
- [x] ZPL transpiler that converts pdfme template schemas + resolved inputs into valid ZPL strings (text, barcodes, QR — images deferred) — Validated in Phase 2: ZPL Generator
- [x] On-prem print service: SSE-subscriber Python process that forwards ZPL or PDF bytes to a printer on the LAN — Validated in Phase 3: Print Service
- [x] Print dialog step 3: "Download PDF" (existing) + "Send to [printer name]" button — visible when user has printer preference set — Validated in Phase 4: Full Integration
- [x] Printer model gets `type` (zpl/pdf) and `timeout_seconds` fields in settings UI — Validated in Phase 4: Full Integration
- [x] Main app settings: configure product label template and position label template for the warehouse app — Validated in Phase 4: Full Integration
- [x] Warehouse app print flow uses the new print service + configured templates instead of hardcoded ZPL + `/pstprint` — Validated in Phase 4: Full Integration
- [x] Docker Compose service definition for the print service (`deploy/compose/print.yaml`) — Validated in Phase 3: Print Service
- [x] `printServerURL` approach superseded — button visibility driven by user printer preference; no appConfig.js change needed — Validated in Phase 4: Full Integration

### Out of Scope

- ZPL image fields (`^GFA` bitmap conversion) — complex, not blocking for v2; deferred to v3
- Warehouse app UX changes — click-to-print behavior stays identical; only the backend pathway changes
- Auth on the print service — stateless LAN relay, no DB access; auth would add complexity without value
- Cloud/remote printing — on-prem LAN only; no tunneling or SaaS relay

## Context

**Existing printing (before this milestone):**
- Main webapp: pdfme v5 designer + PDF download only; no direct printing
- Warehouse app: hardcoded ZPL string templates for product/position labels sent via Zebra's `/pstprint` endpoint — only works with specific Zebra models

**Why this needs to change:**
- Customer site needs ZPL direct printing on non-Zebra-specific hardware
- Two separate printing systems (main PDF vs warehouse hardcoded ZPL) create fragmentation
- Hardcoded ZPL templates can't be customized without code changes

**Architecture:**
- One design surface (pdfme designer), two output paths: `generate() → PDF` and `generateZpl() → ZPL string`
- Print service is a LAN-only TCP relay — browser calls it directly on the local network, not through the main API or Traefik
- Warehouse app's `printServerURL` config determines the relay endpoint; printer config (host, port, type) stored in app settings

**Tech stack (relevant):**
- Frontend: Vue3 + Quasar, pdfme v5 for template designer
- Backend: FastAPI (Python), ArangoDB
- Warehouse app: Quasar + Capacitor (mobile/tablet)
- Print service: FastAPI + uvicorn, raw TCP sockets, Docker

## Constraints

- **Portability**: Print service must work with any ZPL-compatible printer (not just Zebra), so no vendor-specific protocols
- **No backend model changes**: pdfme template schema is the single source of truth for both PDF and ZPL — no new DB collections needed for this milestone
- **Warehouse UX unchanged**: Operators' click-to-print workflow must not change — only the implementation behind it changes
- **LAN-only relay**: Print service is a server-side SSE subscriber — browser never calls it directly; all traffic goes through the main API

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| One pdfme template → two output paths (PDF + ZPL) | Avoids maintaining a separate ZPL editor or template type | Validated |
| Stateless TCP relay (SSE subscriber, not a spooler) | Keeps service ~100 lines, no DB, no auth, easy to deploy on-prem | Validated |
| `traefik.enable=false` for print service | Print service is an outbound SSE client; no inbound ports needed | Validated |
| ZPL images deferred | `^GFA` bitmap conversion is complex; text + barcodes cover 90% of label use cases | Validated |
| Warehouse app template config in main app (not warehouse app) | Admins configure templates, not operators; main app is the admin surface | Validated |
| "Send to Printer" uses user preference (no dialog dropdown) | Simpler UX — one button per user's configured printer; printer changed in settings, not per-print | Validated |

---
**Current state:** All 4 phases complete. Printing v2 fully operational — template string fields, ZPL transpiler, print service deployed, full-stack integration wired. Milestone v1.0 complete.

*Last updated: 2026-03-20 — Phase 4 complete — Milestone v1.0 complete*
