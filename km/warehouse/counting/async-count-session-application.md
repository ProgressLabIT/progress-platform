# Async Count Session Application

This document describes the asynchronous processing architecture for count session application, which replaced the original synchronous implementation to improve UX for large count sessions (500-1000+ records).

---

## Motivation

The original `CountSessionAppliedEvent` processed all count records synchronously in a single transaction. This caused problems at scale:

- **Long response times**: 500+ records could take 30+ seconds
- **Poor UX**: Users faced frozen UI with no feedback
- **All-or-nothing**: Single error aborted entire operation
- **No visibility**: Couldn't track progress or identify problematic records

The async implementation solves these issues by splitting the work into three phases: immediate confirmation, background processing, and finalization.

---

## Architecture Overview

### Three-Phase Processing

```
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 1: Sync Confirmation (~500ms)                                │
│ Event: CountSessionConfirmedEvent                                   │
│ • Validate session (status = COMPLETED)                             │
│ • Check for conflicts                                                │
│ • Create EMPTY MovementList (status = PLANNED)                      │
│ • Transition count records: completed/submitted → confirmed          │
│ • Lock inventory positions (set locked=true, locked_by=session_key) │
│ • Update session: status → PROCESSING                                │
│ • Trigger Prefect workflow via HTTP API                              │
└─────────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 2: Async Processing (50-200ms per record)                    │
│ Workflow: apply_inventory_counts (Prefect)                          │
│ • For each confirmed record with delta ≠ 0:                         │
│   - Event: CountAppliedEvent                                        │
│   - Create adjustment movement(s)                                    │
│   - Link to MovementList                                             │
│   - Mark record as processed=true OR store error                     │
│   - Continue on failure (isolation)                                  │
└─────────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 3: Sync Finalization (~200ms)                                │
│ Event: CountSessionAppliedEvent (refactored)                        │
│ • Unlock inventory positions (set locked=false, locked_by=null)     │
│ • Count movements created + failed records                           │
│ • Update MovementList: status → COMPLETED                            │
│ • Update session: status → APPLIED, store stats                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Status Flow (Updated)

```
PLANNED → STARTED → COMPLETED → PROCESSING → APPLIED
              ↑          ↓            ↓
              └──────────┘            │
                (resume)              │
                                      │
        Count Record Status:          │
        completed/submitted ──→ confirmed (processed: false → true)
                                      │
                                      └──→ (error_details if failure)
```

---

## Events

### CountSessionConfirmedEvent (NEW)

**File:** `backend/api/events/inventory/count_session_confirmed.py`

**Purpose:** Phase 1 - Validate session, create empty list, confirm records, trigger workflow

**Transition:** COMPLETED → PROCESSING

**Validation:**
- Session must be in COMPLETED status
- No unresolved conflicts (same check as original `CountSessionAppliedEvent`)

**Actions:**
1. Fetch and validate session
2. Check for conflicts (blocks if found)
3. Count records with delta ≠ 0 (winning record per product/position)
4. Create empty MovementList with `status=PLANNED`, `movement_type=ADJUSTMENT`
5. Bulk update count records: `completed`/`submitted` → `confirmed`
6. Lock inventory positions: Set `locked=true` and `locked_by=session_key` on all `is_in_position` records for products/positions in confirmed count records
7. Update session:
   - `status` → `PROCESSING`
   - `adjustment_list_key` = created list
   - `processing_started` = current timestamp
   - `movements_processed_count` = 0
8. Trigger Prefect workflow via post_processing() hook using HTTP API

**Response:**
```python
{
  'trigger_workflow': True,  # Signals API to start Prefect flow
  'adjustment_list_key': 'ml_...',
  'records_to_process': 123,
  'message': 'Count session confirmed - processing started'
}
```

**Why empty MovementList?**
- Allows immediate confirmation without blocking on movement creation
- Movements are added incrementally during Phase 2
- Required removing the `len(movements) >= 1` constraint from `MovementListNew` validation

**Winning Record Selection:**
The same AQL logic from original `CountSessionAppliedEvent` is used:
```sql
COLLECT product_id = r._from, position_id = r._to
INTO records
LET winning_record = FIRST(
  FOR rec IN records[*].r
  SORT rec.counted_at DESC
  LIMIT 1
  RETURN rec
)
```
Most recent count wins when multiple records exist for same product/position.

---

### CountAppliedEvent (NEW)

**File:** `backend/api/events/inventory/count_applied.py`

**Purpose:** Phase 2 - Process individual count record, create movements

**Transition:** Record remains in `confirmed` status, `processed` flag set to true

**Info Model:**
```python
class InfoModel(EventInfoModel):
  count_record_key: str
  movement_list_key: str
  inventory_count_session_key: str
```

**Validation:**
- Count record must exist
- Record must not have been processed yet (`processed != true`)

**Actions:**

1. **Fetch record** and calculate delta
2. **Check if serialized** (product.traceability_level)

**Non-serialized products:**
```python
# Single quantity adjustment
movement = InventoryMovementNew(
  product_key=record['product_key'],
  position_key=record['position_key'],
  movement_type=InventoryMovementType.ADJUSTMENT,
  qt_confirmed=delta,
  movement_list_key=self.info.movement_list_key,
  references=InventoryMovementReferences(
    inventory_count_session_key=self.info.inventory_count_session_key,
    inventory_count_record_key=self.info.count_record_key
  )
)
# Create via MovementCompletedEvent (child event)
```

**Serialized products:**
```python
# Calculate serial differences
added_serials = counted_serial_keys - system_serial_keys
removed_serials = system_serial_keys - counted_serial_keys

# Create movement per serial
for serial_key in added_serials:
  movement = InventoryMovementNew(..., qt_confirmed=+1, serial_key=serial_key)
  # Create via MovementCompletedEvent

for serial_key in removed_serials:
  movement = InventoryMovementNew(..., qt_confirmed=-1, serial_key=serial_key)
  # Create via MovementCompletedEvent
```

3. **Mark record as processed:**
```python
tx.collection('inventory_count_record').update({
  '_key': self.info.count_record_key,
  'processed': True,
  'movement_keys': self.movement_keys
})
```

**For zero-delta records:**
```python
tx.collection('inventory_count_record').update({
  '_key': self.info.count_record_key,
  'processed': True,
  'movement_keys': []
})
```

**Error Handling:**
```python
try:
  # ... processing logic
  return {'success': True, 'movements_created': count}
except Exception as e:
  # Store error but don't fail workflow
  tx.collection('inventory_count_record').update({
    '_key': self.info.count_record_key,
    'error_details': str(e)
  })
  return {'success': False, 'error': str(e)}
```

**Why use MovementCompletedEvent?**
- Maintains transaction boundaries (each record isolated)
- Triggers side effects (Kafka events, notifications)
- Ensures consistency with all other movement creation
- Properly handles serial tracking and position updates

---

### CountSessionAppliedEvent (REFACTORED)

**File:** `backend/api/events/inventory/count_session_applied.py`

**Purpose:** Phase 3 - Finalize session after async processing completes

**Transition:** PROCESSING → APPLIED

**Original vs Refactored:**

| Original | Refactored |
|----------|------------|
| COMPLETED → APPLIED | PROCESSING → APPLIED |
| Builds all movements | Only counts movements |
| Delegates to WarehouseListCreatedEvent | Updates existing list to COMPLETED |
| Single transaction (slow) | Fast finalization |

**Actions:**

1. **Validate session:**
   - Must be in `PROCESSING` status (not COMPLETED)
   - Must have `adjustment_list_key`

2. **Unlock inventory positions:**
   - Set `locked=false` and `locked_by=null` on all `is_in_position` records locked by this session

3. **Count movements and failures:**
```python
# Count successful movements
movements_created = db.aql.execute("""
  FOR m IN movement
  FILTER m.movement_list_key == @list_key
  COLLECT WITH COUNT INTO count
  RETURN count
""", bind_vars={'list_key': adjustment_list_key}).next()

# Count failed records
movements_failed = db.aql.execute("""
  FOR r IN inventory_count_record
  FILTER r.inventory_count_session_key == @session_key
    AND r.error_details != null
  COLLECT WITH COUNT INTO count
  RETURN count
""", bind_vars={'session_key': session_key}).next()
```

4. **Update MovementList:**
```python
tx.collection('MovementList').update({
  '_key': adjustment_list_key,
  'status': MovementListNewStatus.COMPLETED.value,
  'end': self.info.timestamp
})
```

5. **Update session:**
```python
tx.collection('InventoryCountSession').update({
  '_key': self.info.session_key,
  'status': InventoryCountSessionStatus.APPLIED.value,
  'movements_created': movements_created,
  'movements_failed': movements_failed,
  'processing_completed': self.info.timestamp
})
```

---

## Workflow Orchestration

**File:** `backend/workflow/flows/flowcode/apply_inventory_counts.py`

**Prefect Flow:** `main(session_key: str)`

### Tasks

#### 1. fetch_data_for_processing
```python
@task
def fetch_data_for_processing(session_key: str) -> tuple[list[dict], str]:
  """Fetch all count records in CONFIRMED status that haven't been processed yet."""
  db = connect_to_progress_db()

  query = """
    FOR r IN inventory_count_record
    FILTER r.inventory_count_session_key == @session_key
      AND r.status == 'confirmed' AND r.processed != true
    RETURN MERGE(r, { product_code: DOCUMENT(r._from).code, position_code: DOCUMENT(r._to).code })
  """
  records = list(db.aql.execute(query, bind_vars={'session_key': session_key}))
  movement_list_key = db.collection('InventoryCountSession').get(session_key).get('adjustment_list_key')

  return records, movement_list_key
```

**Why query again?**
- Workflow might be retried/restarted
- Ensures we process current state, not stale data from Phase 1
- Filters out already-processed records (idempotency)
- Fetches movement_list_key from session (not passed as parameter)

#### 2. apply_count_record
```python
@task(task_run_name=get_task_run_name)
def apply_count_record(record: dict, session_key: str, movement_list_key: str) -> bool:
  """Apply a single count record via event API."""
  event_data = dict(
    event_type='COUNT_APPLIED',
    count_record_key=record['_key'],
    movement_list_key=movement_list_key,
    inventory_count_session_key=session_key
  )

  r = httpx.post(base_url+'/event', headers=headers, json=event_data, timeout=5)
  return True  # Or Failed state on error
```

**Why call API instead of direct event?**
- Respects same transaction boundaries as user actions
- Triggers same middleware/logging/validation
- Simpler to test and monitor
- No need for shared DB connection pool

#### 3. finalize_session
```python
@task
def finalize_session(session_key: str) -> dict:
  """Finalize the count session via event API."""
  event_data = dict(
    event_type='COUNT_SESSION_APPLIED',
    session_key=session_key
  )
  r = httpx.post(base_url+'/event', headers=headers, json=event_data, timeout=5)
  r.raise_for_status()
```

### Flow Logic

```python
@flow(name="Apply Inventory Counts", log_prints=True)
def main(session_key: str):
  records, movement_list_key = fetch_data_for_processing(session_key)

  for record in records:
    apply_count_record(record=record, session_key=session_key, movement_list_key=movement_list_key)

  finalize_session(session_key)
```

**Why sequential not parallel?**
- Each record is independent (separate product/position)
- Database can handle concurrent writes via transactions
- Easier to implement and debug
- Prefect agent has limited concurrency anyway

**Future optimization:**
Could use `task.map()` for parallel processing if needed:
```python
results = apply_count_record.map(
  api=unmapped(api),
  record=records,
  session_key=unmapped(session_key),
  movement_list_key=unmapped(movement_list_key)
)
```

---

## API Integration

### Triggering the Workflow

The workflow is triggered from the frontend via the standard `/event` endpoint using the `COUNT_SESSION_CONFIRMED` event type:

```javascript
// CountSessionScreen.vue - applyAdjustments()
const response = await sendEvent({
  event_type: 'COUNT_SESSION_CONFIRMED',
  event_data: {
    session_key: props.countSessionKey,
  },
});
```

The `CountSessionConfirmedEvent` handles all Phase 1 work synchronously. The frontend then polls for workflow status using the Prefect API.

### Progress Tracking Endpoint

**File:** `backend/api/endpoints/counting.py`

**Route:** `GET /inventory/count-session/{session_key}/processed-records`

Returns the count of processed records for progress display:

```python
@router.get('/inventory/count-session/{session_key}/processed-records')
def get_counting_session_processed_records(session_key: str):
  query = """
    FOR r IN inventory_count_record
    FILTER r.inventory_count_session_key == @session_key && r.processed == true
    RETURN 1
  """
  result = db.aql.execute(query, bind_vars=dict(session_key=session_key), count=True).count()
  return result
```

### Prefect API Integration (Frontend)

The frontend uses `usePrefectAPI` composable to monitor workflow status:

```javascript
// usePrefectAPI.js
async function findDeploymentByName(deploymentName) {
  const response = await axios.post(`${prefectBaseUrl}/deployments/filter`, {
    deployments: { name: { like_: deploymentName } },
    limit: 1
  })
  return response.data[0] || null
}

async function getFlowRunsForSession(sessionKey) {
  const deployment = await findDeploymentByName('apply_inventory_counts')
  const flowRuns = await getFlowRunsByDeployment(deployment.id, 10)
  return flowRuns.find(run => run.parameters?.session_key === sessionKey)
}
```

**Deployment Name:** `apply_inventory_counts` (matches flow function name in `sys_loader.py`)

---

## Frontend Updates

### CountSessionScreen.vue

**Progress Display:**
```vue
<!-- Processing - Progress Display (in header) -->
<div
  v-if="sessionStatus === 'processing' &&
        !errorStates.includes(flowRunStatus)"
  class="row items-center q-gutter-sm"
>
  <q-spinner-dots color="theme-blue" size="sm" />
  <div class="text-caption">
    {{ $t('warehouse.counting.processing_progress', {
      processed: processedRecords,
      total: countSessionStore.records.filter(r => r.status !== 'discarded').length
    }) }}
  </div>
</div>

<!-- Processing Errors -->
<template v-if="sessionStatus === 'applied' && processingErrors > 0">
  <q-icon color="theme-orange" size="xs" name="mdi-alert" />
  <div class="text-caption highlight">
    {{ $t('warehouse.counting.processing_errors', { count: processingErrors }) }}
  </div>
</template>
```

**Workflow Status Monitoring:**
```javascript
const { 
  findDeploymentByName, 
  getFlowRunsForSession, 
  triggerFlowRun 
} = usePrefectAPI();

const flowRunStatus = ref(null);
const processedRecords = ref(0);
const errorStates = ['FAILED', 'CRASHED', 'CANCELLED', 'NOT_FOUND', 'API_ERROR'];

async function checkProcessingStatus() {
  // Fetch processed record count
  api.get(`/inventory/count-session/${props.countSessionKey}/processed-records`)
    .then(response => {
      processedRecords.value = response.data;
    });

  // Check Prefect flow run status
  const flowRun = await prefectAPI.getFlowRunsForSession(props.countSessionKey);
  if (flowRun) {
    flowRunStatus.value = flowRun.state_type;
  }
}
```

**Polling (every 3 seconds):**
```javascript
let processingPollInterval = null;

watch(sessionStatus, (newStatus, oldStatus) => {
  if (newStatus === 'processing' && !processingPollInterval) {
    processingPollInterval = setInterval(async () => {
      await checkProcessingStatus();
    }, 3000);
    checkProcessingStatus(); // Check immediately
  }
});

onBeforeUnmount(() => {
  if (processingPollInterval) {
    clearInterval(processingPollInterval);
  }
});
```

**Apply Function (triggers COUNT_SESSION_CONFIRMED event):**
```javascript
async function applyAdjustments() {
  const response = await sendEvent({
    event_type: 'COUNT_SESSION_CONFIRMED',
    event_data: {
      session_key: props.countSessionKey,
    },
  });

  await countSessionStore.loadSessionData(props.countSessionKey);
}
```

**Resume Processing (for failed workflows):**
```javascript
async function resumeProcessing() {
  const deployment = await prefectAPI.findDeploymentByName('apply_inventory_counts');
  await prefectAPI.triggerFlowRun(deployment.id, {
    session_key: props.countSessionKey
  });
  // Restart polling...
}
```

### CountSessionRecordsTab.vue / useCountRecordFilters.js

**Error Filter State:**
```javascript
// useCountRecordFilters.js
filters: {
  // ... other filters
  onlyErrors: false,
}

// Filter logic
if (filters.value.onlyErrors) {
  result = result.filter(r => r.hasError);
}
```

**Error Detection in Aggregation:**
```javascript
// useCountRecordAggregation.js
aggregate.hasError = aggregate.records.some(r => r.error_details);
```

**Filter UI in CountRecordFilterSidebar.vue:**
```vue
<q-checkbox
  v-model="filters.onlyErrors"
  :label="$t('warehouse.counting.errors_only')"
  dense
/>
```

---

## Database Schema Changes

### InventoryCountSession

**New Fields:**
```python
processing_started: datetime | None = None
processing_completed: datetime | None = None
movements_processed_count: int | None = None  # Reserved for future use
```

**New Status:**
```python
class InventoryCountSessionStatus(str, Enum):
  # ... existing statuses
  PROCESSING = 'processing'  # Between COMPLETED and APPLIED
```

**Status Tracking:**
- `movements_created`: Count of successful movements (from finalization)
- `movements_failed`: Count of records with errors (from finalization)

### InventoryCountRecord

**New Fields:**
```python
processed: bool = False  # True when record has been evaluated by CountAppliedEvent
error_details: str | None = None  # Error message if movement creation failed
```

**Status Change:**
- Removed `APPLIED` status from `InventoryCountStatus` enum
- Records remain in `confirmed` status after processing
- Use `processed` flag to determine if record has been evaluated
- Use `movement_keys` to determine if movements were created

### MovementList Validation

**Change in `MovementListNew`:**
```python
@model_validator(mode='before')
def validate(cls, values):
  # Allow empty movement lists for incremental population
  movements = values.get('movements')
  if not movements:
    return values  # Skip validation if empty

  # ... rest of validation for non-empty lists
```

**Rationale:**
- Enables Phase 1 to create list immediately
- Movements added in Phase 2 via `MovementCompletedEvent`
- List finalized in Phase 3 with `status=COMPLETED`

### Inventory (is_in_position) Position Locking

**New Fields:**
```python
class Inventory(BaseModel):  # edge is_in_position
  # ... existing fields
  locked: bool = False  # True means inventory is locked during adjustment processing
  locked_by: str | None = None  # count session key that locked this inventory
```

**Purpose:**
Position locking prevents inventory changes during the async adjustment processing phase to ensure data consistency.

**Lock Flow:**
1. **Lock (Phase 1):** `CountSessionConfirmedEvent` sets `locked=true` and `locked_by=session_key` for all inventory records involved in confirmed counts
2. **Validation:** `InventoryChangedEvent` blocks any inventory movements when `locked=true`
3. **Unlock (Phase 3):** `CountSessionAppliedEvent` sets `locked=false` and `locked_by=null` after processing completes

**Validation in InventoryChangedEvent:**
```python
if current_record.get('locked', False):
    raise InventoryMovementException(
        f'Inventory for product {product.code} in position {position["code"]} '
        f'is locked during adjustment processing and cannot be changed.'
    )
```

**Why Lock Positions?**
- **Review Protection:** When session is COMPLETED, users can still edit count records. Locking doesn't apply here.
- **Processing Protection:** When session is PROCESSING, adjustments are being applied. Locks prevent concurrent inventory changes that could cause inconsistencies.
- **Clean Separation:** COMPLETED = review mode (no locks), PROCESSING = adjustment mode (locked)

---

## Error Handling

### Error Isolation

Each count record is processed in a **separate transaction**. If one fails:
- Error stored in `count_record.error_details`
- Record remains in `confirmed` status (can be retried)
- Other records continue processing
- Session still transitions to `APPLIED` (partial success)

**Benefits:**
- No all-or-nothing failures
- Clear visibility of problematic records
- Manual retry/correction possible
- Session doesn't get stuck

### Retry Strategy

| Component | Retries | Delay | Rationale |
|-----------|---------|-------|-----------|
| fetch_confirmed_records | 3 | 5s | Database read (idempotent) |
| apply_count_record | 2 | 3s | API call (event is idempotent) |
| finalize_session | 3 | 5s | Critical final step |

**Event Idempotency:**
- `CountAppliedEvent`: Checks record status, skips if already applied
- `CountSessionAppliedEvent`: Checks session status, fails if not PROCESSING

### Recovery Scenarios

**Workflow crashes during Phase 2:**
- Session remains in `PROCESSING`
- Some records in `applied`, others in `confirmed`
- Manual options:
  1. Restart workflow (will only process remaining `confirmed` records)
  2. Manually finalize via direct event call

**Finalization fails:**
- Session stuck in `PROCESSING`
- All movements created and linked to list
- Manual finalize via API:
```bash
curl -X POST http://api/event \
  -d '{"event_type":"COUNT_SESSION_APPLIED","session_key":"..."}'
```

---

## Important Design Decisions

### Why three phases (not two)?

**Alternative considered:** Sync validation → Async processing + finalization

**Chosen approach:** Sync validation → Async processing → Sync finalization

**Rationale:**
- Finalization must be atomic (update list + session)
- Workflow engine shouldn't hold transaction lock
- Clearer separation: workflow = business logic, events = state transitions

### Why confirm all records upfront?

**Alternative considered:** Confirm records incrementally during processing

**Chosen approach:** Bulk transition `completed/submitted` → `confirmed` in Phase 1

**Rationale:**
- Atomic state transition (no partial confirmations)
- Simpler workflow (doesn't need to update record status)
- Clear audit trail (all confirmed at same timestamp)

### Why query records again in workflow?

**Alternative considered:** Pass record list from Phase 1 to workflow

**Chosen approach:** Re-query records in workflow

**Rationale:**
- Workflow might be retried/restarted
- Ensures we process current state
- Handles edge case where records are manually modified during processing

### Why not use workflow for Phase 1?

**Alternative considered:** Entire process as workflow (including validation)

**Chosen approach:** Phase 1 as synchronous event, trigger workflow from API

**Rationale:**
- Immediate validation feedback to user
- Transaction holds all validation locks
- Workflow agent might be down/busy
- Follows existing pattern (sync validation → async work)

### Why MovementCompletedEvent (not direct movement creation)?

**Same rationale as original implementation:**
- Maintains transaction boundaries
- Triggers side effects (Kafka, notifications)
- Ensures consistency across all movement creation
- Properly handles serial tracking

---

## Deployment

### Docker Compose Setup

The Prefect workflow services are included in the main development compose files:

**Files:** `deploy/compose/dev.yaml`, `deploy/compose/dev.debug.yaml`

The workflow agent runs alongside the main application services and connects to the Prefect server for task orchestration.

### Workflow Deployment

**Script:** `backend/workflow/flows/sys_loader.py`

The sys_loader script automatically discovers and deploys flows from the `flowcode/` directory.

**Deploy command:**
```bash
cd backend/workflow/flows
python sys_loader.py
```

**Verify deployment:**
```bash
prefect deployment ls
# Should show: apply_inventory_counts
```

---

## Testing Checklist

### Phase 1: Confirmation
- [ ] Session must be in COMPLETED status (not STARTED/APPLIED)
- [ ] Conflicts block confirmation
- [ ] Empty MovementList created with correct attributes
- [ ] Records transitioned to CONFIRMED status
- [ ] Session updated to PROCESSING with correct timestamps
- [ ] Zero-delta records not counted in `records_to_process`
- [ ] Positions locked (`locked=true`, `locked_by=session_key`)

### Phase 2: Processing
- [ ] Workflow queries only CONFIRMED records that haven't been processed
- [ ] Non-serialized: Single movement with correct `qt_confirmed`
- [ ] Serialized: Individual movements per serial difference
- [ ] Movements linked to MovementList via `movement_list_key`
- [ ] Movements include count session/record references
- [ ] Successful records marked with `processed=true`
- [ ] Failed records store error in `error_details`
- [ ] Failures don't block other records

### Phase 3: Finalization
- [ ] Session must be in PROCESSING status (not COMPLETED)
- [ ] Positions unlocked (`locked=false`, `locked_by=null`)
- [ ] Movement count matches created movements
- [ ] Failed count matches records with error_details
- [ ] MovementList status → COMPLETED
- [ ] Session status → APPLIED
- [ ] Timestamps populated correctly

### Workflow Orchestration
- [ ] Empty sessions handled correctly (no records to process)
- [ ] Retries work correctly (idempotency via `processed` flag)
- [ ] Workflow visible in Prefect UI
- [ ] Task run names show position > product for clarity

### Frontend
- [ ] PROCESSING status shows spinner and progress count
- [ ] Progress count updates every 3s via `/processed-records` endpoint
- [ ] Flow run status monitored via Prefect API
- [ ] Error states (FAILED, CRASHED, etc.) show "Resume Processing" button
- [ ] Error filter shows only failed records
- [ ] Auto-refresh stops when complete or on error
- [ ] Translations work in both languages

### Error Recovery
- [ ] Partial failure leaves session in APPLIED (not stuck)
- [ ] Failed records can be manually corrected and reprocessed
- [ ] Workflow can be restarted for retry
- [ ] Manual finalization works if workflow fails

---

## Performance Characteristics

### Synchronous (Original)
- **500 records**: ~25-30 seconds
- **1000 records**: ~50-60 seconds
- **User experience**: Frozen UI, timeout risk
- **Failure mode**: All-or-nothing

### Asynchronous (New)
- **Phase 1**: ~500ms (regardless of record count)
- **Phase 2**: 50-200ms per record (parallel potential)
- **Phase 3**: ~200ms (regardless of record count)
- **Total for 1000 records**: ~1 minute (with progress)
- **User experience**: Immediate feedback, real-time progress
- **Failure mode**: Partial success with error visibility

---

## Future Enhancements

### Parallel Processing
Use Prefect's task mapping for concurrent record processing:
```python
from prefect import unmapped

results = apply_count_record.map(
  api=unmapped(api),
  record=records,
  session_key=unmapped(session_key),
  movement_list_key=unmapped(movement_list_key)
)
```

**Benefits:**
- ~5-10x faster for large sessions
- Better resource utilization

**Considerations:**
- Database connection pool sizing
- Transaction lock contention
- Prefect agent concurrency limits

### Manual Retry for Failed Records

Add UI button to retry only failed records:
```python
@router.post('/inventory/count-session/{session_key}/retry-failed')
async def retry_failed_records(session_key: str):
  # Fetch records with error_details != null
  # Clear error_details, set status back to confirmed
  # Trigger workflow again (will only process these)
```

### Progress via WebSocket

Replace polling with real-time updates:
```python
# In CountAppliedEvent.apply()
await manager.broadcast(
  event='count_record_processed',
  data={'session_key': ..., 'progress': ...}
)
```

### Notification on Completion

Send notification when processing completes:
```python
# In CountSessionAppliedEvent.apply()
if self.info.movements_failed > 0:
  create_notification(
    message=f"Count session applied with {movements_failed} errors",
    type='warning'
  )
```

---

## Related Documentation

- [Count Session Lifecycle](./count-session-lifecycle.md) - Overall session status flow
- [Count Record Import/Export](./import-export/count-record-import-export.md) - Bulk data operations
- [Count Session Records Tab UI Logic](./count-session-records-tab-ui-logic.md) - Frontend record display
