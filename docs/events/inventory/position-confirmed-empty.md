---
title: PositionConfirmedEmptyEvent
description: POSITION_CONFIRMED_EMPTY — Progress Platform Events Reference
---

# PositionConfirmedEmptyEvent

**EventType:** `POSITION_CONFIRMED_EMPTY`
**Domain:** inventory
**NATS subject:** `progress.notification.inventory`

Records that an operator explicitly confirmed a storage position is empty
during a count session. Inserts an `inventory_count_position_complete` record
without a count quantity, distinguishing a confirmed-empty from a counted-zero.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: POSITION_CONFIRMED_EMPTY`.

## Preconditions

- `InventoryCountSession` exists with key `info.session_key`
- Position exists with key `info.position_key`

## State Changes (Transaction)

**Collections:** `inventory_count_position_complete`

- `inventory_count_position_complete` record inserted:
  `session_key`, `position_key`, `confirmed_empty → true`, optional `notes`

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseInventoryEvent`:
- Publishes to `progress.notification.inventory`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `session_key` | `str` | ArangoDB key of the count session |
| `position_key` | `str` | ArangoDB key of the position confirmed empty |
| `notes` | `str \| None` | Operator notes |

## Related Events

_None._

## Source

[`PositionConfirmedEmptyEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/inventory/position_confirmed_empty.py)
