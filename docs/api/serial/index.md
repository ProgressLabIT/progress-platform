---
title: Serial — API Reference
description: Serial API operations — Progress Platform.
---

# Serial API

Serial number lifecycle — creation, traceability, hierarchy, WIP tracking, and Device History Records.

> Operations below are scaffolded from FastAPI introspection. Each operation page
> renders inline via `<OAOperation>` once CI populates `openapi.json`.

## Operations

- [GET /serial-field](/api/serial/get-serial-field) — Fetch serial field definitions.
- [GET /serial-batch](/api/serial/get-serial-batch) — Get a serial batch.
- [GET /component-batch](/api/serial/get-component-batch) — Get a component batch.
- [GET /serial-parents](/api/serial/get-serial-parents) — Get parent serials.
- [GET /serial-children](/api/serial/get-serial-children) — Get child serials.
- [GET /serial-hierarchy](/api/serial/get-serial-hierarchy) — Get the full serial hierarchy.
- [GET /wip-serial](/api/serial/get-wip-serial) — Get WIP serials.
- [GET /serial-selection](/api/serial/get-serial-selection) — Get serial selection options.
- [GET /serial/{serial_key}](/api/serial/get-serial/serial-key) — Fetch a serial by key.
- [GET /serial-code](/api/serial/get-serial-code) — Fetch a serial by code.
- [GET /serial-code/verify-free](/api/serial/get-serial-code/verify-free) — Verify a serial code is not in use.
- [GET /serial](/api/serial/get-serial) — Search serials.
- [GET /serial/{serial_key}/dhr](/api/serial/get-serial/serial-key/dhr) — Fetch the Device History Record for a serial.
