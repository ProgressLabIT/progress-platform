# Event Sourcing Architecture

## Overview

The Progress Platform uses an **immutable event-sourcing pattern** for all core business logic. Instead of mutating state directly in the database (CRUD), API endpoints construct **Event objects** that own the mutation. State is derived by applying events inside an ArangoDB transaction; the event itself is appended to the `Event` collection for audit + replay.

**Key Benefits:**
- **Auditability**: Complete history of "who did what and when" in the `Event` collection.
- **Traceability**: Critical for manufacturing compliance.
- **Decoupling**: Each event's NATS publish drives downstream consumers (SSE refresh, notification fan-out, integration sinks) without endpoints knowing the consumers.
- **Cascading**: Parent events spawn child events sharing the same transaction, atomically.

## Core Components

### `BaseEvent` — `backend/api/events/base_event.py`

All events inherit (directly or indirectly) from `BaseEvent`. Subclasses define:

| Method / Attribute | Purpose |
|---|---|
| `class InfoModel(EventInfoModel)` | Pydantic v2 schema for the event payload (validated at construction). |
| `@classmethod get_event_type()` | Returns the `EventType` enum value identifying this event in storage and dispatch. |
| `@classmethod get_tx_collections()` | Returns the list of ArangoDB collections this event's `apply()` writes to. The framework auto-adds `Event` and `event_source`. |
| `def apply(self)` | The business logic. Mutates state via `self.tx.collection(...)` operations and may spawn child events. Sets `self.response` if the endpoint needs a return value. |
| `def pre_processing(self)` *(optional)* | Hook to validate invariants and reject the event before `apply()` runs. Raise `ValueError` for domain rejections — the endpoint maps to 422. |
| `_notification_subtopic` *(class attr)* | Sub-topic appended to `progress.notification.<topic>` (e.g. `production`). Drives SSE routing. |

### Lifecycle of a `save()` call (`base_event.py`)

1. **Construct**: `event = MyEvent(info=dict(...))` — Pydantic validates `info` against `InfoModel`. `_owns_transaction = (tx is None)`.
2. **`event.save()`** opens a transaction (if it owns one) with `get_tx_collections() + ['Event', 'event_source']`.
3. **`pre_processing()`** runs (if defined). Raise `ValueError` here for invariant rejection.
4. **`apply()`** runs inside the tx. Mutates state. May call `OtherEvent.create_as_child(self, ...)`.
5. **`store_event()`** writes the `Event` document + `event_source` link.
6. **NATS payload built** via `_build_event_payload()` and appended to `tx._pending_events`.
7. **Commit** (only if `_owns_transaction`). After commit, `_publish_collected_events(tx)` publishes all pending NATS messages in one wave.

If `pre_processing()` or `apply()` raises, the tx is aborted (only if owned). No partial commit, no NATS publish.

## Event Patterns

### 1. Endpoint-as-thin-wrapper (canonical)

The endpoint exists for backward compatibility and shape preservation. All mutation logic lives in the event class.

```python
@router.patch('/work-order/{wo_key}', ...)
async def update_work_order(wo_key: str, new_due_date: ... = Body(None), ...):
    try:
        event = WorkOrderUpdatedEvent(info=dict(
            event_type=EventType.WORK_ORDER_UPDATED,
            work_order_key=wo_key,
            new_due_date=new_due_date,
            # ...
            primary=True,
        ))
        event.save()
        return APIResponse(detail=event.response)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=dict(
            error_type=e.__class__.__name__,
            message=e.args[0] if e.args else None,
        ))
    except Exception:
        raise HTTPError(500, "There was a problem updating the work order")
```

**Error mapping convention** (mirror `backend/api/endpoints/traceability.py:64-109`):
- `ValueError` and domain exceptions → **422**.
- Anything else → **500**.

**Files demonstrating the pattern:**
- `backend/api/endpoints/production.py` → `update_work_order` (PATCH `/work-order/{key}`) → `WorkOrderUpdatedEvent`.
- `backend/api/endpoints/traceability.py:64-109` → the original reference template.

### 2. Parent-child events — `Event.create_as_child(parent, payload)`

When a parent event's `apply()` triggers further domain mutations that deserve their own audit row + NATS publish, spawn a **child event** sharing the parent's transaction and `event_group`.

```python
def apply(self):
    # ... do parent's own work ...
    if some_condition:
        WorkOrderClosedEvent.create_as_child(self, dict(
            work_order_key=self.info.work_order_key,
        ))
```

Behind the scenes (`base_event.py:62`): `create_as_child` sets `info['primary'] = False`, passes `tx=self.tx`, and reuses `self.info.event_group`. The child runs its own `apply()` inside the parent tx; its `Event` row links via `event_group`; its NATS payload joins `tx._pending_events` and publishes after the parent commits.

**Constraint** (`base_event.py:146-147`): secondary events MUST have both `tx` and `event_group`. `create_as_child` ensures both.

**Files demonstrating the pattern:**
- `backend/api/events/production/base_production.py:79-99` — `BaseProductionEvent` post-processing spawns `WorkOrderStartedEvent` / `WorkOrderClosedEvent` as children when the parent event flips WO status.

### 3. Batch primary events — `BaseEvent.spawn_multiple(shared_data, event_data, tx=None)`

When one HTTP call must fire N primary events of the **same type** atomically (e.g. bulk job updates touching multiple work orders), use `spawn_multiple` (`base_event.py:76`).

```python
shared_data = EventSharedData(
    event_type=EventType.WORK_ORDER_UPDATED,
    # user_key, user_session_key, timestamp, event_group filled by spawn_multiple
)
event_data = [
    {"work_order_key": wo_key, "job_updates": updates}
    for wo_key, updates in by_wo.items()
]
BaseEvent.spawn_multiple(shared_data=shared_data, event_data=event_data)
```

**Guarantees:**
- **ONE tx** across all N events. Either all commit or all roll back.
- **ONE `event_group`** (auto-generated if not provided) → one HTTP call = one audit group, queryable as a unit.
- **ONE NATS publish wave** at the end (`base_event.py:130`).
- All events must share `event_type` (constraint at `base_event.py:87`).
- If `tx` is provided externally, events are spawned as secondary (`primary=False`); if `tx=None`, spawn_multiple opens its own tx and events are primary.

**Files demonstrating the pattern:**
- `backend/api/endpoints/traceability.py:112-156` — `POST /event/bulk` accepts client-supplied `shared_data` + `events` and dispatches via `spawn_multiple`.

### 4. Notification-only events (empty `apply()`)

Some events exist purely to drive downstream consumers (SSE, notification fan-out) without mutating state. Their `apply()` is `pass` and `get_tx_collections()` is `[]`. They're typically spawned as children of a parent event that performed the actual mutation.

```python
class WorkOrderStartedEvent(BaseEvent):
    _notification_subtopic = "production"

    class InfoModel(EventInfoModel):
        work_order_key: str

    @classmethod
    def get_event_type(cls):
        return EventType.WORK_ORDER_STARTED

    @classmethod
    def get_tx_collections(cls):
        return []

    def apply(self):
        pass
```

**Files demonstrating the pattern:**
- `backend/api/events/production/work_order_events.py` — `WorkOrderStartedEvent`, `WorkOrderClosedEvent`, `WorkOrderCreatedEvent`.

### 5. External transaction sharing — `tx=...` argument

`BaseEvent.__init__` accepts an optional `tx`. When provided, the event uses the caller's transaction (`_owns_transaction = False`) and won't commit on its own — the caller commits when ready. This is the mechanism behind `create_as_child` and `spawn_multiple`, and can be used directly when a custom orchestrator needs to coordinate multiple events under one tx.

The shared transaction carries `tx._pending_events` (`base_event.py:247`) — every event saved into the same tx appends its NATS payload here, and only the tx owner publishes after commit.

## NATS Payload Enrichment — `_build_event_payload()`

`BaseEvent._build_event_payload()` (`base_event.py:171`) returns the NATS message body. Subclasses can override to enrich the payload before publish.

`BaseProductionEvent._build_event_payload()` (`backend/api/events/production/base_production.py:102-133`) overrides this to fetch the latest `Job` doc + parent `WorkOrder` doc via AQL and merge them into the payload under `job_data`. This means **any production event with `job_key` in its InfoModel automatically broadcasts the updated job state over SSE**, without endpoint or apply() code having to construct it.

**Frontend contract:** `webapps/main/src/components/JobList.vue:826-832` subscribes to the `production` SSE topic and, on receiving any event with `event.job_data`, commits `UPDATE_SINGLE_JOB` to the Vuex store. Any production event firing with `job_key` set will trigger a single-job state refresh in the UI for free.

## Event Grouping for Audit — `event_group`

Every event carries an `event_group: str` (UUID). Primary events without a group get one auto-generated (`spawn_multiple` and `__init__`). Child events inherit the parent's group via `create_as_child`. Sibling primary events in a `spawn_multiple` call share one group.

**Audit query pattern:**
- "What happened to WO X?" → `Event.find({work_order_key: 'X'})`.
- "What happened from one HTTP call?" → `Event.find({event_group: '<uuid>'})`.
- "What were the side effects of this primary event?" → `Event.find({event_group: <parent>.event_group, primary: false})`.

## NATS Subject Routing

Notification publishes go to `progress.notification.<subtopic>` where `<subtopic>` = `cls._notification_subtopic` (e.g. `production`, `inventory`, `traceability`). Frontend SSE handlers subscribe per subtopic via the `useSSE(topic)` composable (`webapps/main/src/composables/useSSE.js`). See `km/architecture/messaging.md` for the full subject hierarchy and `km/architecture/notification-flow.md` for the end-to-end SSE wiring.

## Rules for Developers

1. **Never update state directly in API endpoints.** Always create an Event and call `.save()`. The endpoint is a thin wrapper.
2. **Events are immutable** once saved. To "correct" an event, append a compensating event.
3. **`apply()` must be transactional.** All mutations within `apply()` go through `self.tx.collection(...)`. The framework commits or rolls back atomically.
4. **Side effects (emails, slack, integrations) go through Managers**, not `apply()`. Managers subscribe to NATS and react to events asynchronously.
5. **Domain rejections raise `ValueError` in `pre_processing()` or `apply()`.** The endpoint maps to 422. Generic exceptions map to 500.
6. **Use the right cascade primitive:**
   - One primary event from one HTTP call → just construct + `.save()`.
   - Mutation triggers further domain mutations → spawn children via `create_as_child`.
   - One HTTP call must fire N primary events atomically → `spawn_multiple`.
7. **Notification-only events** (empty `apply()`, empty `get_tx_collections()`) are fine for pure SSE fan-out from a parent.
8. **For production-domain events**, inherit from `BaseProductionEvent` to get automatic `job_data` enrichment in the SSE payload + WO status cascade.

## File Map

| File | Role |
|---|---|
| `backend/api/events/base_event.py` | `BaseEvent` + `spawn_multiple` + tx semantics + NATS publish. |
| `backend/api/events/production/base_production.py` | `BaseProductionEvent` — WO status recompute, `job_data` payload enrichment, cascade to `WorkOrderStarted/Closed` children. |
| `backend/api/events/production/work_order_events.py` | Per-WO event classes (`WorkOrderUpdatedEvent`, notification-only shells). |
| `backend/api/events/admin/extra_update_requested.py` | Structural template for an event with class-typed InfoModel + cross-collection apply(). |
| `backend/api/endpoints/traceability.py:112-156` | `/event/bulk` — canonical `spawn_multiple` consumer. |
| `backend/api/models/event.py` | `EventType` enum, `EventInfoModel`, `EventSharedData`. |
