---
title: AssignmentCompletedEvent
description: ASSIGNMENT_COMPLETED — Progress Platform Events Reference
---

# AssignmentCompletedEvent

**EventType:** `ASSIGNMENT_COMPLETED`
**Domain:** inventory
**NATS subject:** `progress.notification.inventory`

Marks a count assignment as completed. A count assignment represents a
portion of an inventory count session delegated to a specific operator or
position. This event records the completion state of the assignment document.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: ASSIGNMENT_COMPLETED`.

## Preconditions

- Assignment exists with key `info.assignment_key`

## State Changes (Transaction)

**Collections:** `[]` (no writes beyond event log; `AssignmentCompletedEvent.get_tx_collections()` returns empty list)

- Event record stored in the event log

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseInventoryEvent`:
- Publishes to `progress.notification.inventory`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `assignment_key` | `str` | ArangoDB key of the count assignment |

## Related Events

_None._

## Source

[`AssignmentCompletedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/inventory/assignment_completed.py)
