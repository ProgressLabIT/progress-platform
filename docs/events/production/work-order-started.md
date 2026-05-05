---
title: WorkOrderStartedEvent
description: WORK_ORDER_STARTED — Progress Platform Events Reference
---

# WorkOrderStartedEvent

**EventType:** `WORK_ORDER_STARTED`
**Domain:** production
**Broker subject:** `progress.notification.production`

Records that a work order has transitioned to `STARTED` status. Spawned
automatically by `BaseProductionEvent.update_work_order()` when the work
order's computed status changes from `CREATED` to `STARTED` (i.e., the
first job on the work order is started).

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Spawned as a child event by `BaseProductionEvent.update_work_order()` in
`backend/api/events/production/base_production.py`.

## Preconditions

- Work order exists with key `info.work_order_key`
- Work order was in `CREATED` status before the parent event

## State Changes (Transaction)

**Collections:** `[]` (no writes; `WorkOrderStartedEvent.get_tx_collections()` returns empty list)

- Event record stored in the event log

## Side Effects (post_processing)

`WorkOrderStartedEvent` sets `_notification_subtopic = "production"` directly.
Publishes to `progress.notification.production` after commit.

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `work_order_key` | `str` | ArangoDB key of the work order that started |

## Related Events

_None._

## Source

[`WorkOrderStartedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/production/work_order_events.py)
