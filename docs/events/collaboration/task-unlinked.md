---
title: TaskUnlinkedEvent
description: TASK_UNLINKED — Progress Platform Events Reference
---

# TaskUnlinkedEvent

**EventType:** `TASK_UNLINKED`
**Domain:** collaboration
**Broker subject:** `progress.notification.task`

Removes a `task_rel` edge, unlinking a task from a previously linked entity.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: TASK_UNLINKED`.

## Preconditions

- Task exists with key `info.task_key`
- A `task_rel` edge exists from the task to the target entity

## State Changes (Transaction)

**Collections:** `task_rel`

- `task_rel` edge deleted where `_from = Task/{task_key}` and
  `_to = {link_type_collection}/{link_key}`

## Side Effects (post_processing)

Publishes to `progress.notification.task` after commit.

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `task_key` | `str` | ArangoDB key of the task |
| `link_type` | `str` | Type of entity being unlinked |
| `link_key` | `str` | ArangoDB key of the target entity |

## Related Events

_None._

## Source

[`TaskUnlinkedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/collaboration/task_unlinked.py)
