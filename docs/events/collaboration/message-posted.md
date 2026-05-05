---
title: MessagePostedEvent
description: MESSAGE_POSTED — Progress Platform Events Reference
---

# MessagePostedEvent

**EventType:** `MESSAGE_POSTED`
**Domain:** collaboration
**Broker subject:** `progress.notification.message`

Inserts a new message in a collaboration thread. The message is linked to a
sender, a recipient (user or group key), and carries the text content.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: MESSAGE_POSTED`.

## Preconditions

- Sender and recipient keys are valid user identifiers

## State Changes (Transaction)

**Collections:** `Event`, `Issue`, `issue_rel`, `WorkOrder`, `Job`, `message`

- `message` document inserted with `sender`, `recipient`, `content`,
  `created` timestamp

## Side Effects (post_processing)

Publishes to `progress.notification.message` after commit.

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `sender` | `str` | User key of the message sender |
| `recipient` | `str` | Recipient key (user or group) |
| `content` | `str` | Message text content |
| `message_key` | `str \| None` | Pre-assigned key for the message document |

## Related Events

_None._

## Source

[`MessagePostedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/collaboration/message_posted.py)
