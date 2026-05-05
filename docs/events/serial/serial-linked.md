---
title: SerialLinkedEvent
description: SERIAL_LINKED — Progress Platform Events Reference
---

# SerialLinkedEvent

**EventType:** `SERIAL_LINKED`
**Domain:** serial
**Broker subject:** `progress.notification.serial`

Links a child serial to a parent serial via the `contains` edge collection,
optionally moving the child's inventory record from its current position and
replacing an existing parent link.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: SERIAL_LINKED`. Also spawned as a child event by
`BatchCompletedEvent` when batch serials are linked to a parent assembly.

## Preconditions

- Child serial exists with key `info.child_serial_key`
- Parent serial exists with key `info.parent_serial_key` (if provided)

## State Changes (Transaction)

**Collections:** `contains`, `is_in_position`, `movement`, `Serial`

- `contains` edge inserted linking child to parent
- `is_in_position` record for child serial updated or moved
- `movement` record inserted if inventory movement is processed
- Existing `contains` edge replaced if `replace_existing` is `true`

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseSerialEvent`:
- Publishes to `progress.notification.serial`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `child_serial_key` | `str` | ArangoDB key of the child serial |
| `parent_serial_key` | `str \| None` | ArangoDB key of the parent serial |
| `wo_key` | `str \| None` | Work order key for context |
| `component_key` | `str \| None` | BOM component key |
| `batch_key` | `str \| None` | Batch key for context |
| `phase_key` | `str \| None` | Phase key for context |
| `job_key` | `str \| None` | Job key for context |
| `process_inventory` | `bool \| None` | Whether to move inventory when linking |
| `replace_existing` | `bool \| None` | Whether to replace an existing parent link |

## Related Events

_None._

## Source

[`SerialLinkedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/serial/serial_linked.py)
