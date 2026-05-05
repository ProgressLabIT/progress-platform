---
title: Process — API Reference
description: Process API operations — Progress Platform.
---

# Process API

Process templates, phases, operations, steps, step media, and process configuration.

> Operations below are scaffolded from FastAPI introspection. Each operation page
> renders inline via `<OAOperation>` once CI populates `openapi.json`.

## Operations

- [GET /operation](/api/process/get-operation) — List all process operations.
- [POST /operation](/api/process/post-operation) — Create a new process operation.
- [PATCH /operation/{operation_key}](/api/process/patch-operation/operation-key) — Update a process operation.
- [DELETE /operation/{operation_key}](/api/process/delete-operation/operation-key) — Delete a process operation.
- [POST /operation/{operation_key}/copy](/api/process/post-operation/operation-key/copy) — Copy an operation to one or more phases.
- [POST /product/{product_key}/process/copy](/api/process/post-product/product-key/process/copy) — Copy a product process template to other products.
- [POST /product/{product_key}/counter/copy](/api/process/post-product/product-key/counter/copy) — Copy counter configuration to other products.
- [GET /step/{step_key}/media](/api/process/get-step/step-key/media) — Fetch media attached to a step.
- [POST /step/{step_key}/media](/api/process/post-step/step-key/media) — Save media to a step.
- [DELETE /step/{step_key}/media/{filename}](/api/process/delete-step/step-key/media/filename) — Delete a step media file.
- [GET /product/{product_key}/process](/api/process/get-product/product-key/process) — Fetch the full production process for a product.
- [PUT /product/{product_key}/process](/api/process/put-product/product-key/process) — Replace the production process for a product.
- [GET /phase](/api/process/get-phase) — Fetch phase data.
- [GET /procedure/{phase_key}](/api/process/get-procedure/phase-key) — Fetch the procedure for a phase.
