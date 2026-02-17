# Float Precision Manual Rounding Checklist

This document lists calculation sites where `round_float()` should be used to prevent floating-point precision issues in raw dictionary updates.

## Critical Pattern: Division Operations

### Progress Calculations (Integer Results)
These calculate job/batch progress percentages as integers - use `round()` directly:

1. **backend/api/events/production/batch_completed.py:165** ✓
   ```python
   new_progress = round(100 * new_job_qt_completed / self.job.qt_planned)
   # Integer result - round() is sufficient
   ```

2. **backend/api/events/admin/batch_canceled.py:95** ✓
   ```python
   progress = round(100 * self.job.qt_completed / self.job.qt_planned)
   # Integer result - round() is sufficient
   ```

3. **backend/api/events/admin/progress_override_requested.py:296** ✓
   ```python
   new_job_progress = round(100 * self.info.new_job_qt_completed / self.job.qt_planned)
   # Integer result - round() is sufficient
   ```

### Ratio/Percentage Calculations
These calculate proportions and must use `round_float()`:

4. **backend/api/events/production/commons/job.py:49**
   ```python
   current_batch_total_value = self.job.active_batch_qt / self.job.qt_planned
   # Should be:
   current_batch_total_value = round_float(self.job.active_batch_qt / self.job.qt_planned)
   ```

5. **backend/api/events/production/commons/job.py:52**
   ```python
   step_progress_value = current_batch_total_value / steps_count
   # Should be:
   step_progress_value = round_float(current_batch_total_value / steps_count)
   ```

6. **backend/api/events/production/commons/job.py:54**
   ```python
   completed_qt_progress = self.job.qt_completed / self.job.qt_planned
   # Should be:
   completed_qt_progress = round_float(self.job.qt_completed / self.job.qt_planned)
   ```

7. **backend/api/events/wip/wip_booked.py:59**
   ```python
   booking_percentage = self.info.quantity / wip.quantity
   # Should be:
   booking_percentage = round_float(self.info.quantity / wip.quantity)
   ```

8. **backend/api/events/wip/wip_removed.py:39**
   ```python
   unbooking_percentage = self.info.quantity / wip.quantity
   # Should be:
   unbooking_percentage = round_float(self.info.quantity / wip.quantity)
   ```

9. **backend/api/events/wip/wip_unbooked.py:42**
   ```python
   unbooking_percentage = self.info.quantity / wip.quantity
   # Should be:
   unbooking_percentage = round_float(self.info.quantity / wip.quantity)
   ```

10. **backend/api/events/admin/time_override_requested.py:61**
    ```python
    batch_quota = b.qt_total / (self.job.qt_completed + self.job.active_batch_qt)
    # Should be:
    batch_quota = round_float(b.qt_total / (self.job.qt_completed + self.job.active_batch_qt))
    ```

11. **backend/api/events/admin/progress_override_requested.py:662**
    ```python
    quantity_ratio = batch.qt_pass / self.info.new_job_qt_completed
    # Should be:
    quantity_ratio = round_float(batch.qt_pass / self.info.new_job_qt_completed)
    ```

### Cost/Value Calculations
These calculate unit costs or values:

12. **backend/api/events/admin/base_admin.py:56**
    ```python
    new_value = round(current_wip.get('value', 0) * leftover_wip / current_wip['quantity'], 4)
    # Should be:
    new_value = round_float(current_wip.get('value', 0) * leftover_wip / current_wip['quantity'])
    # Note: This already uses round() with 4 decimals, but should use round_float() for consistency
    ```

13. **backend/api/events/admin/progress_override_requested.py:656**
    ```python
    average_hourly_cost = 0 if not canceled_work_sessions else sum(ws.hourly_cost or 0 for ws in canceled_work_sessions) / len(canceled_work_sessions)
    # Should be:
    average_hourly_cost = 0 if not canceled_work_sessions else round_float(sum(ws.hourly_cost or 0 for ws in canceled_work_sessions) / len(canceled_work_sessions))
    ```

### AQL Queries with Division
These are database queries with division - harder to fix:

14. **backend/api/events/admin/progress_override_requested.py:542**
    ```python
    # In AQL query:
    RETURN total_duration / b.qt_pass
    # Consider: Add rounding in Python after query execution, or use AQL ROUND() function
    ```

## Implementation Plan

1. Add `from utils.float_precision import round_float` to affected files (for float results only)
2. **For integer results**: Keep `round(... / ...)` - simpler and sufficient
3. **For float results**: Use `round_float(... / ...)` - provides 6-decimal precision control
4. Test each change to ensure behavior is preserved

## Files to Update

- backend/api/events/production/commons/job.py
- backend/api/events/production/batch_completed.py
- backend/api/events/admin/batch_canceled.py
- backend/api/events/admin/progress_override_requested.py
- backend/api/events/admin/time_override_requested.py
- backend/api/events/admin/base_admin.py
- backend/api/events/wip/wip_booked.py
- backend/api/events/wip/wip_removed.py
- backend/api/events/wip/wip_unbooked.py

## Verification

After updates, verify:
- Progress percentages display cleanly (no `.00000001` artifacts)
- Quantity ratios are rounded appropriately
- No business logic breaks (tolerance utilities handle comparison)
