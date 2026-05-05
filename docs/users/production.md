---
title: Production — User Walkthrough
description: How to use the Production module in Progress Platform.
---

# Production

<!-- screenshot: production-overview -->

> Production tracks work orders through their phase queue, splits each phase
> into jobs, runs jobs as work sessions on the floor, and breaks each session
> into batches and steps. Status, queue order, and progress flow through
> typed events into the production timeline.

## Key screens

### Production overview

<!-- screenshot: production-overview-list -->

How to reach: drawer → **Production** → **Work orders** (route: `/app/production/overview/workorder`).

What you can do here:
- **New** — open the new-work-order form.
- **Sort by date** — re-sort the queue by start date / due date.
- **Save new sequence** — commit a manually re-ordered queue.
- **Cancel changes** — discard a pending re-order.
- Filter the list by code, product, phase, operator, status flags (started, queued, on-time, late, active, idle, ready, critical), and date range.

Expected business logic:
- Work orders are listed in queue order; the queue itself is editable and persisted via [QueueUpdatedEvent](/events/production/queue-updated).
- Switching between **Work orders**, **Job list**, and **Archive** is a tab-route swap inside the same overview page.

### Job list

<!-- screenshot: production-job-list -->

How to reach: drawer → **Production** → **Job list** (route: `/app/production/overview/job`).

What you can do here:
- Filter jobs by work order, product, phase, operator, and assigned/unassigned.
- Double-click a job row to jump straight to its work-order screen.

Expected business logic:
- The job list is the operator-centric flat view of all jobs across open work orders, complementary to the work-order-centric grouping in **Work orders**.

### Work-order detail

<!-- screenshot: production-work-order-detail -->

How to reach: drawer → **Production** → **Work orders** → double-click a row (route: `/app/production/overview/workorder/:wo_key/job-list`).

What you can do here:
- Browse jobs grouped by phase; each phase shows progress, processing time, and assigned operators.
- Switch between sub-tabs **Job list**, **BOM**, **History**, **Issues**, **Notes**, **Messages**, **Traceability**.
- Select jobs (checkboxes) to apply phase- or job-level actions.

Expected business logic:
- Closing a job emits [WorkSessionClosedEvent](/events/work_session/work-session-closed); promoting a planned job to running emits [JobStartedEvent](/events/production/job-started).
- The first job to start on a work order emits [WorkOrderStartedEvent](/events/production/work-order-started).
- Issues opened from this screen tie back to [collaboration events](/events/collaboration/) on the same work-order context.

### Work session

<!-- screenshot: production-work-session -->

How to reach: drawer → **Production** → **Job list** → double-click a job (route: `/app/job/:jobKey`).

What you can do here:
- Drive the running job through its **Steps**, **Docs**, **BOM**, **Notes**, **Issues**, **Messages**, and **Process** sub-tabs.
- **Update** the active batch quantity / serials when the job is active.
- Watch the live job timer when `display_job_timer` is enabled in the job parameters.

Expected business logic:
- Step completion fires [StepCompletedEvent](/events/production/step-completed) and feeds the job-progress percentage on the right-hand panel.
- Closing the active batch emits [BatchCompletedEvent](/events/production/batch-completed); creating the next batch emits [BatchCreatedEvent](/events/production/batch-created).
- Pausing a session emits [JobPausedEvent](/events/production/job-paused) (or [JobPauseForcedEvent](/events/production/job-pause-forced) for supervisor-initiated pauses); resuming emits [JobResumedEvent](/events/production/job-resumed).

### Production process

<!-- screenshot: production-process -->

How to reach: from a work-order or product detail screen, open the process editor.

What you can do here:
- Browse the phase list of a product's process.
- **Edit** to enter edit mode; rename, reorder, or delete phases (delete is blocked when a phase has components).
- Mass-copy a phase's content via the copy icon.

Expected business logic:
- The process is the per-product template that work orders inherit at creation time; edits affect future work orders, not running ones.
- Phase rename and delete are guarded by referential checks (phases with components cannot be deleted).

## Related

- [API reference: production](/api/production/)
- [Events: production](/events/production/)
- [Coverage philosophy](/users/coverage)
