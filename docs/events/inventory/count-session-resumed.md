---
title: CountSessionResumedEvent
description: COUNT_SESSION_RESUMED — Progress Platform Events Reference
---

# CountSessionResumedEvent

**EventType:** `COUNT_SESSION_RESUMED`
**Domain:** inventory
**NATS subject:** `progress.notification.inventory`

Resumes a paused inventory count session, setting its status back to `STARTED`
so operators can continue adding count records.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: COUNT_SESSION_RESUMED`.

## Preconditions

- `InventoryCountSession` exists with key `info.session_key`
- Session `status` is `PAUSED`

## State Changes (Transaction)

**Collections:** `InventoryCountSession`

- `InventoryCountSession` updated: `status → STARTED`

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseInventoryEvent`:
- Publishes to `progress.notification.inventory`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `session_key` | `str` | ArangoDB key of the inventory count session to resume |

## Related Events

_None._

## Source

[`CountSessionResumedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/inventory/count_session_resumed.py)
