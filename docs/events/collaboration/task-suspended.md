---
title: TaskSuspendedEvent
description: TASK_SUSPENDED — Progress Platform Events Reference
---

# TaskSuspendedEvent

**EventType:** `TASK_SUSPENDED`
**Domain:** collaboration
**NATS subject:** `progress.notification.task`

Suspends an open task by setting its `status → SUSPENDED`. Suspended tasks
can be reopened via `TaskReopenedEvent`.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: TASK_SUSPENDED`.

## Preconditions

- Task exists with key `info.task_key`
- Task `status` is `OPEN` or `IN_PROGRESS`

## State Changes (Transaction)

**Collections:** `Task`

- `Task` updated: `status → SUSPENDED`

## Side Effects (post_processing)

Publishes to `progress.notification.task` after commit.

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `task_key` | `str` | ArangoDB key of the task to suspend |

## Related Events

_None._

## Source

[`TaskSuspendedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/collaboration/task_suspended.py)
