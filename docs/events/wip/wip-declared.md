---
title: WIPDeclaredEvent
description: WIP_DECLARED — Progress Platform Events Reference
---

# WIPDeclaredEvent

**EventType:** `WIP_DECLARED`
**Domain:** wip
**NATS subject:** `progress.notification.production`

Declares a quantity of material as WIP at a job boundary — typically when
a batch enters a phase but has not been booked with full serial detail yet.
Spawned by `BatchCompletedEvent` to update WIP availability for the
next phase.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Spawned as a child event by `BatchCompletedEvent` in
`backend/api/events/production/batch_completed.py` when WIP needs to be
declared for the next phase.

## Preconditions

- Job exists with key `info.job_key`

## State Changes (Transaction)

**Collections:** Inherited from `BaseProductionEvent.get_tx_collections()`

- `wip` document inserted with job key, quantity, and optional serial keys

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseProductionEvent`:
- Updates `job.last_online`
- Recalculates work order status
- Publishes to `progress.notification.production`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `job_key` | `str` | ArangoDB key of the job |
| `quantity` | `int` | Quantity of units declared as WIP |
| `serial_keys` | `list[str] \| None` | Serial keys included in the WIP declaration |

## Related Events

_None._

## Source

[`WIPDeclaredEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/wip/wip_declared.py)
