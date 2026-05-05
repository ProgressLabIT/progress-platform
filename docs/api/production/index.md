---
title: Production — API Reference
description: Production API operations — Progress Platform.
---

# Production API

Work orders, jobs, queues, and work session management.

> Operations below are scaffolded from FastAPI introspection. Each operation page
> renders inline via `<OAOperation>` once CI populates `openapi.json`.

## Operations

- [POST /work-order](/api/production/post-work-order) — Create a new work order with its associated job records.
- [PATCH /work-order/{wo_key}](/api/production/patch-work-order/wo-key) — Update editable fields of an existing work order.
- [PATCH /work-order/{wo_key}/update-quantities](/api/production/patch-work-order/wo-key/update-quantities) — Update the planned quantity of a work order and its jobs.
- [GET /work-order/{wo_key}](/api/production/get-work-order/wo-key) — Fetch full data for a single work order by key.
- [GET /work-order/{wo_key}/traceability](/api/production/get-work-order/wo-key/traceability) — Fetch serial traceability data for a work order.
- [DELETE /work-order/{wo_key}](/api/production/delete-work-order/wo-key) — Delete a work order and its associated jobs.
- [GET /work-order-search-opts](/api/production/get-work-order-search-opts) — Return distinct work order code/project code options for search filters.
- [GET /work-order](/api/production/get-work-order) — Search and filter work orders with optional date range and status filters.
- [GET /queue/site/{site_key}](/api/production/get-queue/site/site-key) — Fetch the work order queue for a given site.
- [PUT /queue](/api/production/put-queue) — Replace the ordered sequence of a site or operator queue.
- [PUT /queue/operator/{operator_key}](/api/production/put-queue/operator/operator-key) — Update the job queue for a specific operator.
- [GET /job](/api/production/get-job) — Return a filtered list of jobs with their assigned operator details.
- [GET /job-assignment](/api/production/get-job-assignment) — Fetch the current job assignment state grouped by operator.
- [GET /job/{job_key}](/api/production/get-job/job-key) — Fetch full working data for a single job by key.
- [GET /work-session](/api/production/get-work-session) — Fetch the currently active work session for a job.
- [POST /job/update](/api/production/post-job/update) — Apply a batch of job insert, update, or close operations.
- [GET /job/{job_key}/time](/api/production/get-job/job-key/time) — Fetch elapsed and estimated time metrics for a job.
