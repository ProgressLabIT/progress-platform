---
plan: 02-05
phase: 02-critical-event-tests
status: complete
completed: 2026-04-10
requirements_covered: [MOVE-01, MOVE-02, MOVE-03, MOVE-04, MOVE-05, MOVE-06, MOVE-07, MOVE-08, MOVE-09, MOVE-10, MOVE-11, MOVE-12, MOVE-13, MOVE-14, MOVE-15, MOVE-16]
tests_written: 18
tests_passed: 18
---

# Plan 02-05 Summary: MovementCompletedEvent Dual-Layer Test Suite

## What Was Built

`testing/pytest/tests/movement/test_movement_completed.py` — 18 tests in two classes covering all movement types, error paths, and HTTP API layer for MovementCompletedEvent.

## Test Structure

**TestMovementCompletedDirect (16 methods):**
- MOVE-01: Receipt adds inventory at destination
- MOVE-02: Receipt with traceability requires serial_code (error), and creates serial (success)
- MOVE-03: Receipt with serial already in inventory raises InventoryMovementException
- MOVE-04: Shipment removes inventory from source
- MOVE-05: Shipment with traceability requires serial_key
- MOVE-06: Shipment insufficient inventory raises
- MOVE-07: Adjustment adds/removes quantity
- MOVE-08: Product transfer updates both source and destination
- MOVE-09: Container transfer (no product_key) executes without error
- MOVE-10: Fixed position cannot be container-transferred
- MOVE-11: Production movement creates inventory at destination
- MOVE-12: Consumption removes inventory from source
- MOVE-13: Reversal type raises InventoryMovementException
- MOVE-14: Deleted position raises before handler dispatch
- MOVE-15: Planned movement (pre-existing movement_key) updated to COMPLETED

**TestMovementCompletedAPI (2 methods):**
- MOVE-16: HTTP POST /event with receipt returns 200
- MOVE-13 HTTP: Reversal type returns 422

## Infrastructure Fixes

**conftest.py — `create_inventory_at_position` edge orientation:**
Was `_from=Position/..., _to=Product/...` (incorrect). Fixed to `_from=Product/..., _to=Position/...` to match `InventoryChangedEvent.apply()` which queries `_from=Product/{key}, _to=Position/{key}`.

**conftest.py — `create_serial` deleted field:**
Added `deleted: False` default so serial documents match `Serial.find({"deleted": False})` queries.

## Key Findings

- `is_in_position` edge orientation: `_from=Product/{key}`, `_to=Position/{key}` — opposite of intuition
- `TraceabilityLevel` enum for inventory events: `"complete"` or `"form_only"` (not `"serial"` or `"batch"`)
- `InventoryMovement` model uses `type` field (not `movement_type`) for the movement type discriminator
- Adjustment movements require `position_from == position_to` (same position) — the model validator allows this only for ADJUSTMENT and REVERSAL types
- MOVE-15 (planned movement): must pass explicit `start=ts, timestamp=ts` in info — the `set_implicit_values` validator uses `values.get('timestamp')` which is None at mode='before' time (default_factory not yet applied)
- Container transfer (MOVE-09): `update_match({"_from": "Position/{container}"}, {"_to": "Position/{new_parent}"})` — operates on `is_in_position` edges with `_from` pointing to the container Position, not Product edges

## Verification

```
18 passed
```
