# Requirements: Float Precision Fix

**Defined:** 2026-02-17
**Core Value:** Accurate, clean numeric data throughout the system — quantities, progress, and measurements display correctly to users without floating-point noise, and comparisons work reliably without epsilon drift errors.

## v1 Requirements

Requirements for fixing floating-point precision system-wide.

### Database Layer

- [ ] **DB-01**: Serializer in `backend/api/utils/db.py` rounds all float values to 6 decimal places before writing to ArangoDB
- [ ] **DB-02**: Rounding applies to all numeric fields system-wide (quantities, progress, durations, etc.)
- [ ] **DB-03**: Existing database records remain unchanged (new writes only)
- [ ] **DB-04**: Serializer handles nested floats in dictionaries and lists

### Business Logic Layer

- [ ] **LOGIC-01**: Utility function `float_equals(a, b, epsilon=1e-6)` created for tolerance-based equality checks
- [ ] **LOGIC-02**: Utility function `float_less_than(a, b, epsilon=1e-6)` created for tolerance-based less-than comparisons
- [ ] **LOGIC-03**: Utility function `float_greater_than(a, b, epsilon=1e-6)` created for tolerance-based greater-than comparisons
- [ ] **LOGIC-04**: Comparison utilities available as importable module in `backend/api/utils/float_precision.py`
- [ ] **LOGIC-05**: Event validation logic using float comparisons migrated to use tolerance utilities
- [ ] **LOGIC-06**: Inventory business logic (movements, counting) uses tolerance comparisons
- [ ] **LOGIC-07**: Production business logic (progress, consumption) uses tolerance comparisons

### UI Layer

- [ ] **UI-01**: Vue components displaying quantities format floats to max 6 decimals
- [ ] **UI-02**: Movement quantity displays show clean numbers (e.g., 100.0 not 100.000001)
- [ ] **UI-03**: Inventory available_quantity displays show clean numbers
- [ ] **UI-04**: Progress percentage displays show clean numbers
- [ ] **UI-05**: Work session duration displays show clean numbers
- [ ] **UI-06**: Batch completion quantity displays show clean numbers
- [ ] **UI-07**: Reusable Vue composable or filter created for float formatting (if not already exists)

### Utilities & Documentation

- [ ] **UTIL-01**: Helper function `round_float(value, decimals=6)` created for explicit rounding
- [ ] **UTIL-02**: Rounding strategy documented in code comments (db.py, float_precision.py)
- [ ] **UTIL-03**: Epsilon tolerance standard (1e-6) documented in float_precision.py module docstring

## v2 Requirements

Not currently planned, potential future enhancements.

(None identified)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Migrate to Decimal type | Too complex across Pydantic models, DB, frontend; float + rounding sufficient for manufacturing domain needs |
| Migrate existing database values | Leave historical data as-is; risk of breaking existing records outweighs benefit; fix going forward only |
| Change precision standard (6 decimals) | 6 decimals is industry standard for manufacturing quantities; not configurable to maintain consistency |
| Create automated test suite | No active test suite exists; focus on implementation only; manual verification sufficient |
| Monetary/currency fields with Decimal | Not in current scope; may revisit Decimal for true financial reconciliation in future if needed |
| Configurable epsilon per operation | Single tolerance (1e-6) matches 6 decimal precision; complexity not justified for current needs |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| (Populated during roadmap creation) | | |

**Coverage:**
- v1 requirements: 20 total
- Mapped to phases: 0 (pending roadmap)
- Unmapped: 20 ⚠️

---
*Requirements defined: 2026-02-17*
*Last updated: 2026-02-17 after initial definition*
