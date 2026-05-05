---
title: Collaboration Events
description: Collaboration domain events - Progress Platform Events Reference.
---

# Collaboration Events

Collaboration-domain events cover issues, tasks, and messages attached to
production entities. NATS subjects are class-specific: `Issue*` events publish
to `progress.notification.issue`, `Task*` events to `progress.notification.task`,
and `Message*` events to `progress.notification.message`. The special case
`TaskUpdatedEvent` overrides `_build_event_payload()` to emit per-user scoped
subjects (`progress.notification.user.{user_key}`).

## Events

| Event | EventType |
|-------|-----------|
| [IssueClosedEvent](/events/collaboration/issue-closed/) | `ISSUE_CLOSED` |
| [IssueCreatedEvent](/events/collaboration/issue-created/) | `ISSUE_CREATED` |
| [IssueDeletedEvent](/events/collaboration/issue-deleted/) | `ISSUE_DELETED` |
| [IssueReopenedEvent](/events/collaboration/issue-reopened/) | `ISSUE_REOPENED` |
| [IssueUpdatedEvent](/events/collaboration/issue-updated/) | `ISSUE_UPDATED` |
| [MessageDeletedEvent](/events/collaboration/message-deleted/) | `MESSAGE_DELETED` |
| [MessagePostedEvent](/events/collaboration/message-posted/) | `MESSAGE_POSTED` |
| [MessageUpdatedEvent](/events/collaboration/message-updated/) | `MESSAGE_UPDATED` |
| [TaskCanceledEvent](/events/collaboration/task-canceled/) | `TASK_CANCELED` |
| [TaskCompletedEvent](/events/collaboration/task-completed/) | `TASK_COMPLETED` |
| [TaskCreatedEvent](/events/collaboration/task-created/) | `TASK_CREATED` |
| [TaskLinkedEvent](/events/collaboration/task-linked/) | `TASK_LINKED` |
| [TaskReopenedEvent](/events/collaboration/task-reopened/) | `TASK_REOPENED` |
| [TaskSuspendedEvent](/events/collaboration/task-suspended/) | `TASK_SUSPENDED` |
| [TaskUnlinkedEvent](/events/collaboration/task-unlinked/) | `TASK_UNLINKED` |
| [TaskUpdatedEvent](/events/collaboration/task-updated/) | `TASK_UPDATED` |
