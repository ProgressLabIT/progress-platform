---
title: Inventory Events
description: Inventory domain events - Progress Platform Events Reference.
---

# Inventory Events

Inventory-domain events record movements, count sessions, and stock adjustments.
Most inventory events extend `BaseInventoryEvent`, which publishes to
`progress.notification.inventory` after commit. The notable exception is
`CountSessionAppliedEvent`, which extends `BaseEvent` directly and has no
NATS notification — downstream consumers re-read the session state after async
processing completes.

## Events

| Event | EventType |
|-------|-----------|
| [AssignmentCompletedEvent](/events/inventory/assignment-completed/) | `ASSIGNMENT_COMPLETED` |
| [AssignmentStartedEvent](/events/inventory/assignment-started/) | `ASSIGNMENT_STARTED` |
| [CountAppliedEvent](/events/inventory/count-applied/) | `COUNT_APPLIED` |
| [CountCanceledEvent](/events/inventory/count-canceled/) | `COUNT_CANCELED` |
| [CountCompletedEvent](/events/inventory/count-completed/) | `COUNT_COMPLETED` |
| [CountDiscardedEvent](/events/inventory/count-discarded/) | `COUNT_DISCARDED` |
| [CountImportedEvent](/events/inventory/count-imported/) | `COUNT_IMPORTED` |
| [CountSessionAppliedEvent](/events/inventory/count-session-applied/) | `COUNT_SESSION_APPLIED` |
| [CountSessionCompletedEvent](/events/inventory/count-session-completed/) | `COUNT_SESSION_COMPLETED` |
| [CountSessionConfirmedEvent](/events/inventory/count-session-confirmed/) | `COUNT_SESSION_CONFIRMED` |
| [CountSessionResumedEvent](/events/inventory/count-session-resumed/) | `COUNT_SESSION_RESUMED` |
| [CountSessionStartedEvent](/events/inventory/count-session-started/) | `COUNT_SESSION_STARTED` |
| [CountStartedEvent](/events/inventory/count-started/) | `COUNT_STARTED` |
| [InventoryChangedEvent](/events/inventory/inventory-changed/) | `INVENTORY_CHANGED` |
| [MovementCompletedEvent](/events/inventory/movement-completed/) | `MOVEMENT_COMPLETED` |
| [MovementPlannedEvent](/events/inventory/movement-planned/) | `MOVEMENT_PLANNED` |
| [MovementReversedEvent](/events/inventory/movement-reversed/) | `MOVEMENT_REVERSED` |
| [MovementUpdatedEvent](/events/inventory/movement-updated/) | `MOVEMENT_UPDATED` |
| [PositionConfirmedEmptyEvent](/events/inventory/position-confirmed-empty/) | `POSITION_CONFIRMED_EMPTY` |
| [WarehouseListClosed](/events/inventory/warehouse-list-closed/) | `WAREHOUSE_LIST_CLOSED` |
