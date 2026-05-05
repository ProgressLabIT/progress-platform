---
title: TaskReopenedEvent
description: TASK_REOPENED — Progress Platform Events Reference
---

# TaskReopenedEvent

**EventType:** `TASK_REOPENED`
**Domain:** collaboration
**Broker subject:** `progress.notification.task`

Reopens a completed or suspended task by setting `status → OPEN` and
clearing the `closed` timestamp.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: TASK_REOPENED`.

## Preconditions

- Task exists with key `info.task_key`
- Task `status` is `COMPLETED` or `SUSPENDED`

## State Changes (Transaction)

**Collections:** `Task`

- `Task` updated: `status → OPEN`, `closed → null`

## Side Effects (post_processing)

Publishes to `progress.notification.task` after commit.

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `task_key` | `str` | ArangoDB key of the task to reopen |

## Related Events

_None._

## Source

[`TaskReopenedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/collaboration/task_reopened.py)
