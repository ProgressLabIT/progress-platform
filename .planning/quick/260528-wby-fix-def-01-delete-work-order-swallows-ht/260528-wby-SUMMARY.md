---
quick_id: 260528-wby
description: Fix DEF-01 — delete_work_order swallows HTTPException(403) into a 500
date: 2026-05-28
status: complete
commit: f5796a51
---

# Quick Task 260528-wby: Fix DEF-01 — delete_work_order swallows HTTPException(403)

## What changed

`backend/api/endpoints/production.py`, function `delete_work_order`: added a narrow
`except HTTPException: raise` clause immediately before the broad `except Exception as e:`
(~L525). For a started work order the function raises `HTTPException(status_code=403)`
inside the `try`; because `HTTPException` subclasses `Exception`, the broad handler was
catching it, aborting the transaction, and rewrapping it as a generic 500. The new narrow
clause lets intended HTTP errors propagate unchanged.

The 403 branch and the broad `except Exception` body were left exactly as-is. `HTTPException`
was already imported at the top of the module (line 8) — no import added.

Net diff: 2 insertions, 0 deletions, single file.

## Verification

```
cd testing/pytest && DOCKER_HOST=unix:///Users/luca/.docker/run/docker.sock PYTHONUNBUFFERED=1 \
  uv run pytest -q tests/production/test_work_orders.py::TestWorkOrderCRUD::test_delete_started_work_order_returns_403
```

Result:

```
1 passed, 9 warnings in 6.51s
```

(Warnings are pre-existing deprecation notices — unrelated to this change.)

## Commit

- `f5796a51` — fix(production): return 403 (not 500) when deleting a started work order
  - Stages only `backend/api/endpoints/production.py` (`1 file changed, 2 insertions(+)`).

## Scope notes

- Pre-existing unrelated dirty/untracked files (`backend/api/main.py`, `deploy/scripts/db_init.py`,
  `km/README.md`, `RELEASE-NOTES-0.10.md`, `backend/api/utils/error_log.py`,
  `testing/pytest/tests/api/test_error_log.py`, and the `.planning/quick/260528-wby-.../` dir)
  were left untouched. The docs commit is handled by the orchestrator.
- Other broad-except sites in `production.py` were left as-is per the plan's out-of-scope note.
