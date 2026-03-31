# Event Sourcing Architecture

## Overview

The Progress Platform uses an **immutable event-sourcing pattern** for all core business logic. Instead of mutating state directly in the database (CRUD), we append **Events** to an append-only log. State is derived from these events.

**Key Benefits:**
- **Auditability**: Complete history of "who did what and when".
- **Traceability**: Critical for manufacturing compliance.
- **Decoupling**: Events trigger side effects (notifications, emails) asynchronously via NATS.

## Core Components

### 1. Base Event (`backend/api/events/base_event.py`)
All events inherit from `BaseEvent`.

```python
class BaseEvent(ABC):
    def get_event_type(self) -> str:
        """Returns the string type identifier for the event."""
        pass

    def apply(self, db, ...) -> None:
        """
        Executes the business logic within a transaction.
        MUST be idempotent.
        """
        pass
```

### 2. Event Execution Flow

1.  **API Endpoint**: Receives request (e.g., `POST /work-order/{id}/start`).
2.  **Event Instantiation**: Endpoint creates an Event object (e.g., `JobStarted(job_id=...)`).
3.  **Application**: The event's `apply()` method is called inside an ArangoDB transaction.
    - Updates the document state (e.g., set `status='RUNNING'`).
    - Creates the `Event` document in the `Events` collection.
4.  **NATS Projection (Select Events)**:
    - **Notifications**: The `NotificationManager` publishes updates to NATS subjects under `progress.notification.*` (triggered via middleware or managers). See `km/architecture/messaging.md` for the full subject hierarchy.
    - **Domain Events**: Specific events (e.g., Serial events) explicitly publish data to NATS subjects (e.g., `progress.serial.events`) for downstream integration.
    - *Note: Not all events are automatically streamed to NATS yet; this is implemented on a per-domain basis.*

## Rules for Developers

1.  **Never update state directly** in API endpoints. Always create an Event.
2.  **Events are immutable**. Once written, they cannot be changed.
3.  **Apply logic must be transactional**. All DB changes in `apply()` must succeed or fail together.
4.  **Side effects go to Managers**, not `apply()`. Don't send emails in `apply()`; use the NotificationManager which listens to the event stream.
