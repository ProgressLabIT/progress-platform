---
title: SerialUnlinkedEvent
description: SERIAL_UNLINKED — Progress Platform Events Reference
---

# SerialUnlinkedEvent

**EventType:** `SERIAL_UNLINKED`
**Domain:** serial
**Broker subject:** `progress.notification.serial`

Removes a child serial from its parent by deleting the `contains` edge.
Optionally reverts the inventory movement that was created when the serial
was linked.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: SERIAL_UNLINKED`.

## Preconditions

- Child serial exists with key `info.child_serial_key`
- A `contains` edge exists from child to parent

## State Changes (Transaction)

**Collections:** `contains`, `is_in_position`, `movement`, `Serial`

- `contains` edge deleted
- If `process_inventory`: `is_in_position` and `movement` records updated
  to reflect the unlinking

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseSerialEvent`:
- Publishes to `progress.notification.serial`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `child_serial_key` | `str` | ArangoDB key of the child serial to unlink |
| `parent_serial_key` | `str \| None` | ArangoDB key of the parent serial |
| `batch_key` | `str \| None` | Batch key for context |
| `reason` | `str \| None` | Reason for unlinking |
| `process_inventory` | `bool \| None` | Whether to revert the inventory movement |

## Related Events

_None._

## Source

[`SerialUnlinkedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/serial/serial_unlinked.py)
