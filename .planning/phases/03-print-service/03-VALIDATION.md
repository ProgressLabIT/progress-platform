---
phase: 3
slug: print-service
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-18
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + pytest-asyncio |
| **Config file** | `backend/print-service/test_tcp_sender.py` (flat file, no tests/ package) |
| **Quick run command** | `cd backend/print-service && python -m pytest test_tcp_sender.py -x -q` |
| **Full suite command** | `cd backend/print-service && python -m pytest test_tcp_sender.py -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend/print-service && python -m pytest test_tcp_sender.py -x -q`
- **After every plan wave:** Run `cd backend/print-service && python -m pytest test_tcp_sender.py -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 1 | SVC-01, SVC-02 | import | `cd backend/api && PYTHONPATH=. python -c "from models.print_job import PrintJobRequest, PrintJobResult, PrintJobRecord; print('OK')"` | n/a (models) | pending |
| 3-01-02 | 01 | 1 | SVC-01, SVC-02 | grep | `grep -c "def create_print_job\|def print_job_stream\|def print_job_result" backend/api/endpoints/print.py` | n/a (endpoints) | pending |
| 3-02-01 | 02 | 2 | SVC-01, SVC-02 | unit | `cd backend/print-service && python -m pytest test_tcp_sender.py -x -q` | Wave 0 | pending |
| 3-02-02 | 02 | 2 | SVC-04, SVC-05 | syntax | `python -c "import ast; ast.parse(open('backend/print-service/main.py').read())" && docker compose -f deploy/compose/print.yaml config --quiet` | n/a | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `backend/print-service/test_tcp_sender.py` — unit tests for encode_zpl, decode_pdf, send_tcp (created by Plan 02 Task 1 as part of TDD)
- [ ] `backend/print-service/requirements.txt` — pytest and pytest-asyncio listed as dependencies

*Plan 01 (main API endpoints) uses import/grep verification — no separate test file needed.*
*Plan 02 Task 1 is type="tdd" and creates test_tcp_sender.py as part of its RED phase.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real LAN printer receives raw bytes | SVC-01 | Requires physical printer hardware | Connect to LAN printer, POST /api/print-job with ZPL payload, confirm print output |
| Docker compose service starts | SVC-04 | Requires Docker environment | `docker compose -f deploy/compose/print.yaml up`, confirm container healthy |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
