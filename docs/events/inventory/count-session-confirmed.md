---
title: CountSessionConfirmedEvent
description: COUNT_SESSION_CONFIRMED — Progress Platform Events Reference
---

# CountSessionConfirmedEvent

**EventType:** `COUNT_SESSION_CONFIRMED`
**Domain:** inventory
**Broker subject:** `progress.notification.inventory`

Confirms a completed inventory count session, triggering the creation of an
adjustment `MovementList` and locking all involved positions. This is the
last operator-facing step before async processing begins via
`CountSessionAppliedEvent`.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: COUNT_SESSION_CONFIRMED`.

## Preconditions

- `InventoryCountSession` exists with key `info.session_key`
- Session `status` is `COMPLETED`

## State Changes (Transaction)

**Collections:** `InventoryCountSession`, `inventory_count_record`,
`Counter`, `Config`, `MovementList`, `is_in_position`

- `InventoryCountSession` updated: `status → PROCESSING`,
  `adjustment_list_key` set
- `MovementList` inserted for adjustments (uses counter if configured)
- `is_in_position` records for all counted positions locked
  (`locked → true`, `locked_by → session_key`)

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseInventoryEvent`:
- Publishes to `progress.notification.inventory`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `session_key` | `str` | ArangoDB key of the inventory count session to confirm |

## Related Events

_None._

## Source

[`CountSessionConfirmedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/inventory/count_session_confirmed.py)
