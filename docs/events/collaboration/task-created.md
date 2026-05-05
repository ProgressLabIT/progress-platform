---
title: TaskCreatedEvent
description: TASK_CREATED — Progress Platform Events Reference
---

# TaskCreatedEvent

**EventType:** `TASK_CREATED`
**Domain:** collaboration
**Broker subject:** `progress.notification.task`

Creates a new task document with a generated code (via `Counter`) and
optional assignments, dates, and custom extra data.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: TASK_CREATED`.

## Preconditions

- Task type exists with key `info.task_type_key`

## State Changes (Transaction)

**Collections:** `Task`, `Counter`

- `Task` inserted with all provided fields; `code` generated from `Counter`
  if not provided
- `Counter` incremented if used

## Side Effects (post_processing)

Publishes to `progress.notification.task` after commit.

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `task_key` | `str \| None` | Pre-assigned key for the task document |
| `task_type_key` | `str` | ArangoDB key of the task type |
| `code` | `str \| None` | Human-readable task code (auto-generated if absent) |
| `title` | `str \| None` | Task title |
| `description` | `str \| None` | Detailed task description |
| `assigned_to` | `list[TaskAssignment] \| None` | Assignment list |
| `start_from` | `date \| None` | Earliest start date |
| `due_by` | `date \| None` | Due date |
| `created` | `datetime \| None` | Creation timestamp (defaults to now) |
| `created_by` | `str \| None` | User key of the creator |
| `extra` | `Any \| None` | Arbitrary extra data |

## Related Events

_None._

## Source

[`TaskCreatedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/collaboration/task_created.py)
