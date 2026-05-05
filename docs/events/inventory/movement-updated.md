---
title: MovementUpdatedEvent
description: MOVEMENT_UPDATED — Progress Platform Events Reference
---

# MovementUpdatedEvent

**EventType:** `MOVEMENT_UPDATED`
**Domain:** inventory
**NATS subject:** `progress.notification.inventory`

Updates a planned movement's confirmed quantity, positions, or splits it into
multiple movements. Adjusts `is_in_position` balances accordingly and
optionally updates associated serial records.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: MOVEMENT_UPDATED`.

## Preconditions

- Movement exists with key `info.movement_key`
- Movement `status` is `PLANNED` or `STARTED`

## State Changes (Transaction)

**Collections:** `movement`, `is_in_position`, `Serial`

- `movement` updated: `qt_confirmed`, `qt_planned`, `position_from`,
  `position_to`; split into child movements if `split_into` provided
- `is_in_position` balances recalculated
- `Serial` records updated if serial tracking is involved

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseInventoryEvent`:
- Publishes to `progress.notification.inventory`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `movement_key` | `str` | Key of the movement to update |
| `qt_confirmed` | `float` | Updated confirmed quantity |
| `qt_planned` | `float` | Updated planned quantity |
| `split_into` | `list[MovementSplitData] \| None` | Split definitions to divide movement into sub-movements |
| `position_from` | `str \| None` | Updated source position |
| `position_to` | `str \| None` | Updated destination position |

## Related Events

_None._

## Source

[`MovementUpdatedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/inventory/movement_updated.py)
