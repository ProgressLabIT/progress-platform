---
title: WIPRemovedEvent
description: WIP_REMOVED — Progress Platform Events Reference
---

# WIPRemovedEvent

**EventType:** `WIP_REMOVED`
**Domain:** wip
**NATS subject:** `progress.notification.production`

Removes a quantity of WIP from a job, reducing the `wip` records by
the given amount. Used when material is consumed, rejected, or when a
batch completion removes the WIP that was declared for the phase.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Spawned as a child event by `BatchCompletedEvent` in
`backend/api/events/production/batch_completed.py` when WIP is consumed
by batch completion.

## Preconditions

- Job exists with key `info.job_key`
- Sufficient WIP quantity exists to subtract

## State Changes (Transaction)

**Collections:** Inherited from `BaseProductionEvent.get_tx_collections()`

- `wip` records reduced by `info.quantity`; records fully consumed are deleted

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseProductionEvent`:
- Updates `job.last_online`
- Recalculates work order status
- Publishes to `progress.notification.production`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `job_key` | `str` | ArangoDB key of the job |
| `quantity` | `int` | Quantity of WIP to remove |

## Related Events

_None._

## Source

[`WIPRemovedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/wip/wip_removed.py)
