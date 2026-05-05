---
title: InventoryChangedEvent
description: INVENTORY_CHANGED — Progress Platform Events Reference
---

# InventoryChangedEvent

**EventType:** `INVENTORY_CHANGED`
**Domain:** inventory
**Broker subject:** `progress.notification.inventory`

Updates the `is_in_position` quantity for a product at a position by
applying a signed `quantity_change`. Inserts a new record if none exists,
otherwise updates the existing one. Used as a child event by
`MovementCompletedEvent` for all movement types.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Spawned as a child event by `MovementCompletedEvent` for each position
touched by a movement in `backend/api/events/inventory/movement_completed.py`.

## Preconditions

- Position identified by `info.position_key` exists
- Product identified by `info.product_key` exists

## State Changes (Transaction)

**Collections:** Inherited from `BaseInventoryEvent.get_tx_collections()`

- `is_in_position` record upserted: `quantity` adjusted by `quantity_change`
  (negative values reduce stock)

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseInventoryEvent`:
- Publishes to `progress.notification.inventory`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `position_key` | `str` | ArangoDB key of the storage position |
| `product_key` | `str` | ArangoDB key of the product |
| `serial_key` | `str \| None` | Serial key if this is a serial-tracked item |
| `quantity_change` | `float` | Signed quantity delta (positive = increase, negative = decrease) |

## Related Events

_None._

## Source

[`InventoryChangedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/inventory/inventory_changed.py)
