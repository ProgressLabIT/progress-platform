---
title: ActiveBatchChangedEvent
description: ACTIVE_BATCH_CHANGED — Progress Platform Events Reference
---

# ActiveBatchChangedEvent

**EventType:** `ACTIVE_BATCH_CHANGED`
**Domain:** production
**Broker subject:** `progress.notification.production`

Updates the active batch quantity on a job and optionally sets the serial
keys associated with that batch. Used when the operator adjusts how many
units are in the current batch before completing it.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: ACTIVE_BATCH_CHANGED`.

## Preconditions

- Job exists with key `info.job_key`
- Job has an active batch

## State Changes (Transaction)

**Collections:** Inherited from `BaseProductionEvent.get_tx_collections()`

- `Job` updated: `active_batch_qt → info.new_active_batch_qt`
- `Batch` updated: `qt_total → info.new_active_batch_qt`, `batch_serials` set if provided

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseProductionEvent`:
- Updates `job.last_online`
- Recalculates work order status
- Publishes to `progress.notification.production`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `job_key` | `str` | ArangoDB key of the job |
| `new_active_batch_qt` | `int` | New quantity for the active batch |
| `batch_serials` | `list[str] \| None` | Serial keys to associate with the updated batch |

## Related Events

_None._

## Source

[`ActiveBatchChangedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/production/active_batch_changed.py)
