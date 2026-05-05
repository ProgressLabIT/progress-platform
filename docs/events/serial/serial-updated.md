---
title: SerialUpdatedEvent
description: SERIAL_UPDATED — Progress Platform Events Reference
---

# SerialUpdatedEvent

**EventType:** `SERIAL_UPDATED`
**Domain:** serial
**Broker subject:** `progress.notification.serial`

Updates a serial's code, form data fields, or release status. Can
selectively clear data from specific phases and optionally un-release a
previously released serial.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: SERIAL_UPDATED`. Also spawned as a child event by
`BatchCompletedEvent` when step form data captured during batch completion
needs to be written to associated serials.

## Preconditions

- Serial exists with key `info.serial_key`

## State Changes (Transaction)

**Collections:** Inherited from `BaseSerialEvent.get_tx_collections()`

- `Serial` updated: `code`, `data` (merge or phase-clear), `released` cleared
  if `unrelease` is `true`

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseSerialEvent`:
- Publishes to `progress.notification.serial`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `serial_key` | `str` | ArangoDB key of the serial to update |
| `serial_code` | `ProcessedSerialCode \| None` | New code to assign |
| `serial_data` | `list[SerialFormFieldValue] \| None` | Form field data updates |
| `remove_data_from_phases` | `list[str] \| None` | Phase keys whose data should be cleared |
| `unrelease` | `bool \| None` | If `true`, clears the `released` timestamp |

## Related Events

_None._

## Source

[`SerialUpdatedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/serial/serial_updated.py)
