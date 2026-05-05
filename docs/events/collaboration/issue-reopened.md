---
title: IssueReopenedEvent
description: ISSUE_REOPENED — Progress Platform Events Reference
---

# IssueReopenedEvent

**EventType:** `ISSUE_REOPENED`
**Domain:** collaboration
**NATS subject:** `progress.notification.issue`

Re-opens a previously closed issue by setting `open: true` and clearing the
`closed` timestamp. Updates the `critical` flag on linked work orders and
jobs.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: ISSUE_REOPENED`.

## Preconditions

- Issue exists and `open` is `false`

## State Changes (Transaction)

**Collections:** `Event`, `Issue`, `issue_rel`, `WorkOrder`, `Job`, `message`

- `Issue` updated: `open → true`, `closed → null`
- `WorkOrder` and `Job` `critical` flags recalculated

## Side Effects (post_processing)

Publishes to `progress.notification.issue` after commit.

## InfoModel Fields

_None._

## Related Events

_None._

## Source

[`IssueReopenedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/collaboration/issue_reopened.py)
