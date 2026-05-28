---
quick_id: 260528-wby
description: Fix DEF-01 — delete_work_order swallows HTTPException(403) into a 500
date: 2026-05-28
status: ready
must_haves:
  truths:
    - "DELETE /work-order/{key} on a started work order returns 403 (not 500)."
    - "Genuine database/transaction errors in delete_work_order still return 500."
  artifacts:
    - "backend/api/endpoints/production.py"
  key_links:
    - "backend/api/endpoints/production.py delete_work_order (~L458 try / ~L472 raise 403 / ~L525 except)"
    - "testing/pytest/tests/production/test_work_orders.py::TestWorkOrderCRUD::test_delete_started_work_order_returns_403"
---

# Quick Task 260528-wby: Fix DEF-01 — delete_work_order swallows HTTPException(403)

## Problem (DEF-01, deferred from the WO+Job event-sourcing milestone)

`delete_work_order` raises `HTTPException(status_code=403, ...)` (~L472) for a started
work order, **inside** the `try` block. The broad `except Exception as e:` (~L525) catches
it — `HTTPException` subclasses `Exception` — aborts the tx and rewraps it as a generic
500. So `DELETE /work-order/{key}` on a started WO returns 500 instead of the intended 403.

Surfaced by `test_delete_started_work_order_returns_403` (the only red in
`tests/production/test_work_orders.py`: `1 failed, 15 passed`).

## Fix

Add a narrow `except HTTPException: raise` clause immediately **before** the broad
`except Exception` so intended HTTP errors propagate unchanged:

```python
  except HTTPException:
    raise
  except Exception as e:
    tx.abort_transaction()
    ...
```

The 403 branch already calls `tx.abort_transaction()` before raising, so re-raising needs
no extra cleanup. Ensure `HTTPException` is imported in this module (it is — used elsewhere
in `production.py`).

### Task 1 — narrow the except in delete_work_order

File: `backend/api/endpoints/production.py`

action: Insert `except HTTPException: raise` directly above the broad `except Exception as e:`
in `delete_work_order`. Do not change the 403 branch or any other logic.
verify: `cd testing/pytest && DOCKER_HOST=unix:///Users/luca/.docker/run/docker.sock PYTHONUNBUFFERED=1 uv run pytest -q tests/production/test_work_orders.py::TestWorkOrderCRUD::test_delete_started_work_order_returns_403`
done: that test passes (403 returned); the broader file's other delete tests stay green.

## Out of scope

- Other broad-except sites in production.py (legacy; leave unless touched).
