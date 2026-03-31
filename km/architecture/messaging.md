# Messaging Architecture (NATS)

## Overview

The Progress Platform uses **NATS** as its inter-process message bus, replacing the previous Apache Kafka setup. NATS handles two distinct communication patterns:

1. **Pub/Sub** — for broadcasting notifications to all API workers and connected browser clients via SSE
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
│   ├── global         → global REFRESH events (data changed, reload views)
│   ├── inventory      → inventory/warehouse changes
│   ├── serial         → serial/traceability changes
│   └── task           → task updates
├── print.
│   └── jobs.{key}     → print job dispatch (request/reply)
├── serial.
│   └── events         → serial domain events for downstream integration
└── (future)
    ├── chat.{room}
    ├── workorder.{event}
    ├── message.{thread}
    └── integration.{app}.>
```

### Wildcard Subscriptions

- `progress.notification.>` — all notification subjects (used by API workers for SSE fan-out)
- `progress.print.jobs.*` — all print jobs regardless of printer key
- `progress.>` — everything (useful for debugging/monitoring)

## Architecture

### Notification Flow (Pub/Sub)

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

**Publishing**: `NotificationManager` uses `ConflatedDelayedQueue` to batch and conflate events (e.g., global REFRESH is conflated over 5 seconds). When the queue fires, it publishes to the appropriate NATS subject via `asyncio.run_coroutine_threadsafe()` (since the queue runs on a background thread).

### Print Job Flow (Request/Reply)

```
Browser → API (POST /print-job) → NATS request → Print Service → NATS reply → API → Browser
```

No SSE, no callbacks, no race conditions. The browser awaits the HTTP response which contains the print result directly.

### Subject-to-Subtopic Mapping

For backward compatibility with existing SSE client contracts, NATS subjects are mapped to legacy "subtopic" strings:

```python
SUBTOPIC_TO_SUBJECT = {
    "global-notification":    "progress.notification.global",
    "inventory-notification": "progress.notification.inventory",
    "serial-notification":    "progress.notification.serial",
    "task-notification":      "progress.notification.task",
}
```

This mapping lives in `backend/api/utils/nats_client.py`.

## Key Files

| File | Purpose |
|------|---------|
| `backend/api/utils/nats_client.py` | NATS connection, publish/subscribe/request helpers, subject mapping |
| `backend/api/managers/notification_manager.py` | Conflated notification publisher (uses NATS) |
| `backend/api/managers/server_event_manager.py` | In-memory SSE queue per worker (fed by NATS callbacks) |
| `backend/api/main.py` | Worker startup: NATS connect + subscribe |
| `backend/api/endpoints/print.py` | Print job endpoint (NATS request/reply) |
| `backend/print-service/main.py` | Print service (NATS subscribe + reply) |
| `webapps/main/src/composables/useSSE.js` | Client-side shared SSE composable |

## Adding a New Event Type

1. Choose a NATS subject following the hierarchy (e.g., `progress.workorder.status_changed`)
2. Add a mapping in `SUBTOPIC_TO_SUBJECT` if browser SSE delivery is needed
3. Publish from the relevant manager/event handler using `nats_client.publish()`
4. The existing NATS subscription (`progress.notification.>`) will automatically pick up new `progress.notification.*` subjects
5. For subjects outside `progress.notification.*`, add explicit subscriptions in `main.py` startup

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
