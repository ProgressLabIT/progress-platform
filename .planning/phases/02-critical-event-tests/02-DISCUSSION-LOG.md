# Phase 2: Critical Event Test Suites - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-10
**Phase:** 02-critical-event-tests
**Areas discussed:** Event instantiation, Cascade assertions, Parametrize matrix, Plan splitting

---

## Event Instantiation

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, event.save(db) | Seed via factories, call event.save(db) directly, assert on collection documents. Keeps API and direct layers cleanly separated by assertion surface. | ✓ |
| API-only, skip direct layer | Only test through httpx endpoints. Simpler but loses cascade branch coverage for edge cases. | |

**User's choice:** Direct event.save(db) with real ArangoDB
**Notes:** Aligns with project constraint #4 (no DB mocks). Pattern: seed → save → assert on collections.

---

## Cascade Assertions

| Option | Description | Selected |
|--------|-------------|----------|
| Parent state + event log | Assert BatchCompleted's own changes (batch status, work session closed, job progress) + query Event collection to verify each expected child event was recorded. Don't duplicate child event DB assertions. | ✓ |
| Full cascade assertion | Assert every child event's DB side effects (WIP edges, inventory movements, serial records). Maximum confidence but high maintenance and duplicates child suites. | |
| Parent only, trust children | Only assert BatchCompleted's direct state changes. Rely on child event suites for cascade correctness. | |

**User's choice:** Parent state + event log verification
**Notes:** Query Event collection for child event types. MovementCompleted has its own suite in this phase.

---

## Parametrize Matrix

| Option | Description | Selected |
|--------|-------------|----------|
| Curated ~16 tests | Pairwise coverage of cascade flags, 2 isolated step_check tests. Update BATCH-20 success criterion to reflect actual count. Comment block documents excluded combos. | ✓ |
| Full 32, mark no-ops | Run all 32 combinations. Mark impossible combos with xfail(strict=False). Satisfies literal criterion but adds CI overhead. | |

**User's choice:** Curated ~16 pairwise tests
**Notes:** auto_new_batch + last_batch is no-op. step_check is orthogonal to cascade flags. Update BATCH-20 criterion.

---

## Plan Splitting

| Option | Description | Selected |
|--------|-------------|----------|
| 5 plans, split BATCH | STEP → BATCH HTTP API → BATCH direct event → PROG → MOVE. Each under ~17 req. | |
| 4 plans, one per event | STEP → BATCH → PROG → MOVE. Simpler but BATCH at 21 req risks executor exhaustion. | |
| 6 plans, split BATCH + MOVE | Also split MOVE into movement-types and movement-API. More granular. | ✓ |

**User's choice:** 6 plans — split both BATCH and MOVE
**Notes:** STEP(8), BATCH-http(~10), BATCH-direct(~11), PROG(17), MOVE-types(~10), MOVE-api(~6)

---

## Claude's Discretion

- Test helper organization (shared vs inline assertions)
- Exact BATCH requirement-to-plan mapping
- Fixture composition strategy for complex preconditions

## Deferred Ideas

None — discussion stayed within phase scope
