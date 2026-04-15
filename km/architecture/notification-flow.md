# Notification Flow — Deep-Dive

> Parent: [Messaging Architecture](./messaging.md)

This document traces a notification from the moment a domain event commits to the browser receiving a real-time update.

## End-to-End Diagram

```
 DOMAIN EVENT                                                          BROWSER
 (BaseEvent.save)                                                     (Vue component)
       │                                                                  ▲
       │ commit → publish_sync(subject, payload)                          │ EventSource
       ▼                                                                  │
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────────┐
│ NATS publish     │───>│ NATS fan-out     │───>│ ServerEventManager   │
│ (auto from       │    │ to ALL workers   │    │ .enqueue() per-topic │
│  BaseEvent.save) │    │                  │    │ per-session Queue    │
└──────────────────┘    └──────────────────┘    └───────┬──────────────┘
                                                        │
                                                        ▼
                                                 ┌──────────────┐
                                                 │ SSE endpoint  │
                                                 │ GET /notif/   │
                                                 │ {topic}       │
                                                 └──────────────┘
```

## Stage 1: Auto-Publish from BaseEvent

Events are automatically published to NATS after a successful transaction commit. This is handled centrally in `BaseEvent.save()` — individual event classes do **not** need to implement notification logic.

### How it works

1. Each domain base class declares `_notification_subtopic` (e.g. `"production"`). `BaseEvent` defaults to `None` (no publish).
2. `BaseEvent.save()` calls `_build_event_payload()` **before** commit (while the transaction is still active, so derived fields can read from the DB).
3. The payload is collected in `tx._pending_events` (a list stashed on the transaction object, shared across parent and child events).
4. After `commit_transaction()`, the transaction owner calls `_publish_collected_events()` which publishes all collected payloads to NATS via `publish_sync()`.

### Payload structure

The auto-published payload is the full `InfoModel` dump of the event, enriched with:

- `subtopic` — the SSE routing key (e.g. `"production"`)
- `notification` — backward-compatible alias for `event_type` (e.g. `"JOB_CLOSED"`)

This is a superset of the old minimal notification dict. It includes all entity keys (`work_order_key`, `job_key`, `serial_key`, etc.) that the frontend uses for filtering.

`BaseProductionEvent` further enriches its payload with `wo_data` — a snapshot of the affected `WorkOrder` document read from the transaction after all mutations are applied (including `update_work_order()`). This allows the client to patch its local state directly without an extra API call.

### Producers

| Base class | `_notification_subtopic` | Entity keys in InfoModel |
|---|---|---|
| `BaseProductionEvent` | `production` | `work_order_key`, `job_key`, `phase_key` |
| `BaseTaskEvent` | `task` | `task_key` |
| `BaseMessageEvent` | `message` | `message_key` + derived `recipient_id` |
| `BaseInventoryEvent` | `inventory` | `movement_key`, `product_key` |
| `BaseSerialEvent` | `serial` | `serial_key`, `product_key` |
| `BaseIssueEvent` | `issue` | derived `work_order_key` (from `issue_rel` edges or `linked_to`) |

Standalone events that inherit `BaseEvent` directly (e.g. `WorkOrderCreatedEvent`, `QueueUpdatedEvent`, `BatchReleasedEvent`, `JobClosedEvent`) declare their own `_notification_subtopic = "production"`.

### Special case: BaseProductionEvent

`BaseProductionEvent` overrides `_build_event_payload()` to add `wo_data` — the full `WorkOrder` document read from the transaction after `apply()` and `post_processing()` have run. This is used by `ProductionOverview` to patch the affected WO in `wo_map` without a follow-up API call.

`wo_data` does **not** include `issue_count` (which only changes from issue events, not production events) or `qt_remaining` (derived client-side as `qt_planned - qt_completed`). The client preserves both from its existing local state when merging.

### Special case: BaseMessageEvent

`BaseMessageEvent` overrides `_build_event_payload()` to add `recipient_id` — a derived field computed from `self.info.recipient` or the message document. This override runs while the transaction is active.

### Special case: BaseIssueEvent

`BaseIssueEvent` overrides both `pre_processing()` and `_build_event_payload()` to attach `work_order_key` to every issue notification:

- **Create**: `work_order_key` is extracted from the `linked_to` array in `issue_data` (the WO link hasn't been persisted yet when `pre_processing()` runs).
- **Update / Close / Reopen / Delete**: `pre_processing()` queries `issue_rel` edges while the transaction is still active (before `apply()` removes them on delete) and stores the key in `self._issue_wo_key`.

This allows `WorkSessionScreen` (and any other subscriber) to filter issue events by work order without an extra API call.

### Special case: Inventory/Serial error notifications

Error notifications (e.g. serial code already present, movement exception) fire via `notify_error()` using `publish_sync()` directly. These bypass the auto-publish mechanism because:

- They are called from `apply()` before a `raise`, meaning the transaction will abort
- No commit follows, so the auto-publish never fires
- The error must reach the client immediately for user feedback

Success notifications for inventory/serial events are handled by the standard auto-publish after commit.

### Transaction ownership

- **Single event** (`_owns_transaction=True`): creates the transaction, collects its own payload, publishes after commit.
- **Child event** (`_owns_transaction=False`): appends its payload to the shared `tx._pending_events` list. The parent publishes all collected events.
- **`spawn_multiple()`**: creates a transaction, all spawned events append payloads, publishes after commit.

## Stage 2: NATS Publish and Fan-Out

`publish_sync()` maps the subtopic to a NATS subject via `subtopic_to_subject()` and schedules the publish on the asyncio event loop using `asyncio.run_coroutine_threadsafe()` (since `save()` runs in synchronous code).

```
subtopic string   →  NATS subject
production        →  progress.notification.production
task              →  progress.notification.task
message           →  progress.notification.message
inventory         →  progress.notification.inventory
serial            →  progress.notification.serial
issue             →  progress.notification.issue
```

NATS fans the message out to all subscribers on `progress.notification.>`.

## Stage 3: ServerEventManager (per-worker)

**File:** `backend/api/managers/server_event_manager.py`

A per-worker singleton that bridges NATS messages to SSE clients. Set up in `main.py`:

```python
async def on_notification(msg):
    data = msg.data.decode()
    ServerEventManager.getInstance().enqueue(data)

await nats_client.subscribe("progress.notification.>", cb=on_notification)
```

### Dispatch logic in `enqueue(message)`

1. Parse `subtopic` from the JSON message
2. **Exact-topic delivery**: push to all sessions subscribed to that exact subtopic
3. **Wildcard fan-out**: if the subtopic contains `:`, also deliver to sessions subscribed to `{prefix}:*`

### SSE generator: `push_events(request, topic)`

1. Poll the per-session queue with a **1-second timeout**
2. On message → yield a `ServerSentEvent(raw_data=event, event=topic)`
3. On timeout → yield heartbeat comment (keeps connection alive)
4. On disconnect → unregister the session queue

## Stage 4: SSE Endpoint

**File:** `backend/api/endpoints/notification.py`

```python
@router.get("/notification/{topic}", response_class=EventSourceResponse)
async def message_stream(request: Request, topic: str):
    async for event in ServerEventManager.getInstance().push_events(request, topic):
        yield event
```

## Stage 5: Frontend — `useSSE` Composable

**Files:** `webapps/main/src/composables/useSSE.js`, `webapps/warehouse/src/composables/useSSE.js` (same pattern; warehouse build uses its own copy wired to `@/boot/axios`).

Manages shared `EventSource` connections (one per topic, ref-counted). Components subscribe with callbacks and filter by entity key or event type.

**Warehouse operator app — movement lists:** `IncomingRoot` and `ShipmentRoot` subscribe to topic `inventory` via `useWarehouseMovementListEvents()` and refetch open list headers on `WAREHOUSE_LIST_CREATED` / `WAREHOUSE_LIST_CLOSED` (aligned with main `MovementListsRoot.vue`), using `lists.refreshHeaders()` so in-progress line items are not cleared by a full store reset.

### Frontend consumption patterns

**Entity-filtered components** (e.g. `WorkOrderScreen`, `TaskScreen`):
```javascript
handleMessage(message) {
    let event = JSON.parse(message.data);
    if (event.work_order_key === this.wo_key) {
        this.reload();
    }
}
```

**Payload-enriched patch** (e.g. `ProductionOverview`):

Rather than reacting to event type and re-fetching, views that display WO list data commit a targeted Vuex mutation directly from the event payload:
```javascript
handleMessage(message) {
    let event = JSON.parse(message.data);
    const type = event.event_type || event.notification;

    if (type === 'QUEUE_UPDATED') {
        // Queue order/membership changed — full reload required
        this.$store.dispatch('loadWorkOrders');
        this.$store.dispatch('loadJobAssignments');
        return;
    }

    if (event.wo_data) {
        // Patch the affected WO in-place — no API call
        this.$store.commit('UPDATE_SINGLE_WO', event.wo_data);
        this.debouncedLoadAssignments(); // trailing 5s debounce
    }
}
```

`wo_data` is attached to every `BaseProductionEvent` payload. The `UPDATE_SINGLE_WO` mutation preserves `sequence` and `issue_count` from local state and recomputes `qt_remaining`.

**Error-aware views** (e.g. warehouse roots, `TraceabilityRoot`):
```javascript
handleMessage(message) {
    let event = JSON.parse(message.data);
    if (event.notification === 'ERROR') {
        showErrorToast(event.error_code, event.error);
        return;
    }
    // type-filtered reload
}
```

## Key Files

| File | Role in the flow |
|---|---|
| `events/base_event.py` | Auto-publish logic (`_build_event_payload`, `_publish_collected_events`) |
| `events/**/base_*.py` | `_notification_subtopic` declarations |
| `utils/nats_client.py` | NATS connection, `publish_sync()`, subject mapping |
| `managers/server_event_manager.py` | Per-worker SSE queue dispatch |
| `main.py` | Worker startup (NATS connect + subscribe + callback) |
| `endpoints/notification.py` | SSE HTTP endpoint |
| `composables/useSSE.js` | Client-side shared EventSource |
