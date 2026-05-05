---
title: WorkSessionCreatedEvent
description: WORK_SESSION_CREATED — Progress Platform Events Reference
---

# WorkSessionCreatedEvent

**EventType:** `WORK_SESSION_CREATED`
**Domain:** work_session
**NATS subject:** `progress.notification.production`

Inserts a new `WorkSession` document linking an operator to their active
batch on a job. Each time an operator starts or resumes a job, a new work
session is created. The session records user, job, batch, phase, product,
work order, and an optional end timestamp for pre-set session limits.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Spawned as a child event by `JobStartedEvent` (initial session) and by
`JobResumedEvent` (resumed session) in `backend/api/events/production/`.

## Preconditions

- Job exists with key `info.job_key`
- Batch exists with key `info.batch_key`
- User exists with key `info.user_key`

## State Changes (Transaction)

**Collections:** `WorkSession`

- `WorkSession` document inserted with all provided keys and timestamps

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseProductionEvent`:
- Updates `job.last_online`
- Recalculates work order status
- Publishes to `progress.notification.production`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `user_key` | `str` | ArangoDB key of the operator |
| `user_session_key` | `str \| None` | Optional external user session key |
| `job_key` | `str` | ArangoDB key of the job |
| `batch_key` | `str` | ArangoDB key of the active batch |
| `work_order_key` | `str` | ArangoDB key of the work order |
| `phase_key` | `str` | ArangoDB key of the production phase |
| `product_key` | `str` | ArangoDB key of the product |
| `work_session_end` | `datetime \| None` | Pre-set session end time (for timed sessions) |
| `forced` | `bool \| None` | Whether the session was created by an administrative override |

## Related Events

_None._

## Source

[`WorkSessionCreatedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/work_session/work_session_created.py)
