---
title: IssueUpdatedEvent
description: ISSUE_UPDATED — Progress Platform Events Reference
---

# IssueUpdatedEvent

**EventType:** `ISSUE_UPDATED`
**Domain:** collaboration
**Broker subject:** `progress.notification.issue`

Updates fields of an existing issue (title, description, severity, assignee,
etc.) and recalculates the `critical` production status.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: ISSUE_UPDATED`.

## Preconditions

- Issue exists with the key provided in the event context

## State Changes (Transaction)

**Collections:** `Event`, `Issue`, `issue_rel`, `WorkOrder`, `Job`, `message`

- `Issue` document updated with provided fields
- `WorkOrder` and `Job` `critical` flags recalculated

## Side Effects (post_processing)

Publishes to `progress.notification.issue` after commit.

## InfoModel Fields

_None. (Fields to update are carried in `issue_data`.)_

## Related Events

_None._

## Source

[`IssueUpdatedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/collaboration/issue_updated.py)
