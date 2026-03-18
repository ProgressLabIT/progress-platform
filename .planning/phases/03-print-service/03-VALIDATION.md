---
phase: 3
slug: print-service
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `print-service/tests/conftest.py` |
| **Quick run command** | `cd print-service && python -m pytest tests/ -x -q` |
| **Full suite command** | `cd print-service && python -m pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd print-service && python -m pytest tests/ -x -q`
- **After every plan wave:** Run `cd print-service && python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 0 | SVC-01 | unit | `cd print-service && python -m pytest tests/test_main.py -x -q` | ❌ W0 | ⬜ pending |
| 3-01-02 | 01 | 1 | SVC-01 | unit | `cd print-service && python -m pytest tests/test_main.py::test_health -x -q` | ❌ W0 | ⬜ pending |
| 3-01-03 | 01 | 1 | SVC-02 | unit | `cd print-service && python -m pytest tests/test_main.py::test_sse_subscribe -x -q` | ❌ W0 | ⬜ pending |
| 3-01-04 | 01 | 1 | SVC-03 | unit | `cd print-service && python -m pytest tests/test_main.py::test_tcp_forward -x -q` | ❌ W0 | ⬜ pending |
| 3-02-01 | 02 | 1 | SVC-04 | unit | `cd print-service && python -m pytest tests/test_main.py::test_zpl_format -x -q` | ❌ W0 | ⬜ pending |
| 3-02-02 | 02 | 1 | SVC-05 | integration | `cd print-service && python -m pytest tests/test_main.py::test_copies -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `print-service/tests/__init__.py` — test package init
- [ ] `print-service/tests/conftest.py` — shared fixtures (mock SSE server, mock TCP socket)
- [ ] `print-service/tests/test_main.py` — stubs for SVC-01 through SVC-05

*Existing infrastructure covers main API side requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real LAN printer receives raw bytes | SVC-01 | Requires physical printer hardware | Connect to LAN printer, `POST /print` with ZPL payload, confirm print output |
| CORS headers accepted by browser | SVC-02 | Requires browser-originated request | Open app in browser, trigger print, confirm no CORS errors in console |
| Docker compose service starts | SVC-04 | Requires Docker environment | `docker compose -f deploy/compose/print.yaml up`, confirm container healthy |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
