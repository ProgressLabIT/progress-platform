---
title: Inventory — User Walkthrough
description: How to use the Inventory module in Progress Platform.
---

# Inventory

<!-- screenshot: inventory-overview -->

> Inventory tracks the live stock state across the warehouse: every product
> quantity by position, every booked movement between positions, and the
> position hierarchy itself. Live updates stream over SSE on the
> `inventory` notification subtopic so the table reflects each commit
> without a manual refresh.

## Key screens

### Inventory overview

<!-- screenshot: inventory-list -->

How to reach: drawer → **Warehouse** → **Inventory** (route: `/app/warehouse/overview/inventory`).

What you can do here:
- Browse the live inventory table sorted by `created`, with virtual-scroll paging.
- Filter by **product code**, **position**, and **serial**.
- Read the position path (`A > A1 > A1-shelf-3`) inline on each row.

Expected business logic:
- Each row reflects a product-quantity-position triple kept in sync via [InventoryChangedEvent](/events/inventory/inventory-changed) and the movement family below.
- Refresh fires on incoming `MOVEMENT_COMPLETED`, `MOVEMENT_REVERSED`, `INVENTORY_PRODUCED`, `INVENTORY_CONSUMED`, and `INVENTORY_CHANGED` notifications.

### Movements

<!-- screenshot: inventory-movements -->

How to reach: drawer → **Warehouse** → **Movements** (route: `/app/warehouse/overview/movements`).

What you can do here:
- Sort and scroll the movement ledger (created / start / end timestamps, type, status, planned vs confirmed quantity, user, references).
- Right-click a row for the context menu: **Revert movement** (when reversible), or copy the canceling-movement key when already reversed.
- Double-click a row to open the movement details.

Expected business logic:
- Planning a movement emits [MovementPlannedEvent](/events/inventory/movement-planned); committing it emits [MovementCompletedEvent](/events/inventory/movement-completed); reverting it emits [MovementReversedEvent](/events/inventory/movement-reversed) and back-links the inverse movement key on both rows.
- Editing a movement before completion emits [MovementUpdatedEvent](/events/inventory/movement-updated).

### Positions

<!-- screenshot: inventory-positions -->

How to reach: drawer → **Warehouse** → **Positions** (route: `/app/warehouse/overview/positions`).

What you can do here:
- Browse the position list with virtual-scroll paging; closed positions are dimmed.
- Filter by **search**, **is in position**, **contains position**, and **created date range**.
- Double-click a row to open position details (sub-route `:positionKey`).
- Open the **new position** form from the position-detail surface.

Expected business logic:
- Confirming an empty position emits [PositionConfirmedEmptyEvent](/events/inventory/position-confirmed-empty); the row stays in the list with the closed flag set.
- The position list refreshes on the same movement and inventory notifications as the inventory table, so structural changes are visible immediately.

## Related

- [API reference: warehouse](/api/warehouse/)
- [Events: inventory](/events/inventory/)
- [Coverage philosophy](/users/coverage)
