---
title: Warehouse mobile app — User Walkthrough
description: How to use the warehouse SPA for floor operations in Progress Platform.
---

# Warehouse mobile app

<!-- screenshot: warehouse-overview -->

> The warehouse app is a touch-friendly Vue 3 SPA opened in the browser of a barcode-scanner-equipped tablet or fixed workstation on the floor. It covers four operational flows — **Incoming** (receipts), **Transfer** (position-to-position moves), **Shipment** (outgoing picks and packing), and **Inventory** (count sessions and on-the-fly checks) — plus a login screen.
>
> Camera-based barcode reading runs through `@zxing/browser`'s `BrowserMultiFormatReader` against the device's `MediaDevices` API; label printing goes through `browserprint-es` to a directly-addressable network printer. The warehouse app is a pure web application — no app-store installation is required.

## Key screens

### Login

<!-- screenshot: warehouse-login -->

How to reach: open the warehouse SPA URL in the browser (Traefik routes it; see [Deployment](/admins/deployment)). The root path `/` redirects to `/login`.

What you can do here:
- Enter username and password, then submit **Inizia sessione** (`session_start`) to authenticate.
- If the backend returns `action: reset_password`, set and confirm a new password before the session starts.
- After verification, the welcome screen names the operator and redirects to the operator's home — by default `IncomingRoot`, or the `redirect_to` query parameter if one was set.

Expected business logic:
- Authentication posts to `/auth` and stores the returned JWT in a cookie named `Authorization`; the same JWT mechanism backs the main webapp ([API reference](/api/)).
- A successful auth issues a follow-up `POST /session` call which the store treats as the start-of-session signal.

### Incoming

<!-- screenshot: warehouse-incoming -->

How to reach: login → Incoming home (route: `/warehouse/incoming/`, name `IncomingHome`). Open a planned list at `/warehouse/incoming/list/{listKey}` or start a free-form receipt at `/warehouse/incoming/manual` (`IncomingManual`).

What you can do here:
- Browse incoming lists grouped by date and supplier; each card shows the list code and a `completed / planned` row counter.
- Tap **Nuovo** (`incoming_new`) to start a manual receipt that walks through the stages **product → quantity → serials → position → confirm** (the `stageComponentMap` in `IncomingManual.vue`).
- Scan or search a product, set the received quantity, capture serial codes if the product is serialised, and assign the receipt to a destination position.

Expected business logic:
- Confirming a receipt creates inventory movements into the chosen destination position; the resulting domain event is [MovementCompletedEvent](/events/inventory/movement-completed) <!-- TODO: verify slug against docs/events/inventory/ -->.
- Lists flagged `due` (today) and `overdue` (past `due_by`) are highlighted on the home view so the operator can prioritise.

### Transfer

<!-- screenshot: warehouse-transfer -->

How to reach: login → Transfer home (route: `/warehouse/transfer/`, name `TransferRoot`). Manual transfers run at `/warehouse/transfer/manual` (`TransferManual`).

What you can do here:
- Tap **Nuovo trasferimento** (`transfer_new`) and choose the starting axis — **Prodotto** (`product`), **Seriali** (`serial`), or **Posizione** (`position`).
- For a product-led transfer, search the product, pick inventory rows from the available positions (`TransferManualProductInventory`), then choose a destination position (`TransferManualDestination`).
- For a position-led transfer, scan the source position, pick contents to move (`TransferManualPositionContents`), then scan the destination.
- For a serial-led transfer, scan or enter the serial codes (`TransferManualSerials`) before selecting a destination.
- Final stage is `confirm` (`TransferManualConfirm`) — review and commit.

Expected business logic:
- A confirmed transfer records an inventory movement from the source position to the destination position; serials carry through unchanged.
- Cross-link: [MovementCompletedEvent](/events/inventory/movement-completed) <!-- TODO: verify slug against docs/events/inventory/ -->.

### Shipment

<!-- screenshot: warehouse-shipment -->

How to reach: login → Shipment home (route: `/warehouse/shipment/`, name `ShipmentHome`). Open a planned shipping list at `/warehouse/shipment/list/{listKey}` or a manual outbound at `/warehouse/shipment/manual` (`ShipmentManual`).

What you can do here:
- Browse outbound lists grouped by date and customer; the same `completed / planned` counter and `due` / `overdue` highlighting as Incoming.
- Open a list to pick its rows; the item card walks through inventory selection (`ShipmentItemInventorySelection`) and confirmation (`ShipmentItemConfirmation`).
- Tap **Stampa etichetta** (`print_label`) on the selected item to print a product label via `printProductLabel(...)` — this is the `browserprint-es` direct-printer path.
- Tap **Avanti** (`next`) once a quantity is selected, choose source positions, then **Conferma** (`confirm`) to commit.

Expected business logic:
- Confirming an item dispatches one or more `MOVEMENT_UPDATED` events via `sendEventsBulk(...)`, marking planned movements as `completed` with the picked positions and quantities.
- Serial-bearing rows match each scanned inventory line back to the planned movement that already names that serial; non-traceable rows split the planned quantity across the picked positions via `split_into`.

### Inventory (count scanning)

<!-- screenshot: warehouse-inventory -->

How to reach: login → Inventory home (route: `/warehouse/inventory/`, name `InventoryHome`). Open an assigned count session at `/warehouse/inventory/count-session/{countSessionKey}`. Ad-hoc checks live at `/warehouse/inventory/product`, `/warehouse/inventory/serial`, and `/warehouse/inventory/position`.

What you can do here:
- See the list of `started` count sessions assigned to this warehouse, each card showing the session code, description, type, and `due_by` date.
- Open a session — product-typed sessions render `CountingProductBrowser`; position-typed sessions render `CountingPositionBrowser` — and scan positions, products, or serials to record actual on-hand quantities.
- For inventory checks outside a session, jump into **Prodotto** (`product`), **Seriali** (`serial`), or **Posizione** (`position`) browsers to inspect current inventory and search by code.

Expected business logic:
- The session is created and assigned from the main app's [Counting](/users/counting) module; scanning takes place here. The warehouse app loads the session via `loadCountSessionData(...)` and submits scan data back to the API.
- Submitted counts feed into the count session and, on session apply, generate [CountSessionAppliedEvent](/events/inventory/count-session-applied) <!-- TODO: verify slug against docs/events/inventory/ -->.

## Related

- [Counting (main app)](/users/counting) — count sessions are created and assigned here; scanning runs in the warehouse app
- [Deployment](/admins/deployment) — how the warehouse SPA is served and which URL to use
- [Events: inventory](/events/inventory/)
- [Coverage philosophy](/users/coverage)
