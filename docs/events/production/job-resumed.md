---
title: JobResumedEvent
description: JOB_RESUMED — Progress Platform Events Reference
---

# JobResumedEvent

**EventType:** `JOB_RESUMED`
**Domain:** production
**NATS subject:** `progress.notification.production`

Resumes a paused job: sets `stage → STARTED`, creates a new `WorkSession`,
and optionally updates the active batch's serial keys.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: JOB_RESUMED`.

## Preconditions

- Job exists with key `info.job_key`
- Job `stage` is `PAUSED`

## State Changes (Transaction)

**Collections:** Inherited from `BaseProductionEvent.get_tx_collections()`

- `Job` updated: `stage → STARTED`, `last_online`, `last_work_session_started`
- `WorkSession` inserted via `WorkSessionCreatedEvent` child event
- Active batch serials updated if `info.batch_serials` provided

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseProductionEvent`:
- Updates `job.last_online`
- Recalculates work order status
- Publishes to `progress.notification.production`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `job_key` | `str` | ArangoDB key of the job to resume |
| `batch_serials` | `list[str] \| None` | Updated serial keys for the active batch |
| `work_order_key` | `str \| None` | Work order key |
| `phase_key` | `str \| None` | Phase key |

## Related Events

- [`WorkSessionCreatedEvent`](/events/work_session/work-session-created) — spawned to open a new work session

## Source

[`JobResumedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/production/job_resumed.py)
