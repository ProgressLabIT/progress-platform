---
title: TaskCompletedEvent
description: TASK_COMPLETED — Progress Platform Events Reference
---

# TaskCompletedEvent

**EventType:** `TASK_COMPLETED`
**Domain:** collaboration
**NATS subject:** `progress.notification.task`

Marks a task as completed by setting `status → COMPLETED` and recording
the `closed` timestamp and `closed_by` user key.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: TASK_COMPLETED`.

## Preconditions

- Task exists with key `info.task_key`
- Task `status` is `OPEN` or `IN_PROGRESS`

## State Changes (Transaction)

**Collections:** `Task`

- `Task` updated: `status → COMPLETED`, `closed` timestamp, `closed_by`

## Side Effects (post_processing)

Publishes to `progress.notification.task` after commit.

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `task_key` | `str` | ArangoDB key of the task |
| `closed` | `datetime \| None` | Timestamp of completion (defaults to now) |
| `closed_by` | `str \| None` | User key of the person closing the task |

## Related Events

_None._

## Source

[`TaskCompletedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/collaboration/task_completed.py)
