---
title: AssignmentStartedEvent
description: ASSIGNMENT_STARTED — Progress Platform Events Reference
---

# AssignmentStartedEvent

**EventType:** `ASSIGNMENT_STARTED`
**Domain:** inventory
**NATS subject:** `progress.notification.inventory`

Marks a count assignment as started, recording when an operator begins
working the delegated portion of an inventory count session.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: ASSIGNMENT_STARTED`.

## Preconditions

- Assignment exists with key `info.assignment_key`

## State Changes (Transaction)

**Collections:** `[]` (no writes beyond event log)

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

[`AssignmentStartedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/inventory/assignment_started.py)
