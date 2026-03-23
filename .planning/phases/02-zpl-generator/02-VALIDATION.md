---
phase: 2
slug: zpl-generator
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest ^4.1.0 |
| **Config file** | `webapps/main/vitest.config.js` |
| **Quick run command** | `cd webapps/main && yarn vitest run src/lib/print/zpl.test.js` |
| **Full suite command** | `cd webapps/main && yarn vitest run` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd webapps/main && yarn vitest run src/lib/print/zpl.test.js`
- **After every plan wave:** Run `cd webapps/main && yarn vitest run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 2-01-01 | 01 | 0 | ZPL-01–05 | unit stub | `cd webapps/main && yarn vitest run src/lib/print/zpl.test.js` | ❌ W0 | ⬜ pending |
| 2-01-02 | 01 | 0 | ZPL-01 | unit | same | ❌ W0 | ⬜ pending |
| 2-02-01 | 02 | 1 | ZPL-02 | unit | same | ❌ W0 | ⬜ pending |
| 2-02-02 | 02 | 1 | ZPL-05 | unit | same | ❌ W0 | ⬜ pending |
| 2-03-01 | 03 | 1 | ZPL-03 | unit | same | ❌ W0 | ⬜ pending |
| 2-03-02 | 03 | 1 | ZPL-03 | unit | same | ❌ W0 | ⬜ pending |
| 2-03-03 | 03 | 1 | ZPL-03 | unit | same | ❌ W0 | ⬜ pending |
| 2-04-01 | 04 | 1 | ZPL-04 | unit | same | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `webapps/main/src/lib/print/zpl.test.js` — stubs for ZPL-01 through ZPL-05
- [ ] `webapps/main/src/lib/print/zpl.js` — implementation module skeleton
- [ ] Export `schemasToV5` and `normalizePageSchema` from `webapps/main/src/lib/print/index.js`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| GS1 DataMatrix is GS1-compliant (FNC1 prefix) | ZPL-03 | Depends on printer firmware; no emulator available | Print label on real Zebra printer, scan with GS1 scanner, verify structured AIs |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
