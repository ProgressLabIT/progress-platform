---
title: BatchCreatedEvent
description: BATCH_CREATED — Progress Platform Events Reference
---

# BatchCreatedEvent

**EventType:** `BATCH_CREATED`
**Domain:** production
**Broker subject:** `progress.notification.production`

Creates a new `Batch` document for a job phase, initialising it with the
job, work order, product, and phase keys. The new batch key is stored in the
parent event's `info` for downstream reference.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Spawned as a child event by `JobStartedEvent` (initial batch) and by
`BatchCompletedEvent` (continuation batch) in
`backend/api/events/production/`.

## Preconditions

- Job exists with key `info.job_key`
- Phase exists with key `info.phase_key`
- Work order exists with key `info.work_order_key`

## State Changes (Transaction)

**Collections:** Inherited from `BaseProductionEvent.get_tx_collections()`

- `Batch` inserted with `job_key`, `phase_key`, `work_order_key`,
  `product_key`, and optional serial links

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseProductionEvent`:
- Updates `job.last_online`
- Recalculates work order status
- Publishes to `progress.notification.production`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `job_key` | `str` | ArangoDB key of the owning job |
| `phase_key` | `str` | ArangoDB key of the production phase |
| `work_order_key` | `str` | ArangoDB key of the work order |
| `product_key` | `str` | ArangoDB key of the product being produced |
| `new_batch_serials` | `list[str] \| None` | Serial keys to pre-associate with the new batch |

## Related Events

_None._

## Source

[`BatchCreatedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/production/batch_created.py)
