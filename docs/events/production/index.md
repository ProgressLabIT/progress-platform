---
title: Production Events
description: Production domain events - Progress Platform Events Reference.
---

# Production Events

Production-domain events govern the lifecycle of work orders, jobs, batches,
steps, and work sessions. Every production event extends `BaseProductionEvent`,
which sets `_notification_subtopic = "production"` — all production events
publish to `progress.notification.production` after transaction commit.
`BaseProductionEvent.post_processing()` also updates `job.last_online` and
recalculates work order status after each commit.

## Events

| Event | EventType |
|-------|-----------|
| [ActiveBatchChangedEvent](/events/production/active-batch-changed) | `ACTIVE_BATCH_CHANGED` |
| [BatchCompletedEvent](/events/production/batch-completed) | `BATCH_COMPLETED` |
| [BatchCreatedEvent](/events/production/batch-created) | `BATCH_CREATED` |
| [BatchReleasedEvent](/events/production/batch-released) | `BATCH_RELEASED` |
| [JobBackOnlineEvent](/events/production/job-back-online) | `JOB_BACK_ONLINE` |
| [JobPauseForcedEvent](/events/production/job-pause-forced) | `JOB_PAUSE_FORCED` |
| [JobPausedEvent](/events/production/job-paused) | `JOB_PAUSED` |
| [JobPausedOfflineEvent](/events/production/job-paused-offline) | `JOB_PAUSED_OFFLINE` |
| [JobResumedEvent](/events/production/job-resumed) | `JOB_RESUMED` |
| [JobStartedEvent](/events/production/job-started) | `JOB_STARTED` |
| [QueueUpdatedEvent](/events/production/queue-updated) | `QUEUE_UPDATED` |
| [StepCompletedEvent](/events/production/step-completed) | `STEP_COMPLETED` |
| [StepEditedEvent](/events/production/step-edited) | `STEP_EDITED` |
| [WorkOrderStartedEvent](/events/production/work-order-started) | `WORK_ORDER_STARTED` |
