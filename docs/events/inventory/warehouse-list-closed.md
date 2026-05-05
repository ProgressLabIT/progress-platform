---
title: WarehouseListClosed
description: WAREHOUSE_LIST_CLOSED — Progress Platform Events Reference
---

# WarehouseListClosed

**EventType:** `WAREHOUSE_LIST_CLOSED`
**Domain:** inventory
**Broker subject:** `progress.notification.inventory`

Closes a warehouse movement list by setting its status to `CLOSED` and
canceling any remaining open planned movements within the list.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: WAREHOUSE_LIST_CLOSED`. Also created directly in
`backend/api/endpoints/inventory.py` at `POST /movement-list` close operation.

## Preconditions

- `MovementList` exists with key `info.movement_list_key`
- Movement list `status` is not already `CLOSED`

## State Changes (Transaction)

**Collections:** `MovementList`, `movement`

- `MovementList` updated: `status → CLOSED`, `end` timestamp set
- Open `movement` records in the list updated: `status → CANCELED`

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseInventoryEvent`:
- Publishes to `progress.notification.inventory`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `movement_list_key` | `str` | ArangoDB key of the movement list to close |

## Related Events

_None._

## Source

[`WarehouseListClosed` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/inventory/warehouse_list_closed.py)
