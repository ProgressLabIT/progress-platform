---
title: IssueDeletedEvent
description: ISSUE_DELETED — Progress Platform Events Reference
---

# IssueDeletedEvent

**EventType:** `ISSUE_DELETED`
**Domain:** collaboration
**NATS subject:** `progress.notification.issue`

Permanently removes an issue document and all associated `issue_rel` edges.
Recalculates the `critical` flag on any linked work orders and jobs after
deletion.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: ISSUE_DELETED`.

## Preconditions

- Issue exists with the key provided in the event context

## State Changes (Transaction)

**Collections:** `Event`, `Issue`, `issue_rel`, `WorkOrder`, `Job`, `message`

- `Issue` document deleted
- `issue_rel` edges deleted
- `WorkOrder` and `Job` `critical` flags recalculated

## Side Effects (post_processing)

Publishes to `progress.notification.issue` after commit.

## InfoModel Fields

_None._

## Related Events

_None._

## Source

[`IssueDeletedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/collaboration/issue_deleted.py)
