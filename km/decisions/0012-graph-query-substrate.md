# 0012 — Graph queries stay in the database; in-memory rejected as primary substrate

**Status:** discussion
**Date:** 2026-05-21
**Audience:** platform (cross-cutting — affects how every graph-traversing endpoint is implemented)
**Related:**
- [ADR-0011](0011-database-substrate.md) — the substrate decision this ADR pairs with (PostgreSQL + AGE or CTEs)
- `km/strategy/defense-aerospace-roadmap.md`
- `km/strategy/arangodb-migration.md`

> **Cross-cutting note.** Same as ADR-0011 — numbered in the
> sparkplug-demo workstream sequence because that's where active ADRs
> live, but the decision is platform-level.

## Context

ADR-0011 commits to migrating the operational DB substrate from
ArangoDB to PostgreSQL, with graph traversals executed either by
Apache AGE (Cypher) or by recursive CTEs + path arrays. During the
analysis that led to ADR-0011, a third option surfaced repeatedly:
**run graph traversals in-memory** using a Python graph library
(NetworkX, or its Rust-backed sibling rustworkx), with the database
holding only edge / vertex storage.

This ADR records the analysis and **rejects in-memory as the primary
graph-query substrate**, while preserving it as an *allowed future
optimisation* for specific bounded sub-domains.

The decision matters now (rather than as an ad-hoc judgement later)
because:

- The Stage 1 migration plan (ADR-0011) determines how `backend/api/utils/bom.py`,
  `serial.py`, `inventory.py` get rewritten. If in-memory were the
  intended target, the migration shape would differ.
- The defense prospect's CISO will ask about consistency, audit, and
  threat-surface implications of any cache layer between system of
  record and query result. The rejection rationale needs to be
  documented, not improvised.

## The five critical patterns and their in-memory fit

From `arangodb-migration.md`. Domain knowledge of the underlying data
volumes added:

| Pattern | Data nature | Realistic edge count | In-memory fit |
|---|---|---|---|
| BOM loop detection (`CHECK_BOM_LOOP`) | Master data, slow-changing | 10k–100k edges per plant | Good |
| Position hierarchy (warehouse → bin) | Facility topology, rare changes | ~10k positions even for large facilities | Good |
| Serial root ancestor (`GET_SERIAL_ROOT_ANCESTOR`) | Transactional `contains` history | Grows linearly with throughput — 1000 units/day × 10 components × 5 years ≈ **18M edges** | Bad — does not fit at production scale |
| Serial children with PRUNE | Same data as above | Same | Bad |
| Bidirectional serial hierarchy | Same data | Same | Bad |

The "good fit" cases (BOM, positions) are bounded master/facility
data. The "bad fit" cases (3 of 5, and by weight the majority of
production query traffic) scale linearly with manufacturing throughput
and are not viable in-memory at any reasonable RAM budget.

So in-memory is at best a *hybrid* substrate, not a wholesale
replacement.

## Failure modes (the meat of the rejection)

Listed roughly in order of severity for our specific deployment
profile.

### 1. Consistency loss for transactional traversals

Database recursive-CTE traversals run inside the calling transaction's
MVCC snapshot. They see exactly the state the rest of the transaction
sees.

In-memory traversal runs against a snapshot loaded at some earlier
point. Concurrent writes between cache load and traversal completion
are invisible. For BOM cycle detection inside a BOM-edit transaction:
two concurrent edits both reading the same pre-merge snapshot would
both pass cycle check and both commit, yielding a cycle that the
in-DB check would have caught.

For an AS9100D-certified manufacturer, "occasionally inconsistent
traceability answers" is an 8.5.2 finding. For a defense customer
under NIST 800-171 AU-family controls, it's worse — the audit trail
itself becomes unreliable.

### 2. Multi-worker cache invalidation

FastAPI runs with multiple uvicorn workers. Each worker would hold an
independent in-memory graph. Writes need to invalidate all workers'
caches via a side channel (NATS pub/sub would work, and is already in
the stack). Adds versioning, stale-snapshot detection, partial-reload
strategy. We would be reinventing a distributed cache layer that the
DB engine provides for free.

### 3. Cold-start latency / restart loops

After process restart, the first request that needs the graph pays a
full-load cost. For 100k edges in rustworkx that's hundreds of
milliseconds; for 18M edges (serial hierarchy), tens of seconds to a
minute — long enough to trigger Kubernetes liveness-probe restarts in
a loop. Mitigations exist (lazy load, snapshot files, pre-warm) but
each is additional code that the DB engine already wrote.

### 4. Memory pressure has a cliff, not a slope

DBs degrade gracefully under data growth — slower queries, more I/O.
In-memory crashes when RAM runs out. On a defense site this is an
incident-level event. We would need explicit per-graph memory budgets,
eviction policies, monitoring, and pre-OOM alerting — none of which we
otherwise need.

### 5. Audit-trail gap

DB queries surface in DB logs, slow-query logs, and (with `pgAudit`)
structured audit events. NIST 800-171 AU-2 / AU-3 evidence is
straightforward.

In-memory traversals do not appear in any DB log. We would need to own
the audit instrumentation at the traversal layer, sampled to the
audit pipeline, with documented mapping to the DB snapshot the
traversal ran against. More work to satisfy the same control.

### 6. Threat-surface expansion

A new component (in-process cache + NATS invalidation channel +
snapshot loader) becomes something a pen-tester scopes against and
the customer's CISO asks about. Cost is real even if the exploit
surface is small.

### 7. Hidden coupling for transactional operations

Some graph traversals run inside the `Event.save()` transaction chain
(`pre_processing()` / `apply()` in `backend/api/events/`). Pulling
those out of the DB transaction means the traversal reads
potentially-stale state and then the event commits against the DB.
Race window between the two is small but real. DB-internal recursive
CTE in the same transaction has none of this.

### 8. Testing burden

The existing testcontainers + pytest setup handles DB-backed
correctness adequately. In-memory adds cache-invalidation races,
partial-reload scenarios, memory-exhaustion fallback, worker-to-worker
consistency, version skew during rolling deploys. Significantly more
failure modes to cover, harder to reproduce deterministically.

### 9. Observability and debugging asymmetry

DB slow query → query plan, indexes, EXPLAIN ANALYZE. Mature tooling.
In-memory slow / wrong → ad-hoc tooling we own end-to-end.

### 10. Doesn't avoid the migration

Even a hybrid that pushed BOM + positions in-memory would still need
to migrate the rest of the data model + the transactional graph
traversals to the new DB substrate. In-memory adds a parallel system
*on top of* the migration, not instead of it.

## Where in-memory genuinely wins (and is therefore permitted)

Being honest about the upside so the door stays open for the right
cases:

- **Graph algorithms beyond traversal** — PageRank on supplier
  network, community detection on co-occurring serials, shortest-path
  with edge weights, constraint satisfaction. Real NetworkX /
  rustworkx strengths. None are in the current critical-query list,
  but may appear in future analytics / OEE / quality-root-cause
  workloads.
- **Heavy graph analytics for reporting** — rebuild on a schedule,
  query thousands of times against the rebuild. Cache-friendly,
  consistency-tolerant.
- **What-if simulation** — "if we change supplier X, which products
  are affected" — read-only, transient, no consistency concern.
- **Bounded master-data caches as perf optimisations** — BOM cycle
  detection on a hot cache rebuilt on every BOM-change event, with
  the DB-internal recursive CTE as the source of truth and the cache
  as a read-through accelerator. Only if measured Postgres CTE perf
  is genuinely too slow under production load.

## Decision

1. **Primary graph-query substrate is the database** (PostgreSQL with
   either Apache AGE or recursive CTEs, as decided by the
   ADR-0011 spike).
2. **In-memory graph libraries (rustworkx preferred over NetworkX)
   are permitted only as bounded, scoped optimisations**, on top of a
   DB system-of-record, in the following situations:
   - Graph algorithms beyond simple traversal (PageRank, community
     detection, weighted shortest path) where no DB-side equivalent
     exists.
   - Analytics / reporting workloads that tolerate eventual
     consistency and rebuild on a schedule.
   - Read-through caches for bounded master-data graphs (BOM,
     positions), **introduced only after** measured DB-side
     performance is shown to be a real production constraint, not a
     theoretical one. Cache layer must:
     - Document its consistency model in writing (snapshot age,
       rebuild trigger, stale-read behaviour).
     - Provide explicit memory budgets + pre-OOM alerting.
     - Expose audit-grade structured logging for every cache-served
       traversal, mapped to the source-of-truth snapshot.
     - Pass a threat-model update with the security-ADR review chain.

In short: **the DB is the system of record. Anything in-memory is a
documented optimisation, not a substitute.**

## Consequences

**Positive:**

- The defense prospect's CISO question "how does your in-memory cache
  stay consistent with the system of record" gets the simple answer:
  "we don't have one in the hot path." Audit and threat-model stories
  are simpler by one component.
- Migration shape (ADR-0011) stays focused on substrate replacement,
  without a parallel "design the cache layer" workstream.
- Performance optimisation remains an option for the future, with a
  documented gate to prevent ad-hoc cache layers sneaking in.

**Negative:**

- Some graph queries that *could* be elegant in-memory will remain
  expressed in SQL recursive CTEs and may be more verbose / less
  readable. Acceptable trade for the consistency and audit
  guarantees.
- If Postgres-side graph performance turns out to be a genuine
  constraint in Stage 1 production, we will have a more-painful
  optimisation cycle than if we had built caching primitives from
  the start. Mitigated by the ADR-0011 spike, which is supposed to
  catch this case before commitment.

## Open questions

- Does any future workload (eval / analytics / what-if simulation)
  already on the roadmap warrant an in-memory analytics pipeline from
  the start? If yes, that pipeline should be ADR'd separately rather
  than smuggled into Stage 1.
- Do we want to standardise on rustworkx now (so when an in-memory
  case does land, library choice is pre-decided), or defer? Lean:
  defer until the first concrete case justifies the choice.

## References

- ADR-0011 — Database substrate
- `km/strategy/defense-aerospace-roadmap.md`
- `km/strategy/arangodb-migration.md`
- `backend/api/utils/bom.py`, `backend/api/utils/serial.py`, `backend/api/utils/inventory.py`
- rustworkx: https://www.rustworkx.org/
- NetworkX: https://networkx.org/
