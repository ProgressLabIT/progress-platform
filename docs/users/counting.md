---
title: Counting — User Walkthrough
description: How to use the Counting module in Progress Platform.
---

# Counting

<!-- screenshot: counting-overview -->

> Counting models a physical stock-take session. A planner creates the
> session, assigns operators to positions or product lists, operators walk
> the floor and record actual quantities, and applying the session
> reconciles the recorded quantities against the live inventory. The actual
> scanning flow runs in the [warehouse SPA](/users/warehouse); this module
> is the planner-side surface in the main webapp.

## Key screens

### Counting overview

<!-- screenshot: counting-list -->

How to reach: drawer → **Warehouse** → **Count sessions** (route: `/app/warehouse/overview/count-sessions`).

What you can do here:
- Browse the count-session list, sorted by `created`, with status and type chips on each row.
- Double-click a row to open the count-session detail screen.
- Open the **new count session** form (sub-route `count-sessions/new`).

Expected business logic:
- Creating a session emits [CountSessionStartedEvent](/events/inventory/count-session-started) once the planner moves it from `new` to `planned`.
- Sessions are listed live; the table refreshes on inventory-domain notifications.

### Count session — Session data tab

<!-- screenshot: counting-session-data -->

How to reach: drawer → **Warehouse** → **Count sessions** → double-click a session → **Session data** tab (route: `/app/warehouse/overview/count-sessions/:countSessionKey`).

What you can do here:
- Pick the session **type** via the toggle (the available types come from the typed enum on the model).
- Edit **code**, **description**, **scheduled start**, **scheduled end** (each guarded by per-status `canEdit*` flags so locked sessions stay locked).
- Read the live status chip in the header (`new`, `planned`, `processing`, `applied`, etc.) and the processing progress when the session is mid-apply.
- **Start session** when the session is `planned` to promote it to `started`.

Expected business logic:
- Starting the session emits [CountSessionStartedEvent](/events/inventory/count-session-started); resuming a paused session emits [CountSessionResumedEvent](/events/inventory/count-session-resumed); confirming the planner-side review emits [CountSessionConfirmedEvent](/events/inventory/count-session-confirmed); closing the session emits [CountSessionCompletedEvent](/events/inventory/count-session-completed).
- The session data tab is the only tab the planner can edit before the session starts; once `processing`, all tabs disable.

### Count session — Assignments tab

<!-- screenshot: counting-assignments -->

How to reach: drawer → **Warehouse** → **Count sessions** → open a session → **Assignments** tab.

What you can do here:
- Add an operator to the session via the **Add assignment** autocomplete (left column).
- Watch the coverage percentage update as positions or products are assigned.
- Select an assigned operator to inspect their share of the available items in the centre panel.
- Remove an assignment (delete icon) on its row.

Expected business logic:
- Assignments are scoped to either a position tree or a product list, depending on the session type chosen on the data tab.
- Starting an assignment from the warehouse SPA emits [AssignmentStartedEvent](/events/inventory/assignment-started); completing one emits [AssignmentCompletedEvent](/events/inventory/assignment-completed).

### Count session — Records tab

<!-- screenshot: counting-records -->

How to reach: drawer → **Warehouse** → **Count sessions** → open a session → **Records** tab.

What you can do here:
- Browse aggregated count records by product, position, and operator with virtual-scroll paging.
- See the position-coverage indicator (full vs partial) per row when records aggregate across sub-positions.
- Read the multi-user / multi-position badges when several operators or sub-positions roll up into one record.
- See discarded-record counts surfaced as a caption when the empty-state condition fires.

Expected business logic:
- Each record corresponds to a [CountStartedEvent](/events/inventory/count-started) → [CountCompletedEvent](/events/inventory/count-completed) pair on the session, with optional [CountDiscardedEvent](/events/inventory/count-discarded) entries excluded from the aggregate by default.
- Applying the session emits [CountSessionAppliedEvent](/events/inventory/count-session-applied) and the per-record application emits [CountAppliedEvent](/events/inventory/count-applied) entries that reconcile to inventory.

## Related

- [Warehouse mobile app](/users/warehouse) — scanning flow for count sessions
- [API reference: warehouse](/api/warehouse/)
- [Events: inventory](/events/inventory/)
- [Coverage philosophy](/users/coverage)
