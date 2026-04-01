# Messaging Architecture (NATS)

## Overview

The Progress Platform uses **NATS** as its inter-process message bus. NATS handles two distinct communication patterns:

1. **Pub/Sub** — for broadcasting event notifications to all API workers and connected browser clients via SSE
2. **Request/Reply** — for synchronous print job dispatch between the API and the print-service

## Why NATS

- **Lightweight**: Single binary, ~15 MB Docker image, no JVM, no ZooKeeper/KRaft
- **Multi-worker safe**: Each Gunicorn worker subscribes independently; NATS fans out to all subscribers
- **Request/Reply built-in**: Eliminates the need for SSE-based result correlation patterns
- **JetStream** enabled (`-js` flag) for future persistence needs (durable subscriptions, replay)

## Subject Hierarchy

```
progress.
├── notification.
│   ├── inventory      → inventory/warehouse changes
│   ├── serial         → serial/traceability changes
│   ├── task           → task updates (created, updated, completed, canceled, etc.)
│   ├── production     → production events (WO, job, batch, step, queue changes)
│   └── message        → message thread updates (posted, updated, deleted)
├── print.
│   └── jobs.{key}     → print job dispatch (request/reply)
├── serial.
│   └── events         → serial domain events for downstream integration
└── (future)
    ├── chat.{room}
    └── integration.{app}.>
```

### Wildcard Subscriptions

- `progress.notification.>` — all notification subjects (used by API workers for SSE fan-out)
- `progress.print.jobs.*` — all print jobs regardless of printer key
- `progress.>` — everything (useful for debugging/monitoring)

## Architecture

### Notification Flow (Pub/Sub)

> For the full walkthrough of every component and the auto-publish mechanism, see [Notification Flow Deep-Dive](./notification-flow.md).

```
API Worker N          NATS           API Worker M          Browser
     │                  │                  │                  │
     │   publish        │                  │                  │
     ├─────────────────>│   fan-out        │                  │
     │                  ├─────────────────>│                  │
     │                  │                  │   SSE            │
     │                  │                  ├─────────────────>│
```

Each API worker:
1. Connects to NATS at startup (`utils/nats_client.py`)
2. Subscribes to `progress.notification.>` with a callback
3. The callback feeds events into the worker's local `ServerEventManager` instance
4. `ServerEventManager` delivers events to connected SSE clients

**Publishing**: `BaseEvent.save()` automatically publishes the full event data to NATS after a successful transaction commit. Each domain base class declares a `_notification_subtopic` class attribute that determines the NATS subject. The payload includes all `InfoModel` fields plus a `subtopic` routing key and a `notification` backward-compatible alias for `event_type`. Publishing uses `publish_sync()` which bridges from synchronous code to the asyncio event loop via `asyncio.run_coroutine_threadsafe()`.

**Error notifications**: Inventory and serial error notifications (e.g. duplicate serial code, movement exception) use `notify_error()` to publish immediately via `publish_sync()`, bypassing the auto-publish since the transaction will abort.

### Print Job Flow (Request/Reply)

```
Browser → API (POST /print-job) → NATS request → Print Service → NATS reply → API → Browser
```

No SSE, no callbacks, no race conditions. The browser awaits the HTTP response which contains the print result directly. On success, a `PRINT_JOB_COMPLETED` notification is published to `production` via `publish_sync()`.

### Subtopic-to-Subject Mapping

Each domain subtopic maps to a NATS subject. The subtopic string doubles as the SSE routing key used by `ServerEventManager` and the frontend `useSSE()` composable:

```python
SUBTOPIC_TO_SUBJECT = {
    "inventory":   "progress.notification.inventory",
    "serial":      "progress.notification.serial",
    "task":        "progress.notification.task",
    "production":  "progress.notification.production",
    "message":     "progress.notification.message",
}
```

This mapping lives in `backend/api/utils/nats_client.py`.

## Key Files

| File | Purpose |
|------|---------|
| `backend/api/events/base_event.py` | Auto-publish logic (payload building, post-commit publish) |
| `backend/api/utils/nats_client.py` | NATS connection, `publish_sync()`, subject mapping |
| `backend/api/managers/server_event_manager.py` | In-memory SSE queue per worker (fed by NATS callbacks) |
| `backend/api/main.py` | Worker startup: NATS connect + subscribe |
| `backend/api/endpoints/print.py` | Print job endpoint (NATS request/reply) |
| `backend/api/endpoints/notification.py` | SSE endpoint (`GET /notification/{topic}`) |
| `backend/print-service/main.py` | Print service (NATS subscribe + reply) |
| `webapps/main/src/composables/useSSE.js` | Client-side shared SSE composable |

## Adding Targeted Notifications to a New Domain

1. **Add a NATS subject** — add a `"<domain>": "progress.notification.<domain>"` entry to `SUBTOPIC_TO_SUBJECT` in `nats_client.py`. The existing `progress.notification.>` subscription in `main.py` will automatically pick it up.

2. **Add `_notification_subtopic` to your event base class** — the auto-publish in `BaseEvent.save()` handles the rest:

```python
class BaseMyDomainEvent(BaseEvent):
    _notification_subtopic = "<domain>"
```

All events inheriting this class will automatically publish their full `InfoModel` data to NATS after commit. No need to override `post_processing()` for notifications.

3. **Subscribe in the frontend** — use `useSSE('<domain>')` and filter by entity key or event type:

```javascript
const { subscribe } = useSSE('<domain>');
subscribe((message) => {
    let event = JSON.parse(message.data);
    if (event.<entity>_key === current_key) {
        reload();
    }
});
```

4. For subjects outside `progress.notification.*`, add explicit subscriptions in `main.py` startup.

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `PROGRESS_NATS_URL` | `nats://broker:4222` | NATS server URL (API) |
| `PROGRESS_PRINT_SERVICE_NATS_URL` | `nats://broker:4222` | NATS server URL (print-service) |

## Infrastructure

The NATS server runs as the `broker` service in Docker Compose with JetStream enabled:

```yaml
broker:
  image: nats:2-alpine
  hostname: broker
  restart: unless-stopped
  command: ["-js"]
```

Monitoring is available on port 8222 (exposed in dev, not in production by default).
