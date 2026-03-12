---
phase: 1
slug: template-string-plugin
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-12
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest (Wave 0 installs — not yet present) |
| **Config file** | `webapps/main/vitest.config.js` — Wave 0 creates |
| **Quick run command** | `cd webapps/main && npx vitest run src/lib/print/templateResolver.test.js` |
| **Full suite command** | `cd webapps/main && npx vitest run src/lib/print/` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd webapps/main && npx vitest run src/lib/print/templateResolver.test.js`
- **After every plan wave:** Run `cd webapps/main && npx vitest run src/lib/print/`
- **Before `/gsd:verify-work`:** Full suite must be green + manual smoke for TMPL-04 and TMPL-05
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-W0-01 | W0 | 0 | TMPL-02 | unit stub | `cd webapps/main && npx vitest run src/lib/print/templateResolver.test.js` | ❌ W0 | ⬜ pending |
| 1-W0-02 | W0 | 0 | TMPL-03 | unit stub | `cd webapps/main && npx vitest run src/lib/print/plugins/linkedTemplateString.test.js` | ❌ W0 | ⬜ pending |
| 1-01-01 | 01 | 1 | TMPL-02 | unit | `cd webapps/main && npx vitest run src/lib/print/templateResolver.test.js` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | TMPL-02 | unit | `cd webapps/main && npx vitest run src/lib/print/templateResolver.test.js` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 1 | TMPL-03 | unit | `cd webapps/main && npx vitest run src/lib/print/plugins/linkedTemplateString.test.js` | ❌ W0 | ⬜ pending |
| 1-03-01 | 03 | 2 | TMPL-01 | manual smoke | Open designer, add template_string field via toolbar button | N/A | ⬜ pending |
| 1-03-02 | 03 | 2 | TMPL-04 | manual smoke | Add template_string field, type expression, save, reload — check stored value | N/A | ⬜ pending |
| 1-04-01 | 04 | 2 | TMPL-05 | manual smoke | Open print dialog with known product/serial — verify template_expression resolves | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `webapps/main/vitest.config.js` — vitest config pointing to `src/` with `npm install -D vitest`
- [ ] `webapps/main/src/lib/print/templateResolver.test.js` — stubs for TMPL-02 (`slugify`, `encodeExpression`, `decodeExpression`, `resolveExpression`)
- [ ] `webapps/main/src/lib/print/plugins/linkedTemplateString.test.js` — stubs for TMPL-03 (`defaultSchema.linkType`)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Toolbar button adds template_string field to designer | TMPL-01 | UI interaction, Vue component rendering | Open designer, click toolbar button, verify field appears in template schema |
| Designer shows decoded expression in property panel | TMPL-04 | Vue reactivity + pdfme designer propPanel | Add template_string field, type `{{cf::product_color}}`, check label shows human-readable name |
| Saving/reloading preserves encoded expression | TMPL-04 | DB round-trip via API | Save template, reload page, verify stored value is encoded and display is decoded |
| PrintDialog resolves template expressions with live data | TMPL-05 | Requires real production data context | Open print dialog with known product/serial, select template with template_string field, verify resolved value shown |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
