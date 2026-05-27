# Tasks

## Overview

Tasks are first-class work items in the collaboration domain. They track discrete units of work, can be linked to other entities (issues, work orders, products, serials, other tasks), and carry a structured form that operators fill during execution.

## Lifecycle

```
pending → open → completed
                ↘ canceled
```

- **pending** — created but not yet started
- **open** — actively being worked on
- **completed** — closed successfully
- **canceled** — closed without completion (status-only change, document preserved)

State transitions are immutable events stored in the `Event` collection. Lifecycle events: `TASK_CREATED`, `TASK_UPDATED`, `TASK_COMPLETED`, `TASK_CANCELED`, `TASK_REOPENED`, `TASK_SUSPENDED`, `TASK_LINKED`, `TASK_UNLINKED`, `TASK_DELETED`.

## Deletion Semantics

Deletion logic lives in `TaskDeletedEvent` (`backend/api/events/collaboration/task_deleted.py`). The decision of whether to hard- or soft-delete is made at delete time inside the event's `apply()`, never pre-computed.

### Hard Delete

**Condition:** the only event referencing this `task_key` is `TASK_CREATED` — the task has no history.

**Effect:**
- `Task` document removed.
- All `task_rel` edges (both directions) removed.
- The `TASK_CREATED` event record removed.
- The `TASK_DELETED` audit event is **retained** as the sole record that a task existed.

### Soft Delete

**Condition:** one or more events beyond `TASK_CREATED` reference this `task_key` (e.g. the task was updated, linked, completed, or canceled before being deleted).

**Effect:**
- `Task.deleted` set to the deletion timestamp.
- `Task.deleted_by` set to the `_key` of the `TASK_DELETED` event (use this to trace back to the actor and timestamp via the `Event` collection).
- Document stays in the database; all history is preserved.
- **Filtered from all query results** via `FILTER t.deleted == null` in `FIND_TASKS` and `GET_TASK_DATA` AQL queries (`backend/api/utils/collaboration.py`).

### Why event_key, not user_key in `deleted_by`

`deleted_by` stores the event key rather than the user key so you can retrieve the full deletion context (actor, timestamp, session, IP, context) with a single document lookup. The user key is available on the event itself.

## API

| Method | Path | Description |
|--------|------|-------------|
| `DELETE` | `/task/{task_key}` | Delete single task. Returns `mode: 'hard' \| 'soft'`. |
| `POST` | `/task/bulk-delete` | Delete multiple tasks. Returns per-task results with `mode`, `success`, `error`. |

Both endpoints guard against deleting already-deleted tasks (404) and return the delete mode so callers can surface appropriate feedback.

## Frontend UX

- **Task overview (bulk):** edit mode exposes a delete button. Single confirm dialog, then call bulk endpoint. If any result has `mode: 'soft'`, an informational notify explains some tasks were hidden rather than permanently deleted.
- **Task detail:** delete icon button always visible. Confirm once, then navigate back on success. Soft-delete results in an explanatory notify.

## Performance Note

The hard/soft check executes `FOR e IN Event FILTER e.task_key == @task_key AND e.event_type != 'TASK_CREATED' LIMIT 1`. Confirm a compound persistent index exists on `Event[task_key, event_type]` to keep this lookup O(log n) as the event log grows.
