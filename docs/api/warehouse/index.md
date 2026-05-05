---
title: Warehouse — API Reference
description: Warehouse API operations — Progress Platform.
---

# Warehouse API

Inventory positions, movements, movement lists, counting sessions, and count assignments.

> Operations below are scaffolded from FastAPI introspection. Each operation page
> renders inline via `<OAOperation>` once CI populates `openapi.json`.

## Operations

- [GET /position](/api/warehouse/get-position) — Search inventory positions.
- [POST /position](/api/warehouse/post-position) — Create a new inventory position.
- [GET /position/{position_key}](/api/warehouse/get-position/position-key) — Fetch detailed data for a single position.
- [PATCH /position/{position_key}](/api/warehouse/patch-position/position-key) — Update an existing inventory position.
- [DELETE /position/{position_key}](/api/warehouse/delete-position/position-key) — Delete an inventory position.
- [GET /position-hierarchy](/api/warehouse/get-position-hierarchy) — Return the full position tree rooted at a given position.
- [GET /movement](/api/warehouse/get-movement) — Search the inventory movement journal.
- [POST /movement](/api/warehouse/post-movement) — Search movement lists with POST filters.
- [GET /movement/latest-positions](/api/warehouse/get-movement/latest-positions) — Get positions with recent movement activity.
- [GET /movement/latest-products](/api/warehouse/get-movement/latest-products) — Get products with recent movement activity.
- [GET /movement-list](/api/warehouse/get-movement-list) — Search movement lists.
- [POST /movement-list](/api/warehouse/post-movement-list) — Create a new movement list.
- [GET /inventory](/api/warehouse/get-inventory) — Get current inventory state.
- [POST /inventory/count-session](/api/warehouse/post-inventory/count-session) — Create a new inventory counting session.
- [GET /inventory/count-session](/api/warehouse/get-inventory/count-session) — Search counting sessions.
- [GET /inventory/count-session/{session_key}](/api/warehouse/get-inventory/count-session/session-key) — Fetch a single counting session by key.
- [PUT /inventory/count-session/{session_key}](/api/warehouse/put-inventory/count-session/session-key) — Update a counting session.
- [DELETE /inventory/count-session](/api/warehouse/delete-inventory/count-session) — Delete a counting session.
- [GET /inventory/count-session/{session_key}/processed-records](/api/warehouse/get-inventory/count-session/session-key/processed-records) — Fetch processed records for a counting session.
- [GET /inventory/count-session/{session_key}/completed-positions](/api/warehouse/get-inventory/count-session/session-key/completed-positions) — Get completed positions for a counting session.
- [GET /inventory/count-assignment](/api/warehouse/get-inventory/count-assignment) — Get counting assignments.
- [POST /inventory/count-assignment](/api/warehouse/post-inventory/count-assignment) — Create counting assignments.
- [DELETE /inventory/count-assignment](/api/warehouse/delete-inventory/count-assignment) — Delete counting assignments.
- [GET /inventory/count-record](/api/warehouse/get-inventory/count-record) — Get counting records.
- [GET /inventory/count-position-status](/api/warehouse/get-inventory/count-position-status) — Get count position status.
- [POST /inventory/count-record/import](/api/warehouse/post-inventory/count-record/import) — Import count records in bulk.
