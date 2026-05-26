# WIP Availability: `next_batch_available`

## What it is

A boolean flag persisted on every `Job` document indicating whether the operator can start a new batch *right now*, given the WIP currently sitting at the job's input phase.

UI uses this flag to enable/disable the "start batch" action.

## How it is computed

Defined in `UPDATE_NEXT_BATCH_AVAILABLE_STATE_FOR_JOBS_IN_PHASES` at `backend/api/utils/traceability.py:308`.

```aql
LET input_for_phase = SUM(
  FOR w IN wip
  FILTER w.wo_key == @wo_key && w._to == CONCAT('Phase/', j.phase_key)
  RETURN w.quantity
)

LET qt_in_production = TO_NUMBER(j.active_batch_qt)
LET qt_remaining = j.qt_planned - j.qt_completed - qt_in_production
LET default_batch = j.parameters.production_batch_qt
LET qt_next_batch = default_batch == 0 ? qt_remaining : MIN([default_batch, qt_remaining])

LET next_batch_available = j.first_phase || qt_next_batch <= input_for_phase
```

Key consequence: the threshold (`qt_next_batch`) is **per-job** — it depends on `qt_planned`, `qt_completed`, `active_batch_qt`, and `parameters.production_batch_qt`. Two sibling jobs in the same phase can legitimately have different flags for the same `input_for_phase`.

## When the flag is recomputed

The query is executed by `BaseProductionEvent.update_wip_availability_for_phases()` (`backend/api/events/production/base_production.py:136`). It updates **all** jobs (open or closed) in the WO matching the given phase keys.

| Trigger | File | Phase(s) recomputed |
|---|---|---|
| `WIPBookedEvent` | `events/wip/wip_booked.py` | booking phase |
| `WIPUnbookedEvent` | `events/wip/wip_unbooked.py` | unbooking phase |
| `WIPDeclaredEvent` | `events/wip/wip_declared.py` | next phase (where wip lands) |
| `ProgressOverrideRequestedEvent` | `events/admin/progress_override_requested.py` | current + next (via `_update_batch_available_states`) |
| `JobResetEvent` | `events/admin/job_reset.py` | current + next (via `_update_batch_available_states`) |

Note: `WIPRemovedEvent` does **not** recompute — by design. It deletes booked WIP records (Phase→Job) on batch completion; phase-level free wip is unaffected.

`COMPLETE_JOB` (`utils/traceability.py:101`) explicitly sets `next_batch_available: null` on closed jobs.

## The inheritance gap (likely root cause of the reported bug)

When new jobs are inserted into an **already-running** phase, the flag is **inherited** from one sibling — not recomputed. Two endpoints do this:

- `POST /job/update` (action `INSERT`) — `endpoints/production.py:765`
- `PATCH /work-order/{wo_key}/update-quantities` (action `INSERT`) — `endpoints/production.py:266`

Both call `_get_phase_batch_available_state` (`endpoints/production.py:408`):

```python
'FOR j IN Job FILTER j.wo_key == @wo_key && j.phase_key == @phase_key LIMIT 1 RETURN j.next_batch_available'
```

Two failure modes:

1. **Sibling's threshold ≠ new job's threshold.** Inherited `false` when `true` would be correct (or vice versa).
   - Sibling: `qt_planned=100`, `default_batch=10`, `qt_completed=90` → `qt_next_batch=10`. Phase wip = 5 → flag `false`.
   - New job: `qt_planned=10`, `default_batch=2` → `qt_next_batch=2`. Phase wip = 5 → should be `true`. Inherits `false`. **Stuck.**

2. **`LIMIT 1` may pick a closed sibling**, which has `next_batch_available: null`. `create_job_record` then falls back to `first_phase` (`utils/production.py:547`), forcing `false` on any non-first phase regardless of actual wip.

The new job's flag is "stuck" until something else triggers `update_wip_availability_for_phases` for that phase (i.e., a booking, unbooking, declaration into the phase, or admin override).

## Why independent queues surface this

The `Queue.independent` flag (`models/production.py:244`) only affects whether `REORDER_JOB_QUEUES` rewrites an operator's queue order. It does **not** participate in the `next_batch_available` formula directly.

The connection is **operational**: with normal queues, work flows roughly in phase sequence — upstream jobs frequently produce, firing `WIPDeclaredEvent` for the downstream phase and refreshing the flag for everyone. With independent queues, operators reorder their work freely, downstream phases may sit idle for long stretches, and a stale/inherited flag never gets corrected because nothing triggers a recompute for that phase.

So independent queues don't *cause* the wrong flag — they extend the window in which it stays wrong.

## Remediation options

In order of preference:

1. **Recompute, don't inherit.** After inserting jobs in `update_jobs` and `update-quantities`, call `update_wip_availability_for_phases` for the affected phase(s) instead of (or in addition to) `_get_phase_batch_available_state`. Cheap — the AQL updates all jobs in the phase in a single pass.

2. **Self-heal on phase load.** Recompute opportunistically when the operator loads a job, so a stale flag never blocks the UI for long. Higher cost on the read path.

3. **Drop the persisted flag.** Compute `next_batch_available` on read (in `GET_WORKING_JOB_DATA` and the assignment list). Eliminates the staleness class entirely. Larger refactor.

## Diagnosing in the field

For a reported case, run against the WO:

```aql
FOR j IN Job
  FILTER j.wo_key == @wo_key && j.phase_key == @phase_key
  LET wip_on_phase = SUM(
    FOR w IN wip
    FILTER w.wo_key == j.wo_key && w._to == CONCAT('Phase/', j.phase_key)
    RETURN w.quantity
  )
  LET qt_remaining = j.qt_planned - j.qt_completed - TO_NUMBER(j.active_batch_qt)
  LET default_batch = j.parameters.production_batch_qt
  LET qt_next_batch = default_batch == 0 ? qt_remaining : MIN([default_batch, qt_remaining])
  RETURN {
    job: j._key,
    stage: j.stage,
    persisted: j.next_batch_available,
    expected: j.first_phase || qt_next_batch <= wip_on_phase,
    qt_next_batch,
    wip_on_phase
  }
```

If `persisted != expected`, the flag is stale — workaround is to fire any wip-affecting event for the phase (e.g., a no-op progress override, or simply re-running `UPDATE_NEXT_BATCH_AVAILABLE_STATE_FOR_JOBS_IN_PHASES` directly) until a proper fix lands.
