---
title: MessageUpdatedEvent
description: MESSAGE_UPDATED — Progress Platform Events Reference
---

# MessageUpdatedEvent

**EventType:** `MESSAGE_UPDATED`
**Domain:** collaboration
**Broker subject:** `progress.notification.message`

Updates the content of an existing message. Records an `edited` timestamp
for audit purposes.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: MESSAGE_UPDATED`.

## Preconditions

- Message exists with key `info.message_key`
- Message is not deleted

## State Changes (Transaction)

**Collections:** `Event`, `Issue`, `issue_rel`, `WorkOrder`, `Job`, `message`

- `message` updated: `content` replaced, `edited` timestamp set

## Side Effects (post_processing)

Publishes to `progress.notification.message` after commit.

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `message_key` | `str` | ArangoDB key of the message to update |
| `content` | `str` | New message text content |

## Related Events

_None._

## Source

[`MessageUpdatedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/collaboration/message_updated.py)
