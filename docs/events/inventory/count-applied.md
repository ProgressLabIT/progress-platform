---
title: CountAppliedEvent
description: COUNT_APPLIED — Progress Platform Events Reference
---

# CountAppliedEvent

**EventType:** `COUNT_APPLIED`
**Domain:** inventory
**NATS subject:** `progress.notification.inventory`

Applies a single count record from a count session: creates inventory
adjustment movements and updates `is_in_position` quantities for the
counted product at the counted position.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: COUNT_APPLIED`.

## Preconditions

- `inventory_count_record` exists with key `info.count_record_key`
- `MovementList` exists with key `info.movement_list_key`
- `InventoryCountSession` exists with key `info.inventory_count_session_key`

## State Changes (Transaction)

**Collections:** `inventory_count_record`, `Product`, `MovementList`,
`movement`, `Serial`, `is_in_position`

- `inventory_count_record` updated: marked as processed
- `movement` records inserted for adjustments
- `is_in_position` quantities updated to match counted values

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseInventoryEvent`:
- Publishes to `progress.notification.inventory`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `count_record_key` | `str` | Key of the count record to apply |
| `movement_list_key` | `str` | Key of the adjustment movement list |
| `inventory_count_session_key` | `str` | Key of the parent count session |

## Related Events

_None._

## Source

[`CountAppliedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/inventory/count_applied.py)
