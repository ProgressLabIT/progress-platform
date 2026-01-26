# Queue Management in Progress Platform

## Overview

The Progress Platform uses queues to track work orders and jobs that need attention. This document describes the queue management logic, including when items should be added to or removed from queues.

## Queue Types

1. **Work Order Queue** - Site-level queue containing work orders that are active (not closed)
2. **Job Queue** - User-level queue containing jobs assigned to specific operators

## Work Order Queue Management

### Key Files
- `backend/api/events/production/base_production.py` - Event-based queue updates (in `update_work_order()`)
- `backend/api/endpoints/production.py` - Direct API endpoint queue updates
- `backend/api/utils/production.py` - Queue query definitions (`ADD_WORK_ORDER_TO_QUEUE`, `REMOVE_WORK_ORDER_FROM_QUEUE`)

### Work Order Status Transitions

| Previous Status | New Status | Queue Action |
|-----------------|------------|--------------|
| CREATED | STARTED | None (already in queue) |
| CREATED | CLOSED | **Remove** from queue |
| STARTED | CLOSED | **Remove** from queue |
| CLOSED | CREATED | **Add** to queue |
| CLOSED | STARTED | **Add** to queue |
| Any | Same | None |

### Correct Logic Pattern

```python
# Remove work order from queue when it becomes closed
if wo_previous_state.status != WorkStatus.CLOSED and updated_wo.status == WorkStatus.CLOSED:
    tx.aql.execute(ProductionQueries.REMOVE_WORK_ORDER_FROM_QUEUE, ...)

# Re-add work order to queue when it's reopened (from closed to anything else)
if wo_previous_state.status == WorkStatus.CLOSED and updated_wo.status != WorkStatus.CLOSED:
    tx.aql.execute(ProductionQueries.ADD_WORK_ORDER_TO_QUEUE, ...)
```

### Common Mistake to Avoid

❌ **Wrong:** `updated_wo.status != WorkStatus.STARTED`
✅ **Correct:** `updated_wo.status != WorkStatus.CLOSED`

The re-add condition must check for "not CLOSED" (meaning reopened), not "not STARTED". Using "not STARTED" would only re-add when transitioning to CREATED, missing the common case of CLOSED → STARTED (e.g., when reducing quantity on a completed work order).

## Job Queue Management

### Key Files
- `backend/api/events/production/job_started.py` - Adds job to queue when operator self-assigns
- `backend/api/events/production/job_closed.py` - Removes job from queue when completed
- `backend/api/events/admin/progress_override_requested.py` - Re-adds job to queue when reopened via progress override
- `backend/api/endpoints/production.py` - Direct job updates (partial queue handling)
- `backend/api/utils/production.py` - Queue query definitions (`ADD_JOB_TO_QUEUE`, `REMOVE_JOB_FROM_QUEUE`)

### Job Queue Logic

```python
# In JobStartedEvent: Add to queue only if job was unassigned (self-assignment)
if self.job.assigned_to is None:
    add_to_queue = True

# In JobClosedEvent: Remove from assigned user's queue
if completed_job.assigned_to:
    tx.aql.execute(ProductionQueries.REMOVE_JOB_FROM_QUEUE, ...)

# In ProgressOverrideRequestedEvent: Re-add when reopening a closed job
if self.info.quantity_change < 0 and was_closed:
    tx.aql.execute(ProductionQueries.ADD_JOB_TO_QUEUE, ...)
```

### Direct Endpoint Updates - Design Intent

The following endpoints handle job closing/removal but do NOT reopen jobs:

- `POST /job/update` (lines 737-837 in `endpoints/production.py`)
- `PATCH /work-order/{wo_key}/update-quantities` (lines 269-297 in `endpoints/production.py`)

**This is intentional behavior:**
- Closed jobs should remain closed
- If work order quantity is increased and existing jobs are closed, a NEW job should be created
- The client is expected to send the appropriate job inserts along with updates

**Multi-Work Order Support:**
The `/job/update` endpoint supports updating jobs across multiple work orders in a single request. The endpoint:
1. Tracks all affected work orders during job processing
2. Updates each affected work order's calculated status and quantities
3. Manages queue operations (add/remove) for each work order based on status transitions
4. Commits all changes atomically in a single transaction

## ⚠️ Critical: Queue Operation Ordering

### The REORDER_JOB_QUEUES Query

The `REORDER_JOB_QUEUES` query (`backend/api/utils/production.py`) rebuilds operator queues by:
1. Getting work orders from the **site queue** (`Queue.type == 's'`)
2. For each work order, iterating through its phase sequence
3. Finding jobs matching the work order, phase, and operator
4. Filtering out closed jobs (`j.stage != 'closed'`)
5. **Overwriting** the operator queue with the filtered job list

**Two conditions can cause a job to be removed:**
1. Job is still marked as `stage: 'closed'` when reorder runs
2. Job's work order is not in the site queue when reorder runs

### Historical Context (Commit History)

**Commit `53299a91` (Sep 29, 2025)** - Partial fix for timing issue:
> "the reordering removes the job from the queue because it hasn't been updated as not closed."

This fix moved queue operations to AFTER the job update, addressing **timing issue #1** (job still marked as CLOSED). However, it did NOT address **timing issue #2** (work order not in site queue yet).

**Commit `6a01c2a4` (Sep 24, 2025)** - Introduced work order queue bug:
Attempted to fix work order queue for CREATED↔CLOSED transitions but used wrong condition (`!= STARTED` instead of `!= CLOSED`), causing work orders to not be re-added when reopening.

### The ProgressOverrideRequestedEvent Trap

In event-based processing:
- `apply()` runs first (job queue operations)
- `post_processing()` runs after (work order queue operations via `update_work_order()`)

**Problem in ProgressOverrideRequestedEvent:** When reopening a closed work order/job:
1. Job is added to queue in `apply()`
2. `REORDER_JOB_QUEUES` runs in `apply()` - but WO not in site queue yet!
3. Reorder query finds no matching work orders → **job is removed**
4. Work order is added to site queue in `post_processing()` (too late!)

### When REORDER_JOB_QUEUES is Safe vs Unsafe

| Context | Work Order in Site Queue? | Safe to Reorder? |
|---------|---------------------------|------------------|
| `create_job_record` (new job) | ✅ Yes (WO created first) | ✅ Safe |
| `JobStartedEvent` (self-assign) | ✅ Yes (WO exists) | ✅ Safe |
| `update_jobs` endpoint (reassign) | ✅ Yes (WO exists) | ✅ Safe |
| `update_target_queue` utility | ✅ Yes (used in above contexts) | ✅ Safe |
| **`ProgressOverrideRequestedEvent`** | ❌ No (added in post_processing) | ❌ **Unsafe** |
x | **`JobResetEvent`** | ❌ No (added in post_processing) | ❌ **Unsafe** |

### Solution

When re-adding jobs in events where the work order might also be getting reopened (like `ProgressOverrideRequestedEvent` or `JobResetEvent`):

1. **In `apply()`:** Add job to queue, but do NOT reorder
2. **In `post_processing()`:** After `update_work_order()` runs (which re-adds WO to site queue), THEN reorder

```python
# In apply():
self._job_was_reopened = was_closed  # Store flag for post_processing
self.tx.aql.execute(ProductionQueries.ADD_JOB_TO_QUEUE, ...)
# DON'T reorder here - WO not in site queue yet!

# In post_processing():
def post_processing(self):
    self.update_work_order()  # This re-adds WO to site queue
    
    # NOW it's safe to reorder
    if getattr(self, '_job_was_reopened', False):
        self.tx.aql.execute(ProductionQueries.REORDER_JOB_QUEUES, ...)
```

**Note:** The `update_target_queue()` utility function in `utils/production.py` does add + reorder, but it's safe because it's only used in contexts where the work order is already in the site queue.

## Work Order Status Calculation

The work order status is automatically calculated based on job states in `UPDATE_WORK_ORDER` query (`backend/api/utils/traceability.py`):

```javascript
// Check if WO is open by checking if any job is not closed
LET open = TO_BOOL(COUNT(FOR j IN jobs FILTER j.stage != 'closed' RETURN 1))

// Check if WO is started by checking if any job is not in 'created' stage
LET started = TO_BOOL(COUNT(FOR j IN jobs FILTER j.stage != 'created' RETURN 1))

// Define wo status
LET status = open ? (started ? 'started' : 'created') : 'closed'
```

## Testing Considerations

When testing queue management, verify these scenarios:
1. New work order creation → added to queue
2. Work order completion (all jobs closed) → removed from queue
3. Progress override decreasing quantity on completed WO → re-added to queue
4. Job assignment → job added to operator's queue
5. Job completion → job removed from operator's queue
6. Progress override reopening closed job → job re-added to queue

