---
title: API Reference
description: REST API reference for the Progress Platform — Progress Platform.
---

# API Reference

The Progress Platform exposes a REST API documenting every public endpoint
under FastAPI. The reference below is rendered inline from the project's
OpenAPI schema (auto-extracted from FastAPI introspection at build time —
no live app required).

API operations are grouped by **tag**, mirroring the platform domains:

| Tag | Description | URL |
|-----|-------------|-----|
| Production | Work orders, jobs, queues, and work session management | [/api/production/](/api/production/) |
| Warehouse | Inventory positions, movements, counting sessions | [/api/warehouse/](/api/warehouse/) |
| Serial | Serial number lifecycle and Device History Records | [/api/serial/](/api/serial/) |
| Collaboration | Issues, issue types, messages, tasks | [/api/collaboration/](/api/collaboration/) |
| Quality | Form fields, print templates, print jobs | [/api/quality/](/api/quality/) |
| Traceability | Batch execution records, event recording, WIP | [/api/traceability/](/api/traceability/) |
| Process | Process templates, phases, operations, steps | [/api/process/](/api/process/) |
| Product | Product catalogue and BOM management | [/api/product/](/api/product/) |
| Organization | Users, departments, API tokens | [/api/organization/](/api/organization/) |
| Administration | Destructive admin operations, data reset | [/api/administration/](/api/administration/) |
| Configuration | System config, tags, counters, custom data | [/api/configuration/](/api/configuration/) |
| Attachments | File and media management | [/api/attachments/](/api/attachments/) |
| Security | Authentication, session, password reset | [/api/security/](/api/security/) |
| Notification | Server-Sent Events stream | [/api/notification/](/api/notification/) |

## Cross-References

Every operation page links to the events it emits via an "Events Emitted"
section. Browse the full event catalogue at [Events Reference](/events/).

The OpenAPI schema is also available as a static asset at
[`/openapi.json`](/openapi.json) for code-generation tooling.

## Schema Status

> **Note:** `openapi.json` is currently a placeholder populated at CI build time
> by `scripts/export_openapi.py`. Operation pages render via `<OAOperation>`
> once CI runs and the schema is fully populated.
