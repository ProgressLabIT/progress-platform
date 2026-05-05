---
title: JobPauseForcedEvent
description: JOB_PAUSE_FORCED — Progress Platform Events Reference
---

# JobPauseForcedEvent

**EventType:** `JOB_PAUSE_FORCED`
**Domain:** production
**Broker subject:** `progress.notification.production`

Administratively forces a running job into paused state. Unlike the
voluntary `JobPausedEvent`, this event flags the job with `forced` after
commit via `BaseAdmin.post_processing()`. Used by supervisors to halt work
without operator consent.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: JOB_PAUSE_FORCED`.

## Preconditions

- Job exists with key `info.job_key`
- Job `stage` is `STARTED`

## State Changes (Transaction)

**Collections:** Inherited from `BaseProductionEvent.get_tx_collections()`

- `Job` updated: `stage → PAUSED`
- Work session closed via `WorkSessionClosedEvent` child event

## Side Effects (post_processing)

Extends `BaseAdmin.post_processing()`:
- Calls `update_work_order()`
- Sets `job.forced = event_key` to mark the forced intervention

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `job_key` | `str` | ArangoDB key of the job to force-pause |
| `work_order_key` | `str \| None` | Work order key |
| `phase_key` | `str \| None` | Phase key |

## Related Events

- [`WorkSessionClosedEvent`](/events/work_session/work-session-closed) — spawned to close the active work session

## Source

[`JobPauseForcedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/production/job_pause_forced.py)
