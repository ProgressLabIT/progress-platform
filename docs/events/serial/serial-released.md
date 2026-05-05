---
title: SerialReleasedEvent
description: SERIAL_RELEASED — Progress Platform Events Reference
---

# SerialReleasedEvent

**EventType:** `SERIAL_RELEASED`
**Domain:** serial
**NATS subject:** `progress.notification.serial`

Releases a serial by setting its `released` timestamp, making it available
for shipment and downstream traceability queries. Spawned as a child event
by `BatchCompletedEvent` when the batch's serials are released on completion.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: SERIAL_RELEASED`. Also spawned as a child event by
`BatchCompletedEvent` in `backend/api/events/production/batch_completed.py`.

## Preconditions

- Serial exists with the key provided in the event context
- Serial is not already released

## State Changes (Transaction)

**Collections:** Inherited from `BaseSerialEvent.get_tx_collections()`

- `Serial` updated: `released` timestamp set

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseSerialEvent`:
- Publishes to `progress.notification.serial`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `released` | `datetime \| None` | Release timestamp (defaults to current time) |

## Related Events

_None._

## Source

[`SerialReleasedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/serial/serial_released.py)
