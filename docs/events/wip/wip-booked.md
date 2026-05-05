---
title: WIPBookedEvent
description: WIP_BOOKED — Progress Platform Events Reference
---

# WIPBookedEvent

**EventType:** `WIP_BOOKED`
**Domain:** wip
**NATS subject:** `progress.notification.production`

Books a quantity of WIP (Work-In-Progress) material for a specific phase
of a job, recording the batch and serial keys involved. WIP booking reserves
material that is mid-process and not yet available as finished inventory.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: WIP_BOOKED`. Spawned internally by `BatchCompletedEvent`
at phase boundaries where WIP is transferred.

## Preconditions

- Job exists with key `info.job_key`
- Phase exists with key `info.phase_key`
- Work order exists with key `info.work_order_key`

## State Changes (Transaction)

**Collections:** Inherited from `BaseProductionEvent.get_tx_collections()`

- `wip` document inserted with job, phase, work order, batch, quantity,
  and serial keys

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseProductionEvent`:
- Updates `job.last_online`
- Recalculates work order status
- Publishes to `progress.notification.production`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `job_key` | `str` | ArangoDB key of the job |
| `phase_key` | `str` | ArangoDB key of the phase the WIP is booked for |
| `work_order_key` | `str` | ArangoDB key of the work order |
| `quantity` | `int` | Quantity of units booked as WIP |
| `batch_key` | `str` | ArangoDB key of the batch |
| `batch_serials` | `list[str] \| None` | Serial keys in this WIP booking |

## Related Events

_None._

## Source

[`WIPBookedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/wip/wip_booked.py)
