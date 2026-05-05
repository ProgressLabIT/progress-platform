---
title: MessageDeletedEvent
description: MESSAGE_DELETED — Progress Platform Events Reference
---

# MessageDeletedEvent

**EventType:** `MESSAGE_DELETED`
**Domain:** collaboration
**Broker subject:** `progress.notification.message`

Soft-deletes a message in a collaboration thread by setting its `deleted`
flag. The message document is retained for audit purposes.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: MESSAGE_DELETED`.

## Preconditions

- Message exists with key `info.message_key`

## State Changes (Transaction)

**Collections:** `Event`, `Issue`, `issue_rel`, `WorkOrder`, `Job`, `message`

- `message` updated: `deleted → true`

## Side Effects (post_processing)

Publishes to `progress.notification.message` after commit.

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `message_key` | `str` | ArangoDB key of the message to delete |

## Related Events

_None._

## Source

[`MessageDeletedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/collaboration/message_deleted.py)
