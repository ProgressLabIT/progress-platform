---
phase: 4
slug: full-integration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest (frontend) |
| **Config file** | `frontend/vitest.config.js` / `webapps/warehouse/vitest.config.js` |
| **Quick run command** | `yarn --cwd frontend test --run` |
| **Full suite command** | `yarn --cwd frontend test --run && yarn --cwd webapps/warehouse test --run` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `yarn --cwd frontend test --run`
- **After every plan wave:** Run `yarn --cwd frontend test --run && yarn --cwd webapps/warehouse test --run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 4-01-01 | 01 | 1 | DIAL-01 | unit | `yarn --cwd frontend test --run` | ❌ W0 | ⬜ pending |
| 4-01-02 | 01 | 1 | DIAL-02 | unit | `yarn --cwd frontend test --run` | ❌ W0 | ⬜ pending |
| 4-01-03 | 01 | 1 | SSE-01/SSE-02 | unit | `yarn --cwd frontend test --run` | ❌ W0 | ⬜ pending |
| 4-02-01 | 02 | 2 | DIAL-03/DIAL-04 | unit | `yarn --cwd frontend test --run` | ❌ W0 | ⬜ pending |
| 4-03-01 | 03 | 3 | WH-01/WH-02 | unit | `yarn --cwd webapps/warehouse test --run` | ❌ W0 | ⬜ pending |
| 4-04-01 | 04 | 4 | DOC-01 | manual | n/a | n/a | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/src/components/print/__tests__/PrintDialog.test.js` — stubs for DIAL-01, DIAL-02, SSE-01, SSE-02
- [ ] `webapps/warehouse/src/__tests__/print.test.js` — stubs for WH-01, WH-02, WH-03

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| End-to-end ZPL print to real LAN printer | DIAL-05 | Requires physical printer hardware | Connect to test ZPL printer, press "Send to Printer", confirm label prints |
| Warehouse operator print flow | WH-03 | Requires warehouse app session + physical printer | Log in as warehouse user, navigate to label print, confirm identical UX |
| Documentation completeness | DOC-01 | Prose quality is subjective | Review `km/print-templates.md` covers all 5 topics listed in success criterion 6 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
