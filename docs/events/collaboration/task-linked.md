---
title: TaskLinkedEvent
description: TASK_LINKED — Progress Platform Events Reference
---

# TaskLinkedEvent

**EventType:** `TASK_LINKED`
**Domain:** collaboration
**NATS subject:** `progress.notification.task`

Creates a `task_rel` edge linking a task to another entity (issue, work
order, product, serial, or another task).

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: TASK_LINKED`.

## Preconditions

- Task exists with key `info.task_key`
- Link target exists with key `info.link_key` in the collection corresponding
  to `info.link_type`

## State Changes (Transaction)

**Collections:** `task_rel`

- `task_rel` edge inserted: `_from = Task/{task_key}`,
  `_to = {link_type_collection}/{link_key}`

## Side Effects (post_processing)

Publishes to `progress.notification.task` after commit.

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `task_key` | `str` | ArangoDB key of the task |
| `link_type` | `Literal['issue', 'work_order', 'product', 'serial', 'task']` | Type of entity to link to |
| `link_key` | `str` | ArangoDB key of the target entity |

## Related Events

_None._

## Source

[`TaskLinkedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/collaboration/task_linked.py)
