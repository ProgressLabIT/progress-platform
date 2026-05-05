---
title: Configuration — API Reference
description: Configuration API operations — Progress Platform.
---

# Configuration API

System configuration, tags, counters, and custom data management.

> Operations below are scaffolded from FastAPI introspection. Each operation page
> renders inline via `<OAOperation>` once CI populates `openapi.json`.

## Operations

- [GET /config](/api/configuration/get-config) — Fetch system configuration.
- [PATCH /config](/api/configuration/patch-config) — Update system configuration fields.
- [PUT /config/{key}/file](/api/configuration/put-config/key/file) — Update a file-type configuration entry.
- [GET /tag](/api/configuration/get-tag) — List all tags.
- [POST /tag](/api/configuration/post-tag) — Create a new tag.
- [POST /tag/update-connections](/api/configuration/post-tag/update-connections) — Update tag connections.
- [POST /counter](/api/configuration/post-counter) — Create a new counter.
- [GET /counter](/api/configuration/get-counter) — Fetch counter definitions.
- [PUT /counter/{counter_key}](/api/configuration/put-counter/counter-key) — Replace counter metadata.
- [DELETE /counter/{counter_key}](/api/configuration/delete-counter/counter-key) — Delete a counter.
- [GET /custom-data](/api/configuration/get-custom-data) — List custom data entries.
- [GET /custom-data/{key}](/api/configuration/get-custom-data/key) — Fetch a custom data entry.
- [PUT /custom-data/{key}](/api/configuration/put-custom-data/key) — Upsert a custom data entry.
- [DELETE /custom-data/{key}](/api/configuration/delete-custom-data/key) — Delete a custom data entry.
