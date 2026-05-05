---
title: Events Reference
description: Domain events emitted by the Progress Platform - Progress Platform Events Reference.
---

# Events Reference

Every state change in the Progress Platform that requires post-commit
side effects flows through a typed **Event** object. Events are
applied within an ArangoDB transaction and, on commit, publish
notifications via NATS subjects (consumed by the SSE stream and the
Sparkplug bridge).

The catalogue below is auto-extracted from `backend/api/events/` on every
push to `DEV`. The top-10 events have hand-crafted sequence diagrams; the
remainder ship with auto-extracted InfoModel and post-processing summaries
(suitable for catalogue navigation, not deep-dive walkthroughs).

## Quick navigation by domain

- [Production](/events/production/) — 14 events
- [Inventory](/events/inventory/) — 18 events
- [Serial](/events/serial/) — 6 events
- [Collaboration](/events/collaboration/) — 13 events
- [Admin](/events/admin/) — 1 event
- [WIP](/events/wip/) — 4 events
- [Work Session](/events/work_session/) — 3 events

## Full event index

| Event | Domain | EventType | NATS Subject |
|-------|--------|-----------|--------------|
| [ExtraUpdateRequestedEvent](/events/admin/extra-update-requested) | admin | `EXTRA_UPDATE_REQUESTED` | — |
| [IssueClosedEvent](/events/collaboration/issue-closed) | collaboration | `ISSUE_CLOSED` | `progress.notification.issue` |
| [IssueCreatedEvent](/events/collaboration/issue-created) | collaboration | `ISSUE_CREATED` | `progress.notification.issue` |
| [IssueDeletedEvent](/events/collaboration/issue-deleted) | collaboration | `ISSUE_DELETED` | `progress.notification.issue` |
| [IssueReopenedEvent](/events/collaboration/issue-reopened) | collaboration | `ISSUE_REOPENED` | `progress.notification.issue` |
| [IssueUpdatedEvent](/events/collaboration/issue-updated) | collaboration | `ISSUE_UPDATED` | `progress.notification.issue` |
| [MessageDeletedEvent](/events/collaboration/message-deleted) | collaboration | `MESSAGE_DELETED` | `progress.notification.message` |
| [MessagePostedEvent](/events/collaboration/message-posted) | collaboration | `MESSAGE_POSTED` | `progress.notification.message` |
| [MessageUpdatedEvent](/events/collaboration/message-updated) | collaboration | `MESSAGE_UPDATED` | `progress.notification.message` |
| [TaskCanceledEvent](/events/collaboration/task-canceled) | collaboration | `TASK_CANCELED` | `progress.notification.task` |
| [TaskCompletedEvent](/events/collaboration/task-completed) | collaboration | `TASK_COMPLETED` | `progress.notification.task` |
| [TaskCreatedEvent](/events/collaboration/task-created) | collaboration | `TASK_CREATED` | `progress.notification.task` |
| [TaskLinkedEvent](/events/collaboration/task-linked) | collaboration | `TASK_LINKED` | `progress.notification.task` |
| [TaskReopenedEvent](/events/collaboration/task-reopened) | collaboration | `TASK_REOPENED` | `progress.notification.task` |
| [TaskSuspendedEvent](/events/collaboration/task-suspended) | collaboration | `TASK_SUSPENDED` | `progress.notification.task` |
| [TaskUnlinkedEvent](/events/collaboration/task-unlinked) | collaboration | `TASK_UNLINKED` | `progress.notification.task` |
| [TaskUpdatedEvent](/events/collaboration/task-updated) | collaboration | `TASK_UPDATED` | `progress.notification.user.{user_key}` |
| [AssignmentCompletedEvent](/events/inventory/assignment-completed) | inventory | `ASSIGNMENT_COMPLETED` | `progress.notification.inventory` |
| [AssignmentStartedEvent](/events/inventory/assignment-started) | inventory | `ASSIGNMENT_STARTED` | `progress.notification.inventory` |
| [CountAppliedEvent](/events/inventory/count-applied) | inventory | `COUNT_APPLIED` | `progress.notification.inventory` |
| [CountCanceledEvent](/events/inventory/count-canceled) | inventory | `COUNT_CANCELED` | `progress.notification.inventory` |
| [CountCompletedEvent](/events/inventory/count-completed) | inventory | `COUNT_COMPLETED` | `progress.notification.inventory` |
| [CountDiscardedEvent](/events/inventory/count-discarded) | inventory | `COUNT_DISCARDED` | `progress.notification.inventory` |
| [CountImportedEvent](/events/inventory/count-imported) | inventory | `COUNT_IMPORTED` | `progress.notification.inventory` |
| [CountSessionAppliedEvent](/events/inventory/count-session-applied) | inventory | `COUNT_SESSION_APPLIED` | — |
| [CountSessionCompletedEvent](/events/inventory/count-session-completed) | inventory | `COUNT_SESSION_COMPLETED` | `progress.notification.inventory` |
| [CountSessionConfirmedEvent](/events/inventory/count-session-confirmed) | inventory | `COUNT_SESSION_CONFIRMED` | `progress.notification.inventory` |
| [CountSessionResumedEvent](/events/inventory/count-session-resumed) | inventory | `COUNT_SESSION_RESUMED` | `progress.notification.inventory` |
| [CountSessionStartedEvent](/events/inventory/count-session-started) | inventory | `COUNT_SESSION_STARTED` | `progress.notification.inventory` |
| [CountStartedEvent](/events/inventory/count-started) | inventory | `COUNT_STARTED` | `progress.notification.inventory` |
| [InventoryChangedEvent](/events/inventory/inventory-changed) | inventory | `INVENTORY_CHANGED` | `progress.notification.inventory` |
| [MovementCompletedEvent](/events/inventory/movement-completed) | inventory | `MOVEMENT_COMPLETED` | `progress.notification.inventory` |
| [MovementPlannedEvent](/events/inventory/movement-planned) | inventory | `MOVEMENT_PLANNED` | `progress.notification.inventory` |
| [MovementReversedEvent](/events/inventory/movement-reversed) | inventory | `MOVEMENT_REVERSED` | `progress.notification.inventory` |
| [MovementUpdatedEvent](/events/inventory/movement-updated) | inventory | `MOVEMENT_UPDATED` | `progress.notification.inventory` |
| [PositionConfirmedEmptyEvent](/events/inventory/position-confirmed-empty) | inventory | `POSITION_CONFIRMED_EMPTY` | `progress.notification.inventory` |
| [WarehouseListClosed](/events/inventory/warehouse-list-closed) | inventory | `WAREHOUSE_LIST_CLOSED` | `progress.notification.inventory` |
| [ActiveBatchChangedEvent](/events/production/active-batch-changed) | production | `ACTIVE_BATCH_CHANGED` | `progress.notification.production` |
| [BatchCompletedEvent](/events/production/batch-completed) | production | `BATCH_COMPLETED` | `progress.notification.production` |
| [BatchCreatedEvent](/events/production/batch-created) | production | `BATCH_CREATED` | `progress.notification.production` |
| [BatchReleasedEvent](/events/production/batch-released) | production | `BATCH_RELEASED` | `progress.notification.production` |
| [JobBackOnlineEvent](/events/production/job-back-online) | production | `JOB_BACK_ONLINE` | `progress.notification.production` |
| [JobPauseForcedEvent](/events/production/job-pause-forced) | production | `JOB_PAUSE_FORCED` | `progress.notification.production` |
| [JobPausedEvent](/events/production/job-paused) | production | `JOB_PAUSED` | `progress.notification.production` |
| [JobPausedOfflineEvent](/events/production/job-paused-offline) | production | `JOB_PAUSED_OFFLINE` | `progress.notification.production` |
| [JobResumedEvent](/events/production/job-resumed) | production | `JOB_RESUMED` | `progress.notification.production` |
| [JobStartedEvent](/events/production/job-started) | production | `JOB_STARTED` | `progress.notification.production` |
| [QueueUpdatedEvent](/events/production/queue-updated) | production | `QUEUE_UPDATED` | `progress.notification.production` |
| [StepCompletedEvent](/events/production/step-completed) | production | `STEP_COMPLETED` | `progress.notification.production` |
| [StepEditedEvent](/events/production/step-edited) | production | `STEP_EDITED` | `progress.notification.production` |
| [WorkOrderStartedEvent](/events/production/work-order-started) | production | `WORK_ORDER_STARTED` | `progress.notification.production` |
| [SerialCreatedEvent](/events/serial/serial-created) | serial | `SERIAL_CREATED` | `progress.notification.serial` |
| [SerialDeletedEvent](/events/serial/serial-deleted) | serial | `SERIAL_DELETED` | `progress.notification.serial` |
| [SerialLinkedEvent](/events/serial/serial-linked) | serial | `SERIAL_LINKED` | `progress.notification.serial` |
| [SerialReleasedEvent](/events/serial/serial-released) | serial | `SERIAL_RELEASED` | `progress.notification.serial` |
| [SerialUnlinkedEvent](/events/serial/serial-unlinked) | serial | `SERIAL_UNLINKED` | `progress.notification.serial` |
| [SerialUpdatedEvent](/events/serial/serial-updated) | serial | `SERIAL_UPDATED` | `progress.notification.serial` |
| [WIPBookedEvent](/events/wip/wip-booked) | wip | `WIP_BOOKED` | `progress.notification.production` |
| [WIPDeclaredEvent](/events/wip/wip-declared) | wip | `WIP_DECLARED` | `progress.notification.production` |
| [WIPRemovedEvent](/events/wip/wip-removed) | wip | `WIP_REMOVED` | `progress.notification.production` |
| [WIPUnbookedEvent](/events/wip/wip-unbooked) | wip | `WIP_UNBOOKED` | `progress.notification.production` |
| [WorkSessionCanceledEvent](/events/work_session/work-session-canceled) | work_session | `WORK_SESSION_CANCELED` | `progress.notification.production` |
| [WorkSessionClosedEvent](/events/work_session/work-session-closed) | work_session | `WORK_SESSION_CLOSED` | `progress.notification.production` |
| [WorkSessionCreatedEvent](/events/work_session/work-session-created) | work_session | `WORK_SESSION_CREATED` | `progress.notification.production` |

> **NATS subject taxonomy:** Production / Inventory / Serial / Issue / Task / Message
> subtopics map to `progress.notification.<subtopic>`. The Sparkplug
> bridge consumes a subset of these for upstream MES integrations —
> see ADR-0002 in the Sparkplug demo workstream for the locked taxonomy.
>
> Events with NATS Subject `—` do not publish a notification on commit.
> `CountSessionAppliedEvent` extends `BaseEvent` directly (bypassing
> `BaseInventoryEvent`) so its `_notification_subtopic` is `null` — downstream
> consumers re-read canonical session state after async processing completes.
> `ExtraUpdateRequestedEvent` (admin) similarly has no subtopic override on its
> base class.
