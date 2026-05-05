---
title: SerialDeletedEvent
description: SERIAL_DELETED — Progress Platform Events Reference
---

# SerialDeletedEvent

**EventType:** `SERIAL_DELETED`
**Domain:** serial
**Broker subject:** `progress.notification.serial`

Deletes a serial, either soft-deleting it (setting `deleted: true`) or
permanently removing the document. Optionally cascades to child serials in
the `contains` hierarchy.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: SERIAL_DELETED`.

## Preconditions

- Serial exists with the key provided in the event's subject context
- If `soft: false`: serial must not be in active inventory

## State Changes (Transaction)

**Collections:** Inherited from `BaseSerialEvent.get_tx_collections()`

- `Serial` soft-deleted (`deleted → true`) or removed
- Child serial records deleted/soft-deleted if `delete_children` is `true`
- `contains` edge records removed for deleted serials

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseSerialEvent`:
- Publishes to `progress.notification.serial`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `soft` | `bool` | If `true`, sets `deleted: true`; if `false`, removes document permanently |
| `delete_children` | `bool \| None` | Whether to cascade deletion to child serials |

## Related Events

_None._

## Source

[`SerialDeletedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/serial/serial_deleted.py)
