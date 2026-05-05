---
title: CountStartedEvent
description: COUNT_STARTED — Progress Platform Events Reference
---

# CountStartedEvent

**EventType:** `COUNT_STARTED`
**Domain:** inventory
**Broker subject:** `progress.notification.inventory`

Registers a new count record within a session and locks the relevant
`is_in_position` records so no concurrent movements can alter the position
while counting is in progress.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: COUNT_STARTED`.

## Preconditions

- `InventoryCountSession` exists with key `info.inventory_count_session_key`

## State Changes (Transaction)

**Collections:** `is_in_position`, `inventory_count_record`, `Product`,
`InventoryCountSession`

- `inventory_count_record` inserted with session key and position/product info
- `is_in_position` records for the position locked
  (`locked → true`, `locked_by → session_key`)
- Product snapshot captured for the count record

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseInventoryEvent`:
- Publishes to `progress.notification.inventory`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `count_key` | `str` | ArangoDB key for the new count record |
| `inventory_count_session_key` | `str` | Key of the parent count session |
| `assignment_key` | `str \| None` | Key of the assignment this count belongs to |
| `inventory_keys` | `list[str] \| None` | Specific `is_in_position` keys to lock |
| `product_key` | `str \| None` | Product being counted |
| `position_key` | `str \| None` | Position being counted |

## Related Events

_None._

## Source

[`CountStartedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/inventory/count_started.py)
