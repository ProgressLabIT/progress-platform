---
title: CountSessionCompletedEvent
description: COUNT_SESSION_COMPLETED — Progress Platform Events Reference
---

# CountSessionCompletedEvent

**EventType:** `COUNT_SESSION_COMPLETED`
**Domain:** inventory
**NATS subject:** `progress.notification.inventory`

Marks all count records in a session as complete and transitions the session
to `COMPLETED` status, ready for the confirmation step.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: COUNT_SESSION_COMPLETED`.

## Preconditions

- `InventoryCountSession` exists with key `info.session_key`
- All count records in the session are in a completable state

## State Changes (Transaction)

**Collections:** `InventoryCountSession`, `inventory_count_record`

- `InventoryCountSession` updated: `status → COMPLETED`
- Any remaining open `inventory_count_record` records finalized

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseInventoryEvent`:
- Publishes to `progress.notification.inventory`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `session_key` | `str` | ArangoDB key of the inventory count session |

## Related Events

_None._

## Source

[`CountSessionCompletedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/inventory/count_session_completed.py)
