---
title: JobPausedEvent
description: JOB_PAUSED — Progress Platform Events Reference
---

# JobPausedEvent

**EventType:** `JOB_PAUSED`
**Domain:** production
**Broker subject:** `progress.notification.production`

Pauses an active job, setting its stage to `PAUSED` and closing the
current work session. The job remains assigned and the active batch is
preserved. Used for voluntary operator pauses during normal operation.

## Sequence Diagram

```mermaid
sequenceDiagram
  participant U as User
  participant API as FastAPI
  participant E as JobPausedEvent
  participant DB as ArangoDB
  participant N as Broker
  participant WSC as WorkSessionClosedEvent

  U->>API: POST /event (event_type: JOB_PAUSED)
  API->>E: Event.save()

  rect rgb(232, 245, 233)
    Note over E,DB: ArangoDB transaction
    E->>DB: pre_processing()
    E->>DB: apply() — Job.stage = PAUSED
    E->>WSC: create_as_child (close current WorkSession)
    E->>DB: store_event()
  end
  Note right of E: commit_transaction

  E-->>N: publish progress.notification.production
  API-->>U: 200 OK
```

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: JOB_PAUSED`.

## Preconditions

- Job exists with key `info.job_key`
- Job `stage` is `STARTED`

## State Changes (Transaction)

**Collections:** Inherited from `BaseProductionEvent.get_tx_collections()`

- `Job` updated: `stage → PAUSED`
- `WorkSession` closed via `WorkSessionClosedEvent` child event

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseProductionEvent`:
- Updates `job.last_online`
- Recalculates work order status
- Publishes to `progress.notification.production`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `job_key` | `str` | ArangoDB key of the job to pause |
| `work_order_key` | `str \| None` | Work order key |
| `phase_key` | `str \| None` | Phase key |

## Related Events

- [`WorkSessionClosedEvent`](/events/work_session/work-session-closed) — spawned to close the current work session

## Source

[`JobPausedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/production/job_paused.py)
