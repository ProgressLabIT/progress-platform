---
title: ExtraUpdateRequestedEvent
description: EXTRA_UPDATE_REQUESTED — Progress Platform Events Reference
---

# ExtraUpdateRequestedEvent

**EventType:** `EXTRA_UPDATE_REQUESTED`
**Domain:** admin
**NATS subject:** —

Stores arbitrary extra data on a job or work order document without going
through the standard production event flow. Used for operator-assisted data
corrections or custom field updates that do not map to a domain event.

::: warning No NATS notification
`ExtraUpdateRequestedEvent` extends `BaseAdmin`, which itself extends
`BaseProductionEvent`. However, `ExtraUpdateRequestedEvent` does not set
`_notification_subtopic`, so no NATS message is published after commit.
:::

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: EXTRA_UPDATE_REQUESTED`.

## Preconditions

- Entity identified by `info.entity_type` + `info.entity_key` exists

## State Changes (Transaction)

**Collections:** `Job`, `WorkOrder`

- Target document (`Job` or `WorkOrder`) updated: `extra` field set to
  `info.extra_data`

## Side Effects (post_processing)

Extends `BaseAdmin.post_processing()`:
- Calls `update_work_order()`
- Sets `job.forced = event_key`
- No NATS publish (no `_notification_subtopic`)

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `entity_type` | `Literal['job', 'work_order']` | Type of entity to update |
| `entity_key` | `str` | ArangoDB key of the entity |
| `extra_data` | `Any` | Arbitrary data to store in the `extra` field |
| `job_key` | `str \| None` | Job key (for post_processing context) |
| `work_order_key` | `str \| None` | Work order key (for post_processing context) |

## Related Events

_None._

## Source

[`ExtraUpdateRequestedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/admin/extra_update_requested.py)
