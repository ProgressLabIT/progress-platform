---
title: Administration — API Reference
description: Administration API operations — Progress Platform.
---

# Administration API

Destructive admin operations — production data reset and forced work order deletion.

> Operations below are scaffolded from FastAPI introspection. Each operation page
> renders inline via `<OAOperation>` once CI populates `openapi.json`.

## Operations

- [DELETE /reset/prod](/api/administration/delete-reset/prod) — Reset all production and traceability data.
- [DELETE /reset/inventory](/api/administration/delete-reset/inventory) — Reset all warehouse/inventory data.
- [DELETE /force-delete-work-order/{work_order_key}](/api/administration/delete-force-delete-work-order/work-order-key) — Force-delete a work order regardless of status.
