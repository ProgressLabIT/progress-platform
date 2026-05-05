---
title: BatchReleasedEvent
description: BATCH_RELEASED — Progress Platform Events Reference
---

# BatchReleasedEvent

**EventType:** `BATCH_RELEASED`
**Domain:** production
**NATS subject:** `progress.notification.production`

Records the release of a completed batch to a downstream phase or shipping,
linking the batch with its product, work order, released quantity, and
optional serial keys. This is a lightweight event with no transaction
write collections beyond `Event`.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: BATCH_RELEASED`.

## Preconditions

- Batch exists with key `info.batch_key`

## State Changes (Transaction)

**Collections:** `[]` (no collection writes beyond event log; `BatchReleasedEvent.get_tx_collections()` returns an empty list)

- Event record stored in the event log

## Side Effects (post_processing)

`BatchReleasedEvent` overrides `_notification_subtopic = "production"` directly.
Publishes to `progress.notification.production` after commit.

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `batch_key` | `str` | ArangoDB key of the batch being released |
| `product_key` | `str` | ArangoDB key of the product |
| `work_order_key` | `str` | ArangoDB key of the work order |
| `qt_released` | `float` | Quantity released |
| `serial_keys` | `list[str] \| None` | Serial keys included in the release |

## Related Events

_None._

## Source

[`BatchReleasedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/production/batch_released.py)
