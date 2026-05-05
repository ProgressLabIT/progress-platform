---
title: TaskUpdatedEvent
description: TASK_UPDATED — Progress Platform Events Reference
---

# TaskUpdatedEvent

**EventType:** `TASK_UPDATED`
**Domain:** collaboration
**NATS subject:** `progress.notification.user.{user_key}`

Updates mutable fields of an existing task. Unlike other task events,
`TaskUpdatedEvent` overrides `_build_event_payload()` to emit a
user-scoped NATS subject — each assigned user receives a targeted
notification at `progress.notification.user.{user_key}` rather than the
shared task subject.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: TASK_UPDATED`.

## Preconditions

- Task exists with key `info.task_key`

## State Changes (Transaction)

**Collections:** `Task`

- `Task` updated with any combination of `title`, `description`,
  `assigned_to`, `start_from`, `due_by`, `form_fields`

## Side Effects (post_processing)

Overrides `_build_event_payload()` — publishes to
`progress.notification.user.{user_key}` for each assigned user rather than
the generic task subject.

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `task_key` | `str` | ArangoDB key of the task to update |
| `title` | `str \| None` | New task title |
| `description` | `str \| None` | New task description |
| `assigned_to` | `list[TaskAssignment] \| None` | Updated assignment list |
| `start_from` | `date \| None` | New earliest start date |
| `due_by` | `date \| None` | New due date |
| `form_fields` | `list[TaskFieldUpdate] \| None` | Custom form field updates |

## Related Events

_None._

## Source

[`TaskUpdatedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/collaboration/task_updated.py)
