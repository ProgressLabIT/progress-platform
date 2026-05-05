---
title: WorkSessionCanceledEvent
description: WORK_SESSION_CANCELED — Progress Platform Events Reference
---

# WorkSessionCanceledEvent

**EventType:** `WORK_SESSION_CANCELED`
**Domain:** work_session
**Broker subject:** `progress.notification.production`

Cancels a work session, marking it as canceled without recording a normal
end. Used in administrative corrections when a session must be voided —
for example during a job reset or when a session was opened in error.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: WORK_SESSION_CANCELED`. Also spawned internally by
admin event flows that cancel all open sessions for a job.

## Preconditions

- `WorkSession` exists with key `info.work_session_key`

## State Changes (Transaction)

**Collections:** Inherited from `BaseProductionEvent.get_tx_collections()`

- `WorkSession` updated: `canceled → event_key`, `active → false`

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseProductionEvent`:
- Updates `job.last_online`
- Recalculates work order status
- Publishes to `progress.notification.production`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `work_session_key` | `str` | ArangoDB key of the work session to cancel |

## Related Events

_None._

## Source

[`WorkSessionCanceledEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/work_session/work_session_canceled.py)
