# Count Session Lifecycle

This document describes the lifecycle of inventory count sessions, including status transitions, event handling, and adjustment generation.

---

## Status Flow

```
PLANNED → STARTED → COMPLETED → PROCESSING → APPLIED
              ↑          ↓
              └──────────┘
                (resume)
```

| Status | Description | Warehouse App Visible | Can Edit |
|--------|-------------|----------------------|----------|
| PLANNED | Session created, not yet active | No | Yes (full) |
| STARTED | Active counting in progress | Yes | Limited |
| COMPLETED | Counting finished, ready for review/application | No | No |
| PROCESSING | Async workflow applying adjustments | No | No |
| APPLIED | Adjustments generated, session closed | No | No |
| CANCELED | Session canceled | No | No |

**Note:** The transition from COMPLETED to APPLIED involves asynchronous processing. See [Async Count Session Application](./async-count-session-application.md) for details.

**Count Record Status:** Individual count records remain in `confirmed` status throughout processing. A `processed: bool` field tracks whether a record has been evaluated, and `movement_keys` indicates which movements were created.

---

## Events

### CountSessionStartedEvent
- **Transition:** PLANNED → STARTED
- **Trigger:** Admin clicks "Start Session" in main app
- **Actions:**
  - Updates session status to STARTED
  - Sets `started` timestamp
- **File:** `backend/api/events/inventory/count_session_started.py`

### CountSessionCompletedEvent
- **Transition:** STARTED → COMPLETED
- **Trigger:** Admin clicks "Complete Session" in main app
- **Validation:**
  - Session must be in STARTED status
- **Actions:**
  - Updates session status to COMPLETED
  - Sets `completed` timestamp
  - Hides session from warehouse app
- **File:** `backend/api/events/inventory/count_session_completed.py`

### CountSessionResumedEvent
- **Transition:** COMPLETED → STARTED
- **Trigger:** Admin clicks "Resume Counting" in main app
- **Validation:**
  - Session must be in COMPLETED status
- **Actions:**
  - Updates session status back to STARTED
  - Clears `completed` timestamp
  - Makes session visible in warehouse app again
- **File:** `backend/api/events/inventory/count_session_resumed.py`

### CountSessionAppliedEvent
- **Transition:** COMPLETED → APPLIED
- **Trigger:** Admin clicks "Apply Adjustments" in main app
- **Validation:**
  - Session must be in COMPLETED status
  - No unresolved conflicts (multiple records with different `counted_qt` for same product/position)
- **Actions:**
  1. Builds a list of `InventoryMovementNew` objects for each count record with delta ≠ 0
  2. Creates MovementList of type ADJUSTMENT via `WarehouseListCreatedEvent` (child event)
  3. Updates session status to APPLIED
  4. Stores `adjustment_list_key` on session
- **Architecture Note:** Uses `WarehouseListCreatedEvent` to delegate list/movement creation, ensuring consistent handling across all warehouse list operations.
- **File:** `backend/api/events/inventory/count_session_applied.py`

---

## Race Condition Prevention

When a session transitions to COMPLETED (review mode), we must ensure no users are actively counting.

### Protections Implemented

| Event | Check | Behavior |
|-------|-------|----------|
| **CountSessionCompletedEvent** | No active counts | Blocks completion if any count records have `status='started'` |
| **CountStartedEvent** | Session must be `started` | Blocks new counts if session is completed/applied/canceled |
| **CountImportedEvent** | Session must be `completed` | Blocks imports if session is not in completed status (review mode) |

### Rationale

- **Completing session**: Blocks if active counts exist, ensuring all operators have finished before entering review mode
- **Starting counts**: Blocked during review to prevent new counting activity
- **Importing counts**: Allowed only during review (COMPLETED status) to enable data correction and bulk updates after counting is finished

Since session completion is blocked when active counts exist, there's no scenario where `CountCompletedEvent` or `CountCanceledEvent` would need to handle a completed session - all counts must be finished or canceled before the session can enter review.

---

## Duplicate Count Handling

When a count is completed (`CountCompletedEvent`), the system automatically discards duplicate count records to keep the records table clean and prevent confusion.

### Auto-Discard Rules

The system discards previous count records for the same product/position pair based on two rules:

#### Rule 1: Same User (Always Discard)
**All** previous counts by the **same user** are automatically discarded when they complete a new count, regardless of whether the values match.

**Rationale:** The latest count from a user always supersedes their previous attempts. Users may recount for various reasons (mistake, rechecking, etc.), and we assume their most recent count is correct.

#### Rule 2: Different Users (Discard if Matching)
Previous counts by **different users** are automatically discarded **only if** the new count matches exactly:

**Matching criteria (all must be true):**
- `counted_qt` is identical
- `counted_serial_keys` are identical (when sorted) for serialized products
- Both null or both present for serial keys

**Rationale:** When different users independently arrive at the same count result, keeping both records creates unnecessary duplicates. The matching count validates the accuracy, so only one record is needed.

**Non-matching counts (conflicts):** If counts from different users **don't** match, both records are kept and flagged as a conflict that requires manual resolution.

### Implementation

Located in `backend/api/events/inventory/count_completed.py`:

```python
def _discard_duplicate_counts(self):
    # 1. Always discard previous counts by SAME user
    self._discard_same_user_counts()
    
    # 2. Discard counts by OTHER users only if they MATCH
    self._discard_matching_counts_from_other_users()
```

### Examples

| Scenario | User A Count | User B Count | Result |
|----------|-------------|-------------|---------|
| Same user recounts | 100 → 95 | - | First count (100) discarded, keep 95 |
| Different users, matching | 95 | 95 | First count discarded, keep one copy |
| Different users, different qty | 95 | 98 | Both kept, flagged as conflict |
| Different users, same qty, different serials | 2 (S001, S002) | 2 (S001, S003) | Both kept, flagged as conflict |

---

## Conflict Detection

A **conflict** exists when multiple non-discarded count records for the same product/position pair have different `counted_qt` values.

### Conflict Check Query
```sql
FOR r IN inventory_count_record
FILTER r.inventory_count_session_key == @session_key
  AND r.status IN ['completed', 'submitted', 'confirmed']
COLLECT product_id = r._from, position_id = r._to
INTO records
LET counted_values = UNIQUE(records[*].r.counted_qt)
FILTER LENGTH(records) > 1 AND LENGTH(counted_values) > 1
RETURN { product_id, position_id }
```

The `LENGTH(UNIQUE(...)) > 1` check ensures we only flag conflicts when the counted quantities actually differ. After the auto-discard logic runs, matching counts from different users are eliminated, so this query only finds true conflicts.

### Resolution
Conflicts must be resolved in the UI before applying adjustments:
1. Navigate to Records tab
2. Click conflict indicator on affected row
3. Select which count record to keep
4. Other records are automatically discarded

---

## Adjustment Generation

### Delta Calculation
For each product/position pair:
```
delta = counted_qt - system_qt
```

Where:
- `system_qt` = Inventory snapshot at count time (captured when count started)
- `counted_qt` = What operator physically counted

### Movement Generation

**Non-serialized products:**
- Single ADJUSTMENT movement with `qt_confirmed = delta`

**Serialized products:**
- Individual movements for each serial:
  - Added serials (in `counted_serial_keys` but not in `system_serial_keys`): +1 adjustment
  - Removed serials (in `system_serial_keys` but not in `counted_serial_keys`): -1 adjustment

### Movement References
All generated movements include:
```python
references = InventoryMovementReferences(
  inventory_count_session_key = session_key
)
```

This links movements back to the originating count session for audit trail.

---

## Important Design Decisions

### Why system_qt from count record (not current inventory)?

The `system_qt` captured at count time is the adjustment baseline because:
1. It represents what the system "expected" at the moment of counting
2. Movements happening after the count are already reflected in current inventory
3. The adjustment is always: "bring inventory to what was counted"

Example:
```
T0: Count starts, system_qt = 100
T1: Operator counts 95 (delta = -5)
T2: Shipment of 10 units happens
T3: Current inventory = 90

Adjustment = -5 (not -15)
Result after adjustment: 90 - 5 = 85 = 95 - 10 ✓
```

### Why use ADJUSTMENT movements (not transfers)?

Count records capture **state**, not **movement**. They tell us "what is" vs "what was expected", not "where items went". Creating transfers would imply knowledge we don't have.

Adjustments:
- Are simple and accurate
- Don't make assumptions about inventory movement
- Provide clear audit trail
- Handle edge cases (deltas that don't balance)

### Why use WarehouseListCreatedEvent (not direct list creation)?

`CountSessionAppliedEvent` delegates to `WarehouseListCreatedEvent` rather than directly creating MovementList and movements because:

1. **Single responsibility**: List creation logic (code generation, validation, movement handling) stays in one place
2. **Consistency**: All movement lists are created through the same event, ensuring uniform behavior
3. **Extensibility**: Any future enhancements to list creation (notifications, hooks, etc.) automatically apply
4. **Reference merging**: `WarehouseListCreatedEvent` handles merging list-level and movement-level references properly

---

## Event Triggering

All status transitions use the generic `/event` endpoint with the appropriate event type:

| Event Type | Transition | Payload |
|------------|------------|---------|
| `COUNT_SESSION_COMPLETED` | STARTED → COMPLETED | `{ session_key }` |
| `COUNT_SESSION_RESUMED` | COMPLETED → STARTED | `{ session_key }` |
| `COUNT_SESSION_APPLIED` | COMPLETED → APPLIED | `{ session_key }` |

This follows the same pattern as other events (e.g., `COUNT_SESSION_STARTED`).

---

## UI Flow

### Main App (CountSessionScreen.vue)

| Current Status | Available Buttons |
|---------------|-------------------|
| PLANNED | "Start Session" |
| STARTED | "Complete Session" |
| COMPLETED | "Resume Counting", "Apply Adjustments" |
| APPLIED | None |

### Warehouse App

Sessions are only visible when status = STARTED. This ensures:
- Operators can't count during review
- Completed/applied sessions don't clutter the list

---

## Testing Checklist

- [ ] Session transitions follow valid paths only
- [ ] Conflicts block adjustment application
- [ ] Empty deltas don't generate movements
- [ ] Positive/negative adjustments work correctly
- [ ] Serialized products create individual serial movements
- [ ] Movement references link to count session
- [ ] Session stores adjustment_list_key after apply
- [ ] Warehouse app visibility follows status correctly
