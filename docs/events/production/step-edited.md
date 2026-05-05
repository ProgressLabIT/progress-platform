---
title: StepEditedEvent
description: STEP_EDITED — Progress Platform Events Reference
---

# StepEditedEvent

**EventType:** `STEP_EDITED`
**Domain:** production
**NATS subject:** `progress.notification.production`

Updates the form data on an existing `StepExecutionData` record after the
step has already been completed. Used when a supervisor or quality officer
needs to correct captured values without invalidating the batch.

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Dispatched via `POST /event` in `backend/api/endpoints/traceability.py`
with `event_type: STEP_EDITED`.

## Preconditions

- `StepExecutionData` record exists with key `info.execution_record_key`

## State Changes (Transaction)

**Collections:** Inherited from `BaseProductionEvent.get_tx_collections()`

- `StepExecutionData` updated: `form_data` replaced with `info.form_data`

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseProductionEvent`:
- Updates `job.last_online`
- Recalculates work order status
- Publishes to `progress.notification.production`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `execution_record_key` | `str` | Key of the `StepExecutionData` record to update |
| `form_data` | `list[FormFieldValue]` | Replacement form field values |
| `job_key` | `str \| None` | Job key (for `post_processing` context) |
| `batch_key` | `str \| None` | Batch key |
| `work_session_key` | `str \| None` | Work session key |

## Related Events

_None._

## Source

[`StepEditedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/production/step_edited.py)
