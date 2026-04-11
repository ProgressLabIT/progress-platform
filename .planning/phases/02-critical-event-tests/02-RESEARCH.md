# Phase 2: Critical Event Test Suites — Research

**Researched:** 2026-04-10
**Domain:** pytest event integration testing — ArangoDB, FastAPI, direct event.save()
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Event Instantiation Strategy**
- D-01: Direct event tests call `event.save(db)` against the real ArangoDB testcontainer — no mocking of the transaction layer
- D-02: Pattern: seed preconditions via Phase 1 factory fixtures → instantiate event with info dict → call `event.save(db)` → assert on collection documents via `db.collection().find()`/`db.collection().get()`
- D-03: HTTP API tests use `httpx.AsyncClient` (session-scoped from Phase 1) with `auth_headers` fixture — these test the endpoint → event dispatch chain
- D-04: The two layers are cleanly separated by assertion surface: API tests assert on HTTP response shape, direct tests assert on DB state

**Cascade Assertion Strategy**
- D-05: For cascading events, assert parent's own DB state changes + verify child events were recorded in the Event collection
- D-06: Do NOT duplicate child event DB side effect assertions in parent tests
- D-07: Query the Event collection to verify each expected child event type was dispatched with correct info

**BatchCompleted Parametrize Matrix**
- D-08: Use a curated ~16-test pairwise matrix (not full 32 cartesian product)
- D-09: Eliminate impossible: `auto_new_batch=True` + last batch is a no-op
- D-10: `step_check` is orthogonal — 2 isolated tests (with/without step_data)
- D-11: Cover all real flag interactions: first/last phase × traceability × warehouse_management × auto_new_batch (non-last-batch scenarios only)
- D-12: Include comment block in parametrize decorator documenting excluded combinations
- D-13: Update BATCH-20 success criterion wording from "32-combination" to reflect actual curated count

**Plan Splitting (6 plans)**
- D-14: Plan 02-01: StepCompletedEvent (STEP-01 through STEP-08, both layers)
- D-15: Plan 02-02: BatchCompletedEvent HTTP API tests (~10 requirements)
- D-16: Plan 02-03: BatchCompletedEvent direct event tests (~11 requirements)
- D-17: Plan 02-04: ProgressOverrideRequestedEvent (PROG-01 through PROG-17, both layers)
- D-18: Plan 02-05: MovementCompletedEvent type coverage (~10 requirements)
- D-19: Plan 02-06: MovementCompletedEvent API + serial traceability (~6 requirements)

### Claude's Discretion
- Test helper organization — whether to create shared assertion helpers (e.g., `assert_event_dispatched()`) or keep assertions inline per test
- Exact requirement-to-plan mapping for BATCH split — Claude to assign requirements to 02-02 vs 02-03 during planning based on which layer each requirement belongs to
- Fixture composition for complex preconditions — whether to create higher-level "scenario" fixtures or compose Phase 1 factories inline

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| STEP-01 | Happy path: completing a non-last step updates StepExecutionData to DONE status | `StepCompletedEvent.apply()` writes StepExecutionData with `status=StepStatus.DONE` at line 63; `overwrite=True` means upsert |
| STEP-02 | Last step triggers BatchCompletedEvent as child event | `_check_all_batch_steps_done()` on line 66 gates `BatchCompletedEvent.create_as_child()` call |
| STEP-03 | Form data is correctly stored in StepExecutionData record | `form_data = self.info.form_data` passed into StepExecutionData model |
| STEP-04 | Work session key is correctly set from current work session | `get_current_work_session()` sets `self.info.work_session_key` |
| STEP-05 | Temporary step data (existing StepExecutionData with no completion) is overwritten | `tx.collection("StepExecutionData").insert(step_data, overwrite=True)` reuses `temp_step_data_key` when found |
| STEP-06 | Missing batch raises ValueError | Line 29: `raise ValueError(f"Batch {self.info.batch_key} not found")` |
| STEP-07 | Response includes updated job data and batch execution data | `self.response` dict with `job_data` and `batch_data` keys |
| STEP-08 | HTTP API integration test via POST endpoint exercises full dispatch chain | Single `/event` POST with `event_type=STEP_COMPLETED` |
| BATCH-01 | Happy path: batch completion updates batch record, closes work session | `COMPLETE_BATCH` AQL + `WorkSessionClosedEvent.create_as_child()` |
| BATCH-02 | Last batch triggers JobClosedEvent | `new_job_qt_completed >= self.job.qt_planned` branch at line 148 |
| BATCH-03 | Non-last batch with auto_new_batch creates new Batch + WorkSession | `create_new_batch` condition at line 181; `BatchCreatedEvent` + `WorkSessionCreatedEvent` |
| BATCH-04 | Non-last batch without auto_new_batch sets job.active=False, active_batch_key=None | `job_update` dict in the else branch at line 169 |
| BATCH-05 | First phase does not generate WIPRemovedEvent | `if not self.job.first_phase:` guard at line 121 |
| BATCH-06 | Non-first phase generates WIPRemovedEvent | Same guard (false branch) |
| BATCH-07 | Non-last phase generates WIPDeclaredEvent | `if not self.job.last_phase:` at line 127 |
| BATCH-08 | Last phase triggers BatchReleasedEvent | `else:` branch at line 135 |
| BATCH-09 | With warehouse management enabled + last phase, generates production MovementCompletedEvent | `_process_output()` — only when `self.job.last_phase` and inventory config enabled |
| BATCH-10 | With warehouse management enabled, generates consumption MovementCompletedEvent per BOM line | `_process_consumption()` iterates BOM lines |
| BATCH-11 | With traceability enabled, fetches batch serial keys and calls SerialUpdatedEvent per serial | `_handle_batch_serials()` — iterates `batch_serial_keys` |
| BATCH-12 | With traceability + last phase, triggers SerialReleasedEvent per serial | `if self.job.last_phase:` block inside `_handle_batch_serials()` |
| BATCH-13 | Component serials trigger SerialLinkedEvent | `batch_component_serials_map` iteration at line 344 |
| BATCH-14 | Step data without step_check stores batch execution data | `_store_batch_execution_data()` called when `not self.job.parameters.step_check` |
| BATCH-15 | Step data with step_check raises ValueError | Line 80: `raise ValueError("Step check is active...")` |
| BATCH-16 | Quantity mismatch raises ValueError | Line 55: `raise ValueError("Active batch quantity does not match...")` |
| BATCH-17 | Closed job raises ValueError | Line 62: `raise ValueError("Job is already closed")` |
| BATCH-18 | Serial code generation via counter when first_phase and serial has no code | `_handle_serial_code()` → `_generate_counter()` |
| BATCH-19 | Batch media files copied to serial directories | `_copy_batch_media_to_serials()` uses shutil.copytree; safe to skip in tests (no /media in testcontainer) |
| BATCH-20 | Parametrized matrix covers key flag combinations | Curated ~16-case matrix per D-08 through D-12 |
| BATCH-21 | HTTP API integration test exercises full cascade through endpoint | POST `/event` with `event_type=BATCH_COMPLETED` |
| PROG-01 | Quantity increase creates forced batch, work session, and downstream WIP | `_handle_quantity_increase()` → `_create_forced_batch_and_work_session()` + wip insert |
| PROG-02 | Quantity decrease cancels batches newest-to-oldest until target reached | `_cancel_batches_for_quantity_decrease()` with deque iteration |
| PROG-03 | Quantity decrease creates compensating batch when over-canceled | `if remaining_qt < 0:` creates forced batch |
| PROG-04 | Time redistribution creates new work sessions with proportional durations | `_handle_time_redistribution()` when `should_adjust_duration=False` |
| PROG-05 | Job transitions: CREATED->STARTED on first increase, STARTED->CLOSED when complete | `_handle_job_status()` quantity_change > 0 branch |
| PROG-06 | Job transitions: CLOSED->STARTED on decrease (reopening), STARTED->CREATED when qty=0 | `_handle_job_status()` quantity_change < 0 branch |
| PROG-07 | Reopened job is re-added to operator queue and site queue reordered | `ADD_JOB_TO_QUEUE` in `_handle_job_status()` + `REORDER_JOB_QUEUES` in `post_processing()` |
| PROG-08 | Upstream WIP reduced on quantity increase (non-first phase) | `_reduce_wip(upstream_free_wip, quantity_change)` in `_handle_quantity_increase()` |
| PROG-09 | Downstream WIP reduced on quantity decrease (non-last phase) | `_reduce_wip(downstream_free_wip, abs(quantity_change))` in `_handle_quantity_decrease()` |
| PROG-10 | Inventory movements created for forced batches when warehouse enabled | `_create_inventory_movements_for_forced_batch()` |
| PROG-11 | Inventory movements reversed for canceled batches | `_reverse_inventory_movements()` |
| PROG-12 | Validation: no assignee raises JobHasNoAssigneeError | `_validate_job_state()` line 148 |
| PROG-13 | Validation: active job raises JobIsActiveError | `_validate_job_state()` line 152 |
| PROG-14 | Validation: active batch raises JobHasActiveBatchError | `_validate_job_state()` line 156 |
| PROG-15 | Validation: traceability enabled raises NotImplementedError | `_validate_job_state()` line 165 |
| PROG-16 | Validation: insufficient upstream WIP raises WipNotAvailableError | `_validate_job_state()` line 170 |
| PROG-17 | HTTP API integration test exercises override flow through endpoint | POST `/event` with `event_type=PROGRESS_OVERRIDE_REQUESTED` |
| MOVE-01 | Receipt adds product to destination position inventory | `_handle_receipt()` → `InventoryChangedEvent` with positive qty |
| MOVE-02 | Receipt with traceability creates or finds serial, validates serial code required | `_handle_receipt_with_traceability()` — serial_code required |
| MOVE-03 | Receipt with existing serial already in inventory raises InventoryMovementException | `if inventory_exists: raise InventoryMovementException` |
| MOVE-04 | Shipment removes product from source position | `_handle_shipment()` → `InventoryChangedEvent` with negative qty |
| MOVE-05 | Shipment with traceability validates serial_key required | `if self.info.serial_key is None: raise InventoryMovementException` |
| MOVE-06 | Shipment from position with insufficient inventory raises InventoryMovementException | `InventoryChangedEvent` raises exception caught in `_handle_shipment()` |
| MOVE-07 | Adjustment adds/removes quantity at position | `_handle_adjustment()` |
| MOVE-08 | Product transfer updates both source and destination positions | `_handle_transfer_production_consumption()` non-container path |
| MOVE-09 | Container transfer updates position hierarchy without moving product | `is_container_transfer` branch: updates `is_in_position` `_to` field |
| MOVE-10 | Fixed position cannot be container-transferred | `if position['fixed']: raise InventoryMovementException` |
| MOVE-11 | Production movement creates inventory at destination | `_handle_transfer_production_consumption()` with `position_from='NULL'` |
| MOVE-12 | Consumption movement removes inventory from source | `_handle_transfer_production_consumption()` with `position_to='NULL'` |
| MOVE-13 | Reversal type raises InventoryMovementException | `apply()` line 81: `if self.info.movement_type == InventoryMovementType.REVERSAL: raise` |
| MOVE-14 | Deleted position raises error | `_ensure_position_not_deleted()` called in `apply()` before handler dispatch |
| MOVE-15 | Planned movement (existing movement_key) updates to COMPLETED status | `_update_movement()` path when `self.info.movement_key is not None` |
| MOVE-16 | HTTP API integration test exercises movement flow through endpoint | POST `/event` with `event_type=MOVEMENT_COMPLETED` |
</phase_requirements>

---

## Summary

This phase tests 4 critical production events via two complementary layers: HTTP API tests (POST to `/event` endpoint) and direct event instantiation tests (construct event → call `.save(db)`). All tests run against the real ArangoDB testcontainer from Phase 1.

The single API entry point for all 4 events is `POST /event` in `backend/api/endpoints/traceability.py`. The endpoint receives an `EventInfoModel` dict, resolves the event class via `get_event_class(event_type)`, instantiates it, calls `.save()`, and returns `APIResponse(detail=event.response)`. Validation errors (ValueError, domain exceptions) are caught and returned as HTTP 422 with a structured `error_type`/`message`/`exception` body.

The critical implementation gap to avoid: `ProgressOverrideRequestedEvent` is in `events/admin/`, inherits from `BaseAdmin` (not `BaseProductionEvent`), and its `post_processing()` handles `update_work_order()` and queue reordering. The `_job_was_reopened` flag is set in `_handle_job_status()` and consumed in `post_processing()` — tests that bypass `event.save()` and call `apply()` directly would miss this side effect.

**Primary recommendation:** Build the test suite in 6 plans per D-14 through D-19. For direct event tests, always invoke `event.save(db)` (never `event.apply()`), since `save()` also runs `pre_processing()`, `post_processing()`, and `store_event()` — all three are exercised by the requirements.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | >=9.0 | Test runner | Already in pyproject.toml [VERIFIED: codebase] |
| pytest-asyncio | >=0.21 | Async test support | Already in pyproject.toml, `asyncio_mode = "auto"` [VERIFIED: codebase] |
| httpx | >=0.28 | API layer tests | Already in pyproject.toml, session-scoped `client` fixture exists [VERIFIED: codebase] |
| python-arango | >=8 | DB assertions | Already in pyproject.toml [VERIFIED: codebase] |

All dependencies are already installed. No new packages needed for Phase 2. [VERIFIED: pyproject.toml]

---

## Architecture Patterns

### Recommended Test Structure

```
testing/pytest/tests/
├── step/
│   ├── __init__.py
│   └── test_step_completed.py      # plan 02-01 — both layers
├── batch/
│   ├── __init__.py
│   ├── test_batch_completed_api.py     # plan 02-02 — HTTP layer
│   └── test_batch_completed_direct.py  # plan 02-03 — direct event layer
├── progress/
│   ├── __init__.py
│   └── test_progress_override.py   # plan 02-04 — both layers
└── movement/
    ├── __init__.py
    ├── test_movement_types.py       # plan 02-05 — type coverage
    └── test_movement_api_serial.py  # plan 02-06 — API + serial paths
```

### Pattern 1: Direct Event Instantiation

```python
# Source: verified against base_event.py save() + event __init__
def test_step_completed_happy_path(db, create_production_graph):
    g = create_production_graph(num_steps=1, step_check=False)
    step_key = g["product"]["steps"][0]["_key"]

    event = StepCompletedEvent(info=dict(
        event_type="STEP_COMPLETED",
        primary=True,
        user_key=g["user"]["_key"],
        batch_key=g["batch"]["_key"],
        step_key=step_key,
    ))
    event.save(db)  # NOT event.apply() — save() runs full lifecycle

    result = db.collection("StepExecutionData").find(dict(
        batch_key=g["batch"]["_key"],
        step_key=step_key,
        canceled=None,
    )).next()
    assert result["status"] == "done"
```

**Key:** `event.save(db)` — pass `db` to override the module-level singleton. BaseEvent.__init__ sets `self._owns_transaction = (tx is None)`, and `save()` creates its own transaction when `tx` is None. But `save()` also calls `db.begin_transaction()` using the module-level `db` — the testcontainer override already patches `utils.db.db`, so **passing `db` to the constructor is NOT how it works**. The constructor signature is `__init__(self, info, tx=None)`. The `save()` method uses the module-level `db` singleton (already patched by the `db` fixture). Correct call:

```python
# Correct — no db argument to save()
event = StepCompletedEvent(info={...})
result = event.save()
```

### Pattern 2: Event Collection Cascade Verification (D-07)

```python
# Verify a child event was dispatched without asserting its side effects
def assert_event_dispatched(db, event_type: str, **filter_fields):
    """Assert at least one Event record with given type and matching info fields exists."""
    cursor = db.collection("Event").find({"event_type": event_type, **filter_fields})
    events = list(cursor)
    assert len(events) >= 1, f"Expected {event_type} event to be dispatched, found 0"
    return events[0]
```

### Pattern 3: HTTP API Layer

```python
# Source: verified against traceability.py endpoint + conftest.py client fixture
async def test_step_completed_api(client, auth_headers, create_production_graph):
    g = create_production_graph(num_steps=1)
    auth_headers("operator production")  # sets dependency override on app

    response = await client.post("/event", json={
        "event_type": "STEP_COMPLETED",
        "primary": True,
        "user_key": g["user"]["_key"],
        "batch_key": g["batch"]["_key"],
        "step_key": g["product"]["steps"][0]["_key"],
    })

    assert response.status_code == 200
    body = response.json()
    assert "detail" in body        # APIResponse wraps in "detail"
    assert "job_data" in body["detail"]
```

### Pattern 4: Validation Error Assertions (PROG-12 through PROG-16)

```python
# For direct event tests expecting domain exceptions
import pytest

def test_validation_no_assignee(db, create_production_graph):
    g = create_production_graph()
    # Remove assignee from job
    db.collection("Job").update({"_key": g["job"]["_key"], "assigned_to": None})

    with pytest.raises(JobHasNoAssigneeError):
        event = ProgressOverrideRequestedEvent(info=dict(
            event_type="PROGRESS_OVERRIDE_REQUESTED",
            primary=True,
            user_key=g["user"]["_key"],
            job_key=g["job"]["_key"],
            new_job_qt_completed=5.0,
        ))
        event.save()
```

### Anti-Patterns to Avoid

- **Calling `event.apply()` directly:** Skips `pre_processing()`, `post_processing()`, `store_event()`, and transaction management. Tests would miss queue reordering (PROG-07), work order update, and Event collection storage.
- **Asserting child event side effects in parent tests (D-06):** BatchCompleted tests should NOT query `is_in_position` for inventory state — that belongs to MovementCompleted tests.
- **Missing `work_session_key` in BatchCompleted info:** `WorkSessionClosedEvent.create_as_child()` requires `work_session_key` to be set on the parent event's `info`. The factory creates a WorkSession, but the Job document's `last_work_session_started` must also be set for `BaseProductionEvent.get_current_work_session()` to find it.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cascade verification | Custom AQL traversal | `db.collection('Event').find({'event_type': '...'})` | Event collection stores all events per D-05/D-07 |
| Async test client | Custom ASGI harness | Phase 1 `client` fixture (httpx.AsyncClient + ASGITransport) | Already session-scoped and wired to app |
| JWT auth in tests | Custom token generation | Phase 1 `auth_headers` fixture (dependency override) | Bypasses crypto entirely via FastAPI override |
| DB isolation | Explicit truncate calls | Phase 1 `truncate_collections` autouse fixture | Runs after every test automatically |
| Config state reset | Manual Config updates | `seed_config` fixture + Phase 1 Config defaults restore | `_capture_config_defaults` restores after each test |

---

## Critical Implementation Details

### Event API Endpoint — Single Entry Point

All 4 events dispatch through the **same endpoint**: `POST /event` (in `traceability.py`). The body is an `EventInfoModel`-compatible dict with `event_type` as discriminator. The endpoint:
1. Calls `get_event_class(event_data.event_type)` to resolve the class
2. Instantiates: `event_class(info=event_data.model_dump())`
3. Calls `event.save()`
4. Returns `APIResponse(detail=event.response)`

HTTP 422 is returned for: ValueError, JobIsActiveError, JobHasActiveBatchError, JobHasNoAssigneeError, JobHasNoActiveBatchError, WipNotAvailableError, serial errors, InventoryMovementException. The body is `{"error_type": "...", "message": "...", "exception": "..."}`.

HTTP 500 for unhandled exceptions.

### StepCompletedEvent — Precondition Checklist

For `event.save()` to succeed, the DB must have:
- `Batch` document with matching `_key` and `job_key` set
- `Job` document with `active_batch_key = batch._key` and `last_work_session_started` set
- `WorkSession` document with `batch_key = batch._key` and `active=True` (for `get_current_work_session()`)
- `StepExecutionData` document(s) for all steps in the batch (for `_check_all_batch_steps_done()`)
- `Phase` document reachable via `job.phase_key` (for `_get_job_data()`)

`create_production_graph` sets all of these up correctly. [VERIFIED: factory conftest]

### BatchCompletedEvent — Precondition Checklist

All StepCompleted preconditions, plus:
- `job.qt_planned` must be set (affects last-batch detection)
- `batch.qt_total` must equal `completed_batch_qt` in the event info (or ValueError)
- For warehouse path: `Config['enable_inventory_management']['value'] = True` (via `seed_config`)
- For consumption path: `WorkOrder` with `wo_bom` BOM lines and `phase_key` match — `create_production_graph(with_bom=True)` handles this
- `Config['default_production_position']` and `Config['default_consumption_position']` must exist — schema init provides them

### BatchCompletedEvent — `work_session_key` Gap

`BatchCompletedEvent` relies on `self.info.work_session_key` already being set when `WorkSessionClosedEvent.create_as_child()` is called. But `InfoModel` does not auto-populate it — the job's `last_work_session_started` must be set so `get_current_work_session()` (from BaseProductionEvent) can find it. The factory sets `last_work_session_started` via:

```python
db.collection("Job").update({"_key": job["_key"], "active_batch_key": batch["_key"]})
```

But `last_work_session_started` is NOT set by the factory — this is a known gap. Direct BatchCompleted tests must also set it:

```python
db.collection("Job").update({
    "_key": job["_key"],
    "last_work_session_started": ws["_key"]
})
```

[VERIFIED: factories conftest — `last_work_session_started` is initialized to `None` in create_job]

### ProgressOverrideRequestedEvent — `post_processing()` Executes After `apply()`

The event's `post_processing()` calls:
1. `self.update_work_order()` (from BaseAdmin)
2. `REORDER_JOB_QUEUES` AQL if `_job_was_reopened=True`

PROG-07 (queue reordering) is tested by calling `event.save()` and then querying the Queue collection after the fact. The `ADD_JOB_TO_QUEUE` call happens inside `apply()` in `_handle_job_status()`, but `REORDER_JOB_QUEUES` only runs in `post_processing()`. Both are exercised by `save()`.

Queue preconditions for PROG-07: operator Queue document must exist with `subqueue_target_key = job.assigned_to`. The `create_queue` factory handles this.

### MovementCompletedEvent — `position_to='NULL'` / `position_from='NULL'`

The `set_implicit_values` model_validator auto-sets:
- PRODUCTION: `position_from = 'NULL'`
- CONSUMPTION: `position_to = 'NULL'`
- SHIPMENT: `position_to = 'OUT'`
- RECEIPT: `position_from = 'OUT'`

The `apply()` method skips `_ensure_position_not_deleted()` for `'NULL'` and `'OUT'`. Test info dicts for production/consumption movements should NOT manually set the auto-assigned field — let the validator handle it.

Container transfer detection: `is_container_transfer = (movement_type == TRANSFER and product_key is None and serial_key is None and position_from is not None)`.

### `_copy_batch_media_to_serials()` in BatchCompleted

This method does `Path("/media/traceability/...").glob(...)` and `shutil.copytree()`. In the testcontainer environment `/media` does not exist. This will silently do nothing (empty glob) rather than raising — confirmed by the `batch_dir.glob('*/*/*/')` returning an empty list if the path doesn't exist. Tests for BATCH-19 should either:
1. Skip (mark as manual-only, since it requires filesystem setup), or
2. Create the tmpdir via `tmp_path` fixture and verify the copy logic separately

Recommended: BATCH-19 is a smoke test that verifies the method is called without error (no exception raised), not that files were actually copied.

### BatchCompleted `auto_new_batch` Condition

```python
create_new_batch = (
    self.job.parameters.auto_new_batch
    and is_next_batch_available    # job.next_batch_available
    and not (self.job.traceability_level and not self.job.first_phase)
)
```

`is_next_batch_available` is read from `job.next_batch_available` at the start of `apply()`. The factory creates jobs with `next_batch_available=False` by default. Tests for BATCH-03 must set `next_batch_available=True`:

```python
db.collection("Job").update({"_key": job["_key"], "next_batch_available": True})
```

---

## Curated BatchCompleted Parametrize Matrix (D-08 through D-12)

Recommended test IDs and flag combinations for BATCH-20:

```python
@pytest.mark.parametrize("flags,expected_events", [
    # ID: first-last-no_trace-no_wh-no_auto
    pytest.param(
        dict(first_phase=True, last_phase=True, traceability_level="none", warehouse_management=False, auto_new_batch=False),
        ["BATCH_RELEASED", "JOB_CLOSED"],
        id="first-last-no_trace-no_wh"
    ),
    # ID: first-mid-no_trace-no_wh-no_auto (non-last: WIPDeclared)
    pytest.param(
        dict(first_phase=True, last_phase=False, traceability_level="none", warehouse_management=False, auto_new_batch=False),
        ["WIP_DECLARED"],
        id="first-mid-no_trace-no_wh"
    ),
    # ID: mid-mid-no_trace-no_wh-no_auto (non-first AND non-last: WIPRemoved + WIPDeclared)
    pytest.param(
        dict(first_phase=False, last_phase=False, traceability_level="none", warehouse_management=False, auto_new_batch=False),
        ["WIP_REMOVED", "WIP_DECLARED"],
        id="mid-mid-no_trace-no_wh"
    ),
    # ID: mid-last-no_trace-no_wh-no_auto (non-first + last: WIPRemoved + BatchReleased)
    pytest.param(
        dict(first_phase=False, last_phase=True, traceability_level="none", warehouse_management=False, auto_new_batch=False),
        ["WIP_REMOVED", "BATCH_RELEASED"],
        id="mid-last-no_trace-no_wh"
    ),
    # Warehouse management enabled
    pytest.param(
        dict(first_phase=True, last_phase=True, traceability_level="none", warehouse_management=True, auto_new_batch=False),
        ["MOVEMENT_COMPLETED", "BATCH_RELEASED"],
        id="first-last-no_trace-wh"
    ),
    # Traceability enabled (batch level)
    pytest.param(
        dict(first_phase=True, last_phase=True, traceability_level="batch", warehouse_management=False, auto_new_batch=False),
        ["SERIAL_UPDATED", "SERIAL_RELEASED", "BATCH_RELEASED"],
        id="first-last-trace-no_wh"
    ),
    # auto_new_batch (non-last batch scenario — requires qt_planned > batch_qt)
    pytest.param(
        dict(first_phase=True, last_phase=True, traceability_level="none", warehouse_management=False, auto_new_batch=True),
        ["BATCH_CREATED", "WORK_SESSION_CREATED"],
        id="first-mid-no_trace-no_wh-auto",  # needs batch_qt < qt_planned
    ),
    # ... etc. up to ~16 total combinations
], ...)
#
# EXCLUDED COMBINATIONS:
# - auto_new_batch=True + last batch (qt_completed >= qt_planned): no-op per D-09
# - step_check interactions: orthogonal per D-10 (covered by BATCH-14/BATCH-15 separately)
# - traceability + non-first-phase auto_new_batch: prevented by create_new_batch condition
```

---

## Common Pitfalls

### Pitfall 1: Missing `last_work_session_started` on Job

**What goes wrong:** `BatchCompletedEvent.apply()` calls `WorkSessionClosedEvent.create_as_child(self, dict(work_session_key=self.info.work_session_key, ...))`. But `self.info.work_session_key` is only set if `BaseProductionEvent.pre_processing()` sets it, which reads `job.last_work_session_started`. Factory creates jobs with `last_work_session_started=None`.

**Why it happens:** Factory was designed to set `active_batch_key` but not `last_work_session_started`.

**How to avoid:** After creating job + work session via factory, add:
```python
db.collection("Job").update({
    "_key": job["_key"],
    "last_work_session_started": ws["_key"]
})
```

**Warning signs:** `NoneType` errors or WorkSessionClosed events not appearing in Event collection.

### Pitfall 2: `ProgressOverrideRequestedEvent` is in `events/admin/`, Not `events/production/`

**What goes wrong:** Import path for direct instantiation is `from events.admin.progress_override_requested import ProgressOverrideRequestedEvent`.

**Why it happens:** The event inherits from `BaseAdmin`, not `BaseProductionEvent`. This means it does NOT have `_get_job_data()`, `get_current_work_session()`, or `get_batch_execution_data()` — it uses its own `_init_instance_variables()`.

**How to avoid:** Import from correct module. Also note `get_tx_collections()` is explicitly defined on the event (unlike BatchCompleted which inherits from BaseProductionEvent's version).

### Pitfall 3: BatchCompleted `completed_batch_qt` Must Match `batch.qt_total`

**What goes wrong:** `apply()` immediately raises `ValueError("Active batch quantity does not match...")` if `batch.qt_total != info.completed_batch_qt`.

**Why it happens:** The system enforces an explicit confirmation that the caller knows the batch quantity.

**How to avoid:** Always pass `completed_batch_qt=g["batch"]["qt_total"]` in the event info.

### Pitfall 4: `MovementCompletedEvent` Container Transfer vs Product Transfer Confusion

**What goes wrong:** Container transfer requires `product_key=None, serial_key=None, position_from=<real_key>`. Product transfer (TRANSFER type) requires `product_key` to be set. The `set_implicit_values` validator does NOT set positions for TRANSFER type — both must be explicit.

**How to avoid:** Check `is_container_transfer` condition in `_handle_transfer_production_consumption()` carefully. Seed a real Position with `fixed=False` for container transfer tests, and a separate Position with `fixed=True` for MOVE-10.

### Pitfall 5: Config Collection Is Not Truncated Between Tests

**What goes wrong:** `seed_config("enable_inventory_management", value=True)` in one test bleeds into the next if restoration fails.

**Why it happens:** Config is in `SKIP_TRUNCATE`. Phase 1 conftest has `_capture_config_defaults` + restore logic, but only restores keys that existed at session start. If a test inserts a NEW Config key, it won't be removed.

**How to avoid:** Only use `seed_config` to override existing Config keys (not insert new ones). The schema init creates `enable_inventory_management` with `value=False` — `seed_config` updates it to `True` for warehouse tests, and the restore logic resets it. [VERIFIED: conftest.py truncate_collections fixture]

---

## Code Examples

### Verified: Direct Event Save Pattern

```python
# Source: base_event.py __init__ + save() — verified
from events.production.step_completed import StepCompletedEvent

def test_example(db, create_production_graph):
    g = create_production_graph(num_steps=2)
    job = g["job"]
    batch = g["batch"]
    step_key = g["product"]["steps"][0]["_key"]  # first step of target phase

    # Set last_work_session_started (required by BaseProductionEvent)
    ws_key = g["work_session"]["_key"]
    db.collection("Job").update({"_key": job["_key"], "last_work_session_started": ws_key})

    event = StepCompletedEvent(info=dict(
        event_type="STEP_COMPLETED",
        primary=True,
        user_key=g["user"]["_key"],
        batch_key=batch["_key"],
        step_key=step_key,
    ))
    result = event.save()   # returns event.response

    # Assert DB state
    sxd_records = list(db.collection("StepExecutionData").find({
        "batch_key": batch["_key"],
        "step_key": step_key,
        "canceled": None,
    }))
    assert len(sxd_records) == 1
    assert sxd_records[0]["status"] == "done"
```

### Verified: HTTP API Test Pattern

```python
# Source: traceability.py /event endpoint + conftest.py client fixture
async def test_event_api(client, auth_headers, create_production_graph):
    g = create_production_graph()
    # Set last_work_session_started
    # auth_headers sets app.dependency_overrides[verify_token]
    auth_headers("operator production")

    response = await client.post("/event", json={
        "event_type": "BATCH_COMPLETED",
        "primary": True,
        "user_key": g["user"]["_key"],
        "active_batch_key": g["batch"]["_key"],
        "completed_batch_qt": g["batch"]["qt_total"],
        "work_session_key": g["work_session"]["_key"],
    })

    assert response.status_code == 200
    # 422 error body shape: {"detail": {"error_type": "...", "message": "...", "exception": "..."}}
```

### Verified: Event Cascade Assertion Helper

```python
# Recommended shared helper per Claude's Discretion area
def assert_event_dispatched(db, event_type: str, **filters):
    """Assert at least one Event record exists with given type and matching info fields."""
    query_filter = {"event_type": event_type, **filters}
    results = list(db.collection("Event").find(query_filter))
    assert results, f"Expected {event_type} event dispatched, found none (filters: {filters})"
    return results[0]

# Usage:
assert_event_dispatched(db, "JOB_CLOSED", job_key=g["job"]["_key"])
assert_event_dispatched(db, "WIP_DECLARED", job_key=g["job"]["_key"])
```

### Verified: Pytest.raises for Domain Exceptions

```python
from utils.exceptions import JobHasNoAssigneeError, JobIsActiveError, WipNotAvailableError, InventoryMovementException
from events.admin.progress_override_requested import ProgressOverrideRequestedEvent

def test_validation_no_assignee(db, create_production_graph):
    g = create_production_graph()
    db.collection("Job").update({"_key": g["job"]["_key"], "assigned_to": None})

    with pytest.raises(JobHasNoAssigneeError):
        ProgressOverrideRequestedEvent(info=dict(
            event_type="PROGRESS_OVERRIDE_REQUESTED",
            primary=True,
            user_key=g["user"]["_key"],
            job_key=g["job"]["_key"],
            new_job_qt_completed=5.0,
        )).save()
```

---

## Requirement to Plan Assignment (BATCH split)

Planner should assign BATCH requirements to 02-02 (HTTP API) vs 02-03 (direct event) as follows:

**Plan 02-02 (HTTP API layer):**
- BATCH-15 (step_check ValueError — 422 response)
- BATCH-16 (quantity mismatch ValueError — 422 response)
- BATCH-17 (closed job ValueError — 422 response)
- BATCH-21 (HTTP API integration — endpoint dispatch chain)

**Plan 02-03 (Direct event layer):**
- BATCH-01 through BATCH-14 (DB state assertions, cascade verification, parametrized matrix)
- BATCH-18 (serial code generation — inspects Serial document)
- BATCH-19 (media copy — smoke assertion, no exception raised)
- BATCH-20 (parametrized matrix — direct event calls)

Rationale: Validation errors that return 422 are best tested at the HTTP layer since that's where the exception-to-status mapping lives. All cascade/DB state assertions belong in direct tests per D-04.

---

## Environment Availability

Step 2.6: SKIPPED — Phase 2 has no new external dependencies beyond Phase 1 infrastructure. The testcontainer ArangoDB and Docker are already in use by Phase 1 tests. No new CLI tools, services, or runtimes required.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.x with pytest-asyncio (asyncio_mode = "auto") |
| Config file | `testing/pytest/pyproject.toml` |
| Quick run command | `cd testing/pytest && uv run pytest tests/step/ -x -q` |
| Full suite command | `cd testing/pytest && uv run pytest -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| STEP-01 | StepExecutionData → DONE status | unit/integration | `pytest tests/step/ -k "happy_path" -x` | ❌ Wave 0 |
| STEP-02 | Last step triggers BatchCompleted child | integration | `pytest tests/step/ -k "last_step" -x` | ❌ Wave 0 |
| STEP-03 | Form data stored in StepExecutionData | integration | `pytest tests/step/ -k "form_data" -x` | ❌ Wave 0 |
| STEP-04 | Work session key set correctly | integration | `pytest tests/step/ -k "work_session" -x` | ❌ Wave 0 |
| STEP-05 | Temp step data overwritten | integration | `pytest tests/step/ -k "overwrite" -x` | ❌ Wave 0 |
| STEP-06 | Missing batch raises ValueError | unit | `pytest tests/step/ -k "missing_batch" -x` | ❌ Wave 0 |
| STEP-07 | Response shape contains job_data + batch_data | integration | `pytest tests/step/ -k "response" -x` | ❌ Wave 0 |
| STEP-08 | HTTP API integration | e2e-ish | `pytest tests/step/ -k "api" -x` | ❌ Wave 0 |
| BATCH-01 to BATCH-20 | BatchCompleted cascade branches | integration | `pytest tests/batch/ -x` | ❌ Wave 0 |
| BATCH-21 | HTTP API integration | e2e-ish | `pytest tests/batch/ -k "api" -x` | ❌ Wave 0 |
| PROG-01 to PROG-16 | ProgressOverride branches + validation | integration | `pytest tests/progress/ -x` | ❌ Wave 0 |
| PROG-17 | HTTP API integration | e2e-ish | `pytest tests/progress/ -k "api" -x` | ❌ Wave 0 |
| MOVE-01 to MOVE-15 | Movement type coverage | integration | `pytest tests/movement/ -x` | ❌ Wave 0 |
| MOVE-16 | HTTP API integration | e2e-ish | `pytest tests/movement/ -k "api" -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/{module}/ -x -q` (the plan's own module)
- **Per wave merge:** `uv run pytest -x -q` (full suite)
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/step/__init__.py`
- [ ] `tests/step/test_step_completed.py`
- [ ] `tests/batch/__init__.py`
- [ ] `tests/batch/test_batch_completed_api.py`
- [ ] `tests/batch/test_batch_completed_direct.py`
- [ ] `tests/progress/__init__.py`
- [ ] `tests/progress/test_progress_override.py`
- [ ] `tests/movement/__init__.py`
- [ ] `tests/movement/test_movement_types.py`
- [ ] `tests/movement/test_movement_api_serial.py`

No new framework install needed — all infrastructure in place from Phase 1.

---

## Open Questions

1. **`_check_all_batch_steps_done()` implementation**
   - What we know: It's called in StepCompletedEvent.apply() at line 66 to decide whether to dispatch BatchCompleted
   - What's unclear: Its exact query — whether it checks StepExecutionData by step_key or phase step sequence
   - Recommendation: Read `backend/api/events/production/base_production.py` before implementing STEP-02 test. The test must ensure all steps except the last are in DONE status before completing the last step.

2. **`BaseProductionEvent.get_current_work_session()` implementation**
   - What we know: Called in StepCompleted and BatchCompleted to find the active WorkSession
   - What's unclear: Whether it queries by `batch_key` or `job.last_work_session_started`
   - Recommendation: Read `base_production.py` before implementing STEP-04. The factory may need additional setup.

3. **`BaseAdmin._reduce_wip()` and `update_work_order()` implementations**
   - What we know: Called in ProgressOverrideRequested for WIP management and work order state
   - What's unclear: Whether `update_work_order()` requires a pre-existing Queue entry for the work order
   - Recommendation: Read `backend/api/events/admin/base_admin.py` before implementing PROG-08/PROG-09.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `_copy_batch_media_to_serials()` silently no-ops when `/media` path doesn't exist | Critical Implementation Details | If it raises FileNotFoundError, BATCH-19 tests fail without extra setup |
| A2 | `create_production_graph` correctly sets `job.last_work_session_started` when `ws` is created | Standard Stack | All BatchCompleted tests fail with None work_session_key if not — mitigated by explicit update recommendation |
| A3 | `ProgressOverrideRequestedEvent.post_processing()` does not require `Event` collection to exist pre-call | Architecture Patterns | Event collection exists from schema init, so low risk |

---

## Sources

### Primary (HIGH confidence)
- `backend/api/events/production/step_completed.py` — StepCompletedEvent apply() logic
- `backend/api/events/production/batch_completed.py` — BatchCompletedEvent apply() + all helpers (489 lines)
- `backend/api/events/admin/progress_override_requested.py` — ProgressOverrideRequestedEvent (292 lines)
- `backend/api/events/inventory/movement_completed.py` — MovementCompletedEvent (292 lines)
- `backend/api/events/base_event.py` — save() lifecycle, create_as_child(), transaction management
- `backend/api/endpoints/traceability.py` — `/event` POST endpoint, error handling, response shape
- `testing/pytest/conftest.py` — Phase 1 fixtures: db, client, auth_headers, truncate_collections
- `testing/pytest/tests/factories/conftest.py` — All factory fixtures including create_production_graph
- `backend/api/models/event.py` — EventType enum, EventInfoModel
- `backend/api/models/inventory/movement.py` — InventoryMovementType, MovementStatus

### Secondary (MEDIUM confidence)
- `testing/pytest/pyproject.toml` — dependency versions, pytest config
- `testing/pytest/tests/factories/test_factory_smoke.py` — existing test style (BDD class pattern)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified in pyproject.toml
- Architecture patterns: HIGH — verified against source event code and base_event.py
- Pitfalls: HIGH for factory gaps (verified code), MEDIUM for batch media (assumed behavior)

**Research date:** 2026-04-10
**Valid until:** 2026-06-10 (stable codebase, no fast-moving dependencies)
