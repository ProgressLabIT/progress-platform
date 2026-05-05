---
title: MovementPlannedEvent
description: MOVEMENT_PLANNED — Progress Platform Events Reference
---

# MovementPlannedEvent

**EventType:** `MOVEMENT_PLANNED`
**Domain:** inventory
**NATS subject:** `progress.notification.inventory`

Creates a planned (uncommitted) movement record that can be confirmed later
via `MovementCompletedEvent`. Optionally pre-reserves a serial for the
planned movement.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: MOVEMENT_PLANNED`.

## Preconditions

- Product and positions involved must be valid

## State Changes (Transaction)

**Collections:** `movement`, `Serial`

- `movement` inserted with `status: PLANNED`
- `Serial` updated if a serial is pre-assigned to the movement

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseInventoryEvent`:
- Publishes to `progress.notification.inventory`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `new_movement_key` | `str \| None` | Key to assign to the new movement document |

## Related Events

_None._

## Source

[`MovementPlannedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/inventory/movement_planned.py)
