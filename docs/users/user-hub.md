---
title: User Hub — User Walkthrough
description: How to use the User Hub for assignments and personal jobs feed.
---

# User Hub

<!-- screenshot: user-hub-overview -->

> The User Hub is the operator's home screen on login. It collects the jobs
> the operator is assigned to (or that are unassigned and actionable) and the
> tasks routed to them, scoped to the current user.

## Key screens

### Jobs tab

<!-- screenshot: user-hub-jobs -->

How to reach: drawer → **User Hub** → **Jobs** (route: `/app/operator?tab=jobs`).

What you can do here:
- Switch between **card** and **list** layout via the layout toggle.
- **Refresh** the jobs feed.
- Filter jobs by **project**, **work order**, **product**, **phase**, and **started only**.
- Click a job to jump into its work session.

Expected business logic:
- The list shows assigned jobs first, then unassigned-but-actionable jobs (those with `next_batch_available` or an `active_batch_qt`).
- Layout preference (`card` vs `list`) is persisted to the user's profile.
- Starting a job from this list emits [JobStartedEvent](/events/production/job-started); the row count in the tab label tracks the visible-after-filter assigned-job count.

### Tasks tab

<!-- screenshot: user-hub-tasks -->

How to reach: drawer → **User Hub** → **Tasks** (route: `/app/operator?tab=tasks`).

What you can do here:
- Browse tasks routed to the current user.
- **Refresh** the tasks list.

Expected business logic:
- Tasks are loaded for the logged-in user on mount and refreshed on demand.
- Task lifecycle is event-sourced via [TaskCreatedEvent](/events/collaboration/task-created), [TaskCompletedEvent](/events/collaboration/task-completed), [TaskCanceledEvent](/events/collaboration/task-canceled), [TaskReopenedEvent](/events/collaboration/task-reopened), and [TaskSuspendedEvent](/events/collaboration/task-suspended).

## Related

- [Production walkthrough](/users/production)
- [Events: production](/events/production/)
- [Coverage philosophy](/users/coverage)
