---
title: Traceability — API Reference
description: Traceability API operations — Progress Platform.
---

# Traceability API

Batch execution records, domain event recording, WIP availability, heartbeats, and temporary step data.

> Operations below are scaffolded from FastAPI introspection. Each operation page
> renders inline via `<OAOperation>` once CI populates `openapi.json`.

## Operations

- [POST /event](/api/traceability/post-event) — Record a single domain event.
- [POST /event/bulk](/api/traceability/post-event/bulk) — Record multiple domain events in bulk.
- [GET /event](/api/traceability/get-event) — Fetch domain events.
- [GET /batch/{batch_key}](/api/traceability/get-batch/batch-key) — Fetch batch execution data.
- [GET /batch/{batch_key}/serials](/api/traceability/get-batch/batch-key/serials) — Fetch serials linked to a batch.
- [POST /job/{job_key}/heartbeat](/api/traceability/post-job/job-key/heartbeat) — Send a heartbeat for an active job.
- [GET /wip](/api/traceability/get-wip) — Get WIP availability for a job.
- [POST /batch/temp-data](/api/traceability/post-batch/temp-data) — Store temporary step data for a batch.
- [PUT /batch/{batch_key}/serial-temp-links](/api/traceability/put-batch/batch-key/serial-temp-links) — Create temporary serial links for a batch.
