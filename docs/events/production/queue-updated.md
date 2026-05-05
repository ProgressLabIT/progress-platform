---
title: QueueUpdatedEvent
description: QUEUE_UPDATED — Progress Platform Events Reference
---

# QueueUpdatedEvent

**EventType:** `QUEUE_UPDATED`
**Domain:** production
**NATS subject:** `progress.notification.production`

Signals that a production queue document has changed. This is a lightweight
notification event — the queue update itself is performed by the calling code,
and this event stores the queue key in the event log for traceability.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: QUEUE_UPDATED`. Also spawned internally by queue
management utilities.

## Preconditions

- Queue exists with key `info.queue_key`

## State Changes (Transaction)

**Collections:** `[]` (no collection writes; `QueueUpdatedEvent.get_tx_collections()` returns empty list)

- Event record stored in the event log

## Side Effects (post_processing)

`QueueUpdatedEvent` sets `_notification_subtopic = "production"` directly.
Publishes to `progress.notification.production` after commit.

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `queue_key` | `str` | ArangoDB key of the queue that was updated |

## Related Events

_None._

## Source

[`QueueUpdatedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/production/queue_updated.py)
