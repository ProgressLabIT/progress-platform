# Phase 2: Business Logic Migration - Research

**Phase Goal**: Business logic comparisons use tolerance-based equality instead of raw float comparison

**Requirements**: LOGIC-05, LOGIC-06, LOGIC-07

## Research Findings

### Float Comparison Sites Identified

Searched the codebase for float-to-float comparisons that could suffer from epsilon precision issues. Found **10 high-priority locations** where quantities, progress, or values are compared directly.

### Categories of Comparisons

#### 1. Quantity Comparisons (WIP Events)
**Pattern**: Checking if requested quantity meets/exceeds available WIP
- `wip_booked.py:47` - `if self.info.quantity >= wip.quantity`
- `wip_unbooked.py:31` - `if self.info.quantity >= wip.quantity`
- `wip_removed.py:32` - `if self.info.quantity >= wip.quantity`

**Risk**: Off-by-epsilon could cause partial bookings when full booking intended, or vice versa.

#### 2. Completion Checks (Production)
**Pattern**: Checking if job/movement is complete
- `production.py:277` - `if job.qt_completed >= job.qt_planned`
- `production.py:782` - `if new_job_data.qt_completed >= new_job_data.qt_planned`
- `movement_updated.py:46,75` - `if self.info.qt_confirmed >= self.info.qt_planned`

**Risk**: Job might not close properly if `qt_completed` is `99.999999` and `qt_planned` is `100.0`.

#### 3. Validation Checks
**Pattern**: Ensuring quantities are within bounds
- `movement_reversed.py:186` - `if quantity_to_revert > movement.qt_confirmed`
- `movement.py:113` - `abs(self.qt_planned) > 1` (serial movement validation)
- `progress_override_requested.py:174` - `abs(quantity_change) > free_wip_qt_downstream`

**Risk**: Validation could incorrectly pass/fail due to precision noise.

### Zero Comparisons (Low Risk)

Found many `== 0` and `> 0` comparisons:
- `quantity == 0` - Safe (exact comparison)
- `quantity > 0` - Safe (zero is exact)

**Decision**: Leave these unchanged. Comparing to zero doesn't have precision issues.

### Threshold Comparisons (Medium Risk)

Progress-related thresholds:
- Progress percentage checks (if implemented in business logic)
- Cost/value thresholds

**Note**: Most progress calculations already use `round()` after our Phase 1 work, reducing risk.

## Migration Strategy

### Approach

Replace direct float comparisons with tolerance-based utilities:

**Before**:
```python
if job.qt_completed >= job.qt_planned:
    # Close job
```

**After**:
```python
from utils.float_precision import float_greater_than, float_equals

if float_equals(job.qt_completed, job.qt_planned) or float_greater_than(job.qt_completed, job.qt_planned):
    # Close job

# Or more concisely:
if not float_less_than(job.qt_completed, job.qt_planned):
    # Close job
```

### Helper Function Considerations

Could create convenience wrappers:
```python
def float_gte(a, b, epsilon=1e-6):
    """Greater than or equal with tolerance"""
    return float_greater_than(a, b, epsilon) or float_equals(a, b, epsilon)

def float_lte(a, b, epsilon=1e-6):
    """Less than or equal with tolerance"""
    return float_less_than(a, b, epsilon) or float_equals(a, b, epsilon)
```

## Impact Assessment

### High Impact (Must Fix)
- Completion checks (production.py, movement_updated.py)
- WIP booking comparisons (wip_booked, wip_unbooked, wip_removed)

### Medium Impact (Should Fix)
- Validation checks (movement_reversed, progress_override_requested)

### Low Impact (Optional)
- Model validators (already use Pydantic validators from Phase 1)
- Zero comparisons (no precision issues)

## Files to Update

1. `backend/api/events/wip/wip_booked.py` - 1 comparison
2. `backend/api/events/wip/wip_unbooked.py` - 1 comparison
3. `backend/api/events/wip/wip_removed.py` - 1 comparison
4. `backend/api/events/inventory/movement_updated.py` - 2 comparisons
5. `backend/api/events/inventory/movement_reversed.py` - 1 comparison
6. `backend/api/events/admin/progress_override_requested.py` - 1 comparison
7. `backend/api/endpoints/production.py` - 2 comparisons
8. `backend/api/models/inventory/movement.py` - 1 comparison (validator)

**Total**: 8 files, 10 comparison sites

## Recommendations

### 1. Add Convenience Functions
Create `float_gte()` and `float_lte()` in `float_precision.py` to avoid verbose `or` chains.

### 2. Conservative Migration
Start with high-impact sites (completion checks, WIP bookings). These directly affect business logic.

### 3. Testing Strategy
- Unit test each migrated comparison
- Integration test job completion workflows
- Test WIP booking/unbooking edge cases

### 4. Documentation
Update inline comments explaining why tolerance comparison is needed for each site.

## Open Questions

1. **Should we migrate model validators?**
   - Movement.py line 113 is in a Pydantic validator
   - Already has Phase 1 field validators for rounding
   - Comparison might be redundant

2. **Epsilon value**:
   - Default 1e-6 matches our 6-decimal standard
   - Any sites need different epsilon?
   - Probably not - manufacturing domain is uniform

3. **Backwards compatibility**:
   - Will changing comparison logic affect existing workflows?
   - Unlikely - we're making comparisons MORE forgiving, not stricter
   - But should test edge cases

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Comparison sites identified | High | Comprehensive grep search |
| Impact assessment | High | Clear business logic patterns |
| Migration approach | High | Straightforward utility substitution |
| Risk of breakage | Low | Making comparisons more tolerant |

---

**Research complete**. Ready for planning phase.
