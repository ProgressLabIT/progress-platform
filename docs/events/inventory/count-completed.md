---
title: CountCompletedEvent
description: COUNT_COMPLETED — Progress Platform Events Reference
---

# CountCompletedEvent

**EventType:** `COUNT_COMPLETED`
**Domain:** inventory
**NATS subject:** `progress.notification.inventory`

Marks a single count record as completed by recording the counted quantity,
optional serial keys, and notes. Updates the `is_in_position` lock state and
writes a `inventory_count_position_complete` record.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: COUNT_COMPLETED`.

## Preconditions

- Count record exists with key `info.count_key`

## State Changes (Transaction)

**Collections:** `inventory_count_record`, `is_in_position`,
`inventory_count_position_complete`

- `inventory_count_record` updated: `count_qt`, `count_serial_keys`, `notes`, completed
- `inventory_count_position_complete` record inserted to mark position as counted
- `is_in_position` lock status updated

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseInventoryEvent`:
- Publishes to `progress.notification.inventory`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `count_key` | `str` | ArangoDB key of the count record |
| `count_qt` | `float` | Quantity counted |
| `count_serial_keys` | `list[str] \| None` | Serial keys counted at this position |
| `notes` | `str \| None` | Operator notes for the count |

## Related Events

_None._

## Source

[`CountCompletedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/inventory/count_completed.py)
