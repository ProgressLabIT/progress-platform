---
title: TaskCanceledEvent
description: TASK_CANCELED — Progress Platform Events Reference
---

# TaskCanceledEvent

**EventType:** `TASK_CANCELED`
**Domain:** collaboration
**NATS subject:** `progress.notification.task`

Cancels a task by setting its `status` to `CANCELED` and optionally
recording a cancellation reason.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: TASK_CANCELED`.

## Preconditions

- Task exists with key `info.task_key`
- Task is not already canceled or completed

## State Changes (Transaction)

**Collections:** `Task`

- `Task` updated: `status → CANCELED`, optional `reason` stored

## Side Effects (post_processing)

Publishes to `progress.notification.task` after commit.

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `task_key` | `str` | ArangoDB key of the task to cancel |
| `reason` | `str \| None` | Reason for cancellation |

## Related Events

_None._

## Source

[`TaskCanceledEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/collaboration/task_canceled.py)
