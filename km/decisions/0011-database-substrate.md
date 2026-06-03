# 0011 — Database substrate: migrate from ArangoDB to PostgreSQL

**Status:** discussion
**Date:** 2026-05-21
**Audience:** platform (cross-cutting — affects every backend service that touches the DB)
**Related:**
- [ADR-0005](0005-timescale-schema-and-downsampling.md) — Timescale on Postgres for historian; this ADR extends that consolidation to the operational DB
- `km/strategy/defense-aerospace-roadmap.md` — the prospect-prep document that surfaced this decision
- `km/strategy/arangodb-migration.md` — existing migration analysis (predates the defense lens; needs the version-cutoff fix noted below)

> **Cross-cutting note.** This ADR is numbered in continuation of the
> sparkplug-demo workstream because that's where active ADRs live, but
> the decision is **platform-level**, not sparkplug-specific. When the
> defense-readiness workstream is formally created it should adopt this
> ADR as its anchor; the file path may move at that point.

## Context

The platform runs on **ArangoDB**. The codebase relies on ArangoDB's
multi-model semantics — document collections for all entities (50+ event
types, products, jobs, serials, positions, etc.) and edge collections
plus AQL traversals for genealogy, BOM cycle detection, position
hierarchies, and WIP flow. The `arangodb-migration.md` survey documents
~5 critical graph queries, ~8 moderate ones, and 50+ document/simple
queries.

Two converging pressures force a substrate decision now:

1. **License + lifecycle.** ArangoDB 3.11.x is the last Apache 2.0
   series; 3.12 (released ~Q2 2024) switched to BSL 1.1. We are pinned
   on 3.11 to stay on OSI-approved OSS, but 3.11 is end-of-maintenance
   upstream — **no security patches**. NIST 800-171 SI-2 ("Identify,
   report, and correct system flaws") and CMMC L2 SI.L2-3.14.1 become
   automatic findings the moment a defense auditor reads the version
   string. The conversion-to-Apache-2.0 clause on 3.12+ doesn't fire
   until ~2028 and running a 4-year-stale CVE-vulnerable DB is itself
   a finding.

2. **Defense / aerospace prospect.** Per `km/strategy/defense-aerospace-roadmap.md`,
   a Canadian HQ group serving DoD and NASA, with EU VP lead, is in the
   near-term pipeline. Their procurement chain will surface BSL-1.1
   bans and EOL-version bans. The current ArangoDB posture does not
   pass that filter; the prior CTO roadmap's "Stage 2: ArangoDB cluster
   mode" line is a paper architecture under these constraints (cluster
   on 3.11 Community lacks encryption-at-rest, audit log, hot-backup,
   DC2DC — all Enterprise features).

Additional fact to fold into `arangodb-migration.md`: it says BSL
started at 3.10 (late 2022). Public record is that **3.12 (~April 2024)
was the first BSL release**; 3.11.x is the last Apache 2.0 series. The
analysis doc needs that fact-fix before being quoted externally.

## Decision drivers

In priority order:

1. **License must be OSI-approved Apache 2.0 / PostgreSQL License /
   equivalent.** No BSL, no SSPL. GPL acceptable only if it does not
   create derivative-work obligations on Progress Platform itself.
2. **Active security patching.** Vendor / community must ship CVE
   remediation on a documented cadence. EOL substrates are
   non-starters.
3. **Production-grade HA available in OSS.** On-prem clustering with
   automatic failover, streaming replication, and immutable-backup
   integration must work without commercial-Enterprise licensing.
4. **Defense procurement signal.** Substrate should not introduce
   geopolitical or governance flags (Section 889, FAR 52.204-25,
   uncertain post-acquisition stewardship).
5. **Operational footprint.** Prefer minimising the number of new
   components a customer's CISO must threat-model and a customer's DBA
   team must operate.
6. **Stack consolidation with TimescaleDB.** ADR-0005 already places
   the historian on Postgres + Timescale. A second Postgres-family
   engine for operational data collapses two engines into one
   operational discipline.
7. **Migration cost.** Lower is better, but is secondary to the above
   — a cheap migration to a substrate that fails (1)–(4) is a wasted
   migration.

## Considered options

Filtered to OSI-approved + actively maintained + plausibly multi-model
at production scale. Rejection rationale captured for the others.

### Rejected at the filter

| Candidate | Rejection rationale |
|---|---|
| ArangoDB 3.11 status quo | EOL — no patches; fails (2) outright. Cluster Community lacks encryption-at-rest / audit log. |
| ArangoDB 3.12+ Community | BSL 1.1 — fails (1) at procurement. Still missing Enterprise features. |
| ArangoDB Enterprise | Commercial licensing reintroduces vendor lock-in and per-node cost; cannot anchor OSS positioning. Worth revisiting only if a single customer fully funds it. |
| SurrealDB / MemGraph / CockroachDB | BSL 1.1 — same licensing problem. |
| MongoDB | SSPL — not OSI-approved; explicit bans in many defense procurement frameworks. |
| Neo4j Community | GPLv3 + clustering is Enterprise-only — fails (3). |
| EdgeDB / Gel | Company folded into Vercel 2025; governance / longevity risk. |
| OrientDB | Apache 2.0 but effectively abandoned post-SAP. Ecosystem decayed. |
| NebulaGraph | Apache 2.0 and technically strong, but Vesoft is China-based. Section 889 / FAR 52.204-25 discussions are political capital we'd rather not spend with this specific prospect. Also no native document model. |
| Dgraph | Apache 2.0 core, but Hypermode acquisition (2024) created governance uncertainty. Schema-first GraphQL is a deeper rewrite than alternatives. |
| TerminusDB | Apache 2.0, interesting "git for data" model, but weak clustering and small community create their own supply-chain-risk findings. |
| YugabyteDB + AGE | Apache 2.0 substrate but AGE-on-Yugabyte not battle-tested at scale. Do not volunteer to be the proof point on a defense deployment. |

### Considered seriously

#### Option A — PostgreSQL + Apache AGE (or recursive CTEs)

- License: PostgreSQL License + Apache 2.0 (AGE).
- HA: Patroni + etcd + streaming replication + pgBackRest + WAL-G to immutable storage. Best-in-class OSS HA story.
- Multi-model: documents via `JSONB`; graph via Apache AGE (Cypher subset) or via recursive CTEs + path arrays for the 5 critical patterns.
- Defense procurement: universally accepted; existing customer-side DBA familiarity.
- Stack consolidation: extends ADR-0005's Timescale-on-Postgres decision to the operational DB. One engine, two extensions.
- Migration cost: 13–18 weeks engineering per `arangodb-migration.md` (1 senior engineer); calendar ~5 months at solo+partner staffing.
- Risk: AGE itself is the only newer component — 1.5.x line. Mitigation: spike (see below) confirms whether AGE is required or whether recursive CTEs alone are sufficient for the 5 critical patterns.

#### Option B — JanusGraph on Cassandra / ScyllaDB

- License: Apache 2.0 (JanusGraph + backends).
- HA: inherits backend's HA (Cassandra: strong).
- Multi-model: graph-native; documents would require a separate engine or awkward Cassandra-as-JSON-store.
- Defense procurement: acceptable; some primes already run Cassandra.
- Stack expansion: backend + Elasticsearch (for indexes) + JVM tuning — operational footprint 3–4× a Postgres deployment.
- Migration cost: 5–8 months — full data-model rewrite; Gremlin queries are a deeper rewrite than AQL → Cypher.

## Decision

**Primary substrate: PostgreSQL + Apache AGE (path-finally-confirmed by
spike) or recursive CTEs (if spike rejects AGE).**

Reasons (mapped to decision drivers):

| Driver | Why Postgres wins |
|---|---|
| (1) License | PostgreSQL License + Apache 2.0 — clean. |
| (2) Patching | Major versions supported 5 years; minor patches monthly. |
| (3) HA in OSS | Patroni + etcd + pgBackRest is the canonical OSS HA topology. |
| (4) Defense signal | Universal acceptance. No geopolitical or governance flag. |
| (5) Ops footprint | Smallest of the viable options. One engine, two extensions. |
| (6) Consolidation | Folds into ADR-0005's Timescale decision. Same engine. |
| (7) Migration cost | Highest of the viable cheap options, but bounded — 5 months calendar. |

**Documented contingency: JanusGraph + Cassandra/ScyllaDB.** Surfaces
only if the Stage 0.5 spike or early Stage 1 production data shows
Postgres graph queries cannot meet performance requirements. Naming the
contingency in the ADR has a side benefit for the prospect conversation:
it shows the OSS graph landscape was scanned, not skipped.

### Stage 0.5 — Substrate validation spike (1 week)

Blocking the Stage 1 migration kickoff. Scope:

1. Stand up a PostgreSQL 16 + Apache AGE 1.5.x environment.
2. Implement each of the 5 critical patterns from `arangodb-migration.md`
   (BOM loop, serial root, PRUNE traversal, position hierarchy,
   bidirectional serial hierarchy) **twice**: once in AGE Cypher,
   once in recursive CTE + path arrays.
3. Load representative data volumes (estimate from production AS9100D
   customer data — anonymised sample). For serial hierarchy, target
   the realistic ceiling: ~1M edges minimum, ideally 10M to validate
   the heavy case.
4. Measure: latency (p50/p95/p99), correctness vs current AQL output,
   plan stability, query-author ergonomics.
5. Decide between AGE and CTE-only. Document in this ADR's
   "Implementation notes" section before status flips to `decided`.

If both AGE and CTE-only fail the perf bar on the heavy case at
representative scale, escalate to the JanusGraph contingency (a longer
spike, ~3 weeks, before commitment).

### Migration shape (Stage 1)

Per `arangodb-migration.md` § "If BSL is Unacceptable", adapted:

1. **Preparation (4 wks)** — Data-access-layer abstraction introduced
   in `backend/api/utils/` and adopters refactored to go through it.
   Cutover becomes a config flip.
2. **Core migration (8 wks)** — Schema, queries (critical → moderate →
   simple), driver swap (`python-arango` → `psycopg` + `agensgraph` /
   `psycopg-pool`).
3. **Validation (4 wks)** — Parallel run on staging; data-consistency
   verification against the existing ArangoDB instance; performance
   benchmark vs current production traces.
4. **Cutover (2 wks)** — Final delta replication, traffic flip, soak.

Total ~18 weeks engineering / ~5 months calendar at current staffing.

### What this ADR does NOT decide

- Existing customer migration cadence (whether AS9100D customers
  currently on ArangoDB get migrated in lockstep or via a dual-DB
  transition period). Surfaces in a follow-up ADR once the spike
  result is known.
- Encryption-at-rest implementation (LUKS vs Cybertec TDE vs Percona
  TDE). Stage 2/3 decision.
- Audit logging configuration (`pgAudit` scope, log shipping format).
  Stage 1 implementation detail.
- Full-text / search-view migration (ArangoSearch → `pg_trgm` +
  `tsvector` + optionally `pgvector`). Mostly mechanical; tracked in
  the migration plan, not this ADR.

## Consequences

**Positive:**

- Substrate ceases to be a Stage 2 paper architecture and becomes a
  Stage 1 deliverable backed by a credible HA topology.
- Defense prospect's procurement chain has nothing to flag on the DB
  axis.
- Stack consolidates around Postgres (operational + historian + future
  search/vector). One engine, one DBA discipline.
- Apache 2.0 ambitions remain intact through the substrate boundary.

**Negative:**

- ~5 months of calendar effort that is not feature work.
- Data-access-layer abstraction adds a temporary indirection; some
  query sites will be uglier during the transition window.
- AGE maturity risk concentrated in one extension on otherwise
  battle-tested substrate. Mitigated by the spike + CTE fallback.
- Migration window introduces parallel-run cost (two databases running
  concurrently for the validation phase).

**Risks / open questions for resolution before `decided`:**

- Confirm 3.12 (not 3.10) is the BSL cutoff; correct
  `arangodb-migration.md` accordingly.
- Confirm AGE 1.5.x's behaviour on the PRUNE-equivalent traversal —
  this is the pattern most likely to surface AGE bugs.
- Sanity-check Patroni + etcd footprint with a defense-deployment lens
  (some sites have strict requirements on consensus-cluster placement).
- Decide on the data-access-layer abstraction shape — repository
  pattern vs. thin adapter, before the spike informs the choice too
  heavily.

## References

- `km/strategy/defense-aerospace-roadmap.md`
- `km/strategy/arangodb-migration.md` (requires fact-fix on 3.10 vs 3.12)
- ADR-0005 — Timescale schema and downsampling (Postgres consolidation)
- `backend/api/utils/bom.py`, `backend/api/utils/serial.py`, `backend/api/utils/inventory.py` — the four files hosting the critical AQL queries
- Apache AGE: https://age.apache.org/
- Patroni: https://github.com/patroni/patroni
- pgBackRest: https://pgbackrest.org/
