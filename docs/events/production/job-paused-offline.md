---
title: JobPausedOfflineEvent
description: JOB_PAUSED_OFFLINE — Progress Platform Events Reference
---

# JobPausedOfflineEvent

**EventType:** `JOB_PAUSED_OFFLINE`
**Domain:** production
**Broker subject:** `progress.notification.production`

Pauses a job that was detected as offline (e.g., operator disconnected without
explicitly pausing). Records the `work_session_end` timestamp so the work
session duration is accurate even when the session was not closed gracefully.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: JOB_PAUSED_OFFLINE`. Typically called by a background
heartbeat monitor rather than directly by the operator.

## Preconditions

- Job exists with key `info.job_key`
- Job `stage` is `STARTED`

## State Changes (Transaction)

**Collections:** Inherited from `BaseProductionEvent.get_tx_collections()`

- `Job` updated: `stage → PAUSED`
- `WorkSession` closed with the provided `work_session_end` timestamp

## Side Effects (post_processing)

`JobPausedOfflineEvent` sets `_notification_subtopic = "production"` explicitly.
Publishes to `progress.notification.production` after commit.

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `job_key` | `str` | ArangoDB key of the job |
| `work_session_end` | `datetime \| None` | Timestamp to record as session end |
| `work_order_key` | `str \| None` | Work order key |
| `phase_key` | `str \| None` | Phase key |

## Related Events

_None._

## Source

[`JobPausedOfflineEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/production/job_paused_offline.py)
