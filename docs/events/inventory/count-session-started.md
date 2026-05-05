---
title: CountSessionStartedEvent
description: COUNT_SESSION_STARTED — Progress Platform Events Reference
---

# CountSessionStartedEvent

**EventType:** `COUNT_SESSION_STARTED`
**Domain:** inventory
**NATS subject:** `progress.notification.inventory`

Creates a new `InventoryCountSession` document with `status: STARTED`,
initialising the session for count record collection.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: COUNT_SESSION_STARTED`.

## Preconditions

- `count_session_key` provided or generated

## State Changes (Transaction)

**Collections:** `InventoryCountSession`

- `InventoryCountSession` inserted: `status → STARTED`, `start` timestamp

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseInventoryEvent`:
- Publishes to `progress.notification.inventory`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `count_session_key` | `str` | ArangoDB key for the new count session |

## Related Events

_None._

## Source

[`CountSessionStartedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/inventory/count_session_started.py)
