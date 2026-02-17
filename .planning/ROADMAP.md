# Roadmap: Float Precision Fix

**Created:** 2026-02-17
**Depth:** Quick
**Phases:** 3
**Coverage:** 20/20 v1 requirements mapped

## Phases

- [x] **Phase 1: Precision Foundation** - Serializer rounding, comparison utilities, and helper functions
- [x] **Phase 2: Business Logic Migration** - Migrate float comparisons in events and domain logic to tolerance utilities
- [ ] **Phase 3: Frontend Display Cleanup** - Clean numeric formatting across all Vue components

## Phase Details

### Phase 1: Precision Foundation
**Goal**: System has the core tools to write clean floats and compare them reliably
**Depends on**: Nothing (first phase)
**Requirements**: DB-01, DB-02, DB-03, DB-04, LOGIC-01, LOGIC-02, LOGIC-03, LOGIC-04, UTIL-01, UTIL-02, UTIL-03
**Success Criteria** (what must be TRUE):
  1. Any float written to ArangoDB via the serializer is rounded to 6 decimal places (e.g., writing 1/3 stores 0.333333, not 0.3333333333333333)
  2. Nested float values inside dicts and lists are also rounded when serialized
  3. Existing database records are not modified by any migration or batch process
  4. Developers can import `float_equals`, `float_less_than`, `float_greater_than`, and `round_float` from a single utility module
  5. Module docstrings and code comments document the 6-decimal / 1e-6 epsilon standard

**Plans:** 2 plans in 1 wave

Plans:
- [ ] 01-01-PLAN.md — Float precision utilities (config + comparison functions)
- [ ] 01-02-PLAN.md — Database serializer rounding (modify encoder with recursive rounding)

### Phase 2: Business Logic Migration
**Goal**: Business logic comparisons use tolerance-based equality instead of raw float comparison
**Depends on**: Phase 1
**Requirements**: LOGIC-05, LOGIC-06, LOGIC-07
**Success Criteria** (what must be TRUE):
  1. Event validation logic that compares float values (progress thresholds, quantity checks) uses tolerance utilities instead of == or < operators on floats
  2. Inventory operations (movements, counting reconciliation) use tolerance comparisons so that quantities like 99.999999 and 100.0 are treated as equal
  3. Production logic (progress completion checks, consumption quantity validation) uses tolerance comparisons so off-by-epsilon values do not block operations

**Plans:** 3 plans in 2 waves

Plans:
- [x] 02-01-PLAN.md — Add convenience comparison functions (float_gte, float_lte)
- [x] 02-02-PLAN.md — Migrate WIP event comparisons (wip_booked, wip_unbooked, wip_removed)
- [x] 02-03-PLAN.md — Migrate production & inventory comparisons (endpoints, events)

### Phase 3: Frontend Display Cleanup
**Goal**: Users see clean, readable numbers everywhere in the UI
**Depends on**: Phase 1 (serializer ensures new data is clean); Phase 2 (business logic handles edge cases)
**Requirements**: UI-01, UI-02, UI-03, UI-04, UI-05, UI-06, UI-07
**Success Criteria** (what must be TRUE):
  1. Movement quantity displays show round numbers (e.g., "100" or "100.5", not "100.000001")
  2. Inventory available_quantity and progress percentages display without trailing noise digits
  3. Work session durations and batch completion quantities display cleanly
  4. A reusable Vue composable or filter is available for consistent float formatting across components

**Plans:** 3 plans in 2 waves

Plans:
- [ ] 03-01-PLAN.md — Create global float formatting utility ($formatFloat)
- [ ] 03-02-PLAN.md — Migrate production component displays (JobCard, ProgressBtn, etc.)
- [ ] 03-03-PLAN.md — Migrate warehouse component displays (movements, inventory)

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Precision Foundation | 2/2 | ✅ Complete | 2026-02-17 |
| 2. Business Logic Migration | 3/3 | ✅ Complete | 2026-02-17 |
| 3. Frontend Display Cleanup | 0/3 | Planning complete | - |

---
*Roadmap created: 2026-02-17*
*Last updated: 2026-02-17 (Phases 1-2 complete, Phase 3 planning complete)*
