---
title: CountDiscardedEvent
description: COUNT_DISCARDED — Progress Platform Events Reference
---

# CountDiscardedEvent

**EventType:** `COUNT_DISCARDED`
**Domain:** inventory
**Broker subject:** `progress.notification.inventory`

Discards a completed or pending count record, removing it from the session
without applying any inventory adjustments.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: COUNT_DISCARDED`.

## Preconditions

- Count record exists with key `info.count_key`

## State Changes (Transaction)

**Collections:** `inventory_count_record`

- `inventory_count_record` updated: `discarded` flag set

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseInventoryEvent`:
- Publishes to `progress.notification.inventory`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `count_key` | `str` | ArangoDB key of the count record to discard |

## Related Events

_None._

## Source

[`CountDiscardedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/inventory/count_discarded.py)
