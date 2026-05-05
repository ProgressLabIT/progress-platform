---
title: MovementReversedEvent
description: MOVEMENT_REVERSED — Progress Platform Events Reference
---

# MovementReversedEvent

**EventType:** `MOVEMENT_REVERSED`
**Domain:** inventory
**NATS subject:** `progress.notification.inventory`

Creates an inverse movement to undo a previously completed movement,
restoring the inventory positions to their pre-movement state. Optionally
reverses only a partial quantity.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: MOVEMENT_REVERSED`.

## Preconditions

- Original movement exists with key `info.original_movement_key`
- Original movement `status` is `COMPLETED`

## State Changes (Transaction)

**Collections:** Inherited from `BaseInventoryEvent.get_tx_collections()`

- `movement` inverse record inserted with `type: REVERSAL`
- `is_in_position` quantities updated to undo the original movement's delta
- Original movement `reversed_by` field updated

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseInventoryEvent`:
- Publishes to `progress.notification.inventory`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `original_movement_key` | `str` | Key of the movement to reverse |
| `inverse_movement_key` | `str \| None` | Key to assign to the reversal movement |
| `quantity_to_revert` | `float \| None` | Partial quantity to revert (null = full reversal) |
| `reason` | `str \| None` | Reason for the reversal |

## Related Events

_None._

## Source

[`MovementReversedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/inventory/movement_reversed.py)
