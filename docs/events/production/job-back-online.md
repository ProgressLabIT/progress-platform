---
title: JobBackOnlineEvent
description: JOB_BACK_ONLINE — Progress Platform Events Reference
---

# JobBackOnlineEvent

**EventType:** `JOB_BACK_ONLINE`
**Domain:** production
**Broker subject:** `progress.notification.production`

Marks a paused job as back online (re-active) after an offline period,
updating `last_online` and resuming the work session. Counterpart to
`JobPausedOfflineEvent`.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: JOB_BACK_ONLINE`.

## Preconditions

- Job exists with key `info.job_key`
- Job `stage` is `PAUSED` (offline pause)

## State Changes (Transaction)

**Collections:** Inherited from `BaseProductionEvent.get_tx_collections()`

- `Job` updated: `stage → STARTED`, `last_online` refreshed

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseProductionEvent`:
- Updates `job.last_online`
- Recalculates work order status
- Publishes to `progress.notification.production`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `job_key` | `str` | ArangoDB key of the job |
| `work_order_key` | `str \| None` | Work order key |
| `phase_key` | `str \| None` | Phase key |

## Related Events

_None._

## Source

[`JobBackOnlineEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/production/job_back_online.py)
