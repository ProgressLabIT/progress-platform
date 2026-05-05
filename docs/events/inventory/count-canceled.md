---
title: CountCanceledEvent
description: COUNT_CANCELED — Progress Platform Events Reference
---

# CountCanceledEvent

**EventType:** `COUNT_CANCELED`
**Domain:** inventory
**Broker subject:** `progress.notification.inventory`

Cancels a pending count record and releases the associated position locks in
`is_in_position`. Allows an operator to abandon an in-progress count without
applying it.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: COUNT_CANCELED`.

## Preconditions

- Count record exists with key `info.count_key`

## State Changes (Transaction)

**Collections:** `is_in_position`, `inventory_count_record`

- `inventory_count_record` updated: `canceled` flag set
- `is_in_position` records unlocked for the affected inventory keys

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseInventoryEvent`:
- Publishes to `progress.notification.inventory`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `count_key` | `str` | ArangoDB key of the count record to cancel |
| `inventory_keys` | `list[str] \| None` | Keys of `is_in_position` records to unlock |

## Related Events

_None._

## Source

[`CountCanceledEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/inventory/count_canceled.py)
