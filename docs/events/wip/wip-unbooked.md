---
title: WIPUnbookedEvent
description: WIP_UNBOOKED — Progress Platform Events Reference
---

# WIPUnbookedEvent

**EventType:** `WIP_UNBOOKED`
**Domain:** wip
**Broker subject:** `progress.notification.production`

Reverses a WIP booking, releasing material that was reserved for a phase
back to the previous phase or pool. Used when a batch or job is reset or
when WIP needs to be redistributed.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: WIP_UNBOOKED`.

## Preconditions

- Job exists with key `info.job_key`
- WIP booking exists for the job

## State Changes (Transaction)

**Collections:** Inherited from `BaseProductionEvent.get_tx_collections()`

- `wip` booking record deleted or reduced by `info.quantity`

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseProductionEvent`:
- Updates `job.last_online`
- Recalculates work order status
- Publishes to `progress.notification.production`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `job_key` | `str` | ArangoDB key of the job |
| `quantity` | `int` | Quantity of WIP to unbook |

## Related Events

_None._

## Source

[`WIPUnbookedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/wip/wip_unbooked.py)
