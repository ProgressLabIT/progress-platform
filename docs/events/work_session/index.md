---
title: Work Session Events
description: Work Session domain events - Progress Platform Events Reference.
---

# Work Session Events

Work session events record when an operator opens, closes, or cancels their
active session on a job batch. Work sessions are child records tied to a
specific job + batch + phase + user combination. These events extend
`BaseProductionEvent` and publish to `progress.notification.production` after
commit.

## Events

| Event | EventType |
|-------|-----------|
| [WorkSessionCanceledEvent](/events/work_session/work-session-canceled/) | `WORK_SESSION_CANCELED` |
| [WorkSessionClosedEvent](/events/work_session/work-session-closed/) | `WORK_SESSION_CLOSED` |
| [WorkSessionCreatedEvent](/events/work_session/work-session-created/) | `WORK_SESSION_CREATED` |
