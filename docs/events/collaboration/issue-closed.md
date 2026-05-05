---
title: IssueClosedEvent
description: ISSUE_CLOSED — Progress Platform Events Reference
---

# IssueClosedEvent

**EventType:** `ISSUE_CLOSED`
**Domain:** collaboration
**NATS subject:** `progress.notification.issue`

Closes an open issue by setting `open: false` and recording the close
timestamp and user. Updates the `critical` flag on linked work orders and
jobs after the issue is no longer active.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: ISSUE_CLOSED`.

## Preconditions

- Issue exists and is in `open` state

## State Changes (Transaction)

**Collections:** `Event`, `Issue`, `issue_rel`, `WorkOrder`, `Job`, `message`

- `Issue` updated: `open → false`, `closed`, `closed_by`
- `WorkOrder` and `Job` `critical` flags recalculated

## Side Effects (post_processing)

Publishes to `progress.notification.issue` after commit.

## InfoModel Fields

_None. (Issue key is resolved from the event's subject context.)_

## Related Events

_None._

## Source

[`IssueClosedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/collaboration/issue_closed.py)
