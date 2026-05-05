---
title: WorkSessionClosedEvent
description: WORK_SESSION_CLOSED — Progress Platform Events Reference
---

# WorkSessionClosedEvent

**EventType:** `WORK_SESSION_CLOSED`
**Domain:** work_session
**Broker subject:** `progress.notification.production`

Closes an active work session by setting `active → false` and recording the
`work_session_end` timestamp. Spawned automatically by `JobPausedEvent`,
`BatchCompletedEvent`, and `JobPauseForcedEvent` to ensure sessions are
always closed when the operator stops working.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Spawned as a child event by `JobPausedEvent`, `BatchCompletedEvent`, and
`JobPauseForcedEvent` in `backend/api/events/production/`.

## Preconditions

- `WorkSession` exists with key `info.work_session_key`
- Session `active` is `true`

## State Changes (Transaction)

**Collections:** `WorkSession`

- `WorkSession` updated: `active → false`, `end → info.work_session_end`

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseProductionEvent`:
- Updates `job.last_online`
- Recalculates work order status
- Publishes to `progress.notification.production`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `work_session_key` | `str` | ArangoDB key of the work session to close |
| `work_session_end` | `datetime` | Timestamp when the session ended |

## Related Events

_None._

## Source

[`WorkSessionClosedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/work_session/work_session_closed.py)
