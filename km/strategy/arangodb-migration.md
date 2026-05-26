# ArangoDB Migration Analysis

> **Status:** Exploratory  
> **Last Updated:** May 2026  
> **Context:** ArangoDB switched to Business Source License (BSL 1.1) starting with version 3.10.x (late 2022)

## Executive Summary

This document evaluates options for potentially migrating away from ArangoDB due to licensing concerns. After analyzing our codebase, we identified **several complex graph patterns** that would require significant effort to migrate, while the majority of our queries are document-based and would port easily to PostgreSQL.

**Key Finding:** BSL 1.1 only restricts offering ArangoDB as a database-as-a-service to third parties. For self-hosted deployments and on-premises software sales, the license does not impose restrictions. A migration should only be pursued if BSL is genuinely incompatible with our business model.

---

## Current ArangoDB Usage

### Graph Collections (Edge Collections)
- `requires` - Product → Phase, Phase → Operation, BOM lines
- `contains` - Serial component hierarchy (parent-child relationships)
- `is_in_position` - Inventory position tree (warehouse locations)
- `issue_rel` - Issues linked to Work Orders, Jobs, Products, Serials
- `task_rel` - Tasks linked to various entities
- `wip` - Work-in-progress flow between phases
- `batch_serial` - Batch → Serial relationships
- `can_use_print_template` - Phases/Steps → Print Templates

### Query Complexity Distribution

| Complexity | Count | Description |
|------------|-------|-------------|
| 🔴 Critical | 4-5 | Cycle detection, variable-depth traversal with PRUNE, root finding |
| 🟡 Moderate | 6-8 | Fixed-depth traversals, bidirectional queries, path extraction |
| 🟢 Simple | 50+ | Document lookups, aggregations, single-hop relationships |

---

## Critical Graph Patterns

### 1. BOM Loop Detection (`CHECK_BOM_LOOP`)
**File:** `backend/api/utils/bom.py`

```aql
FOR v, e, p in 1..30 OUTBOUND start requires
FILTER e._to == start  -- Edge returns to origin = cycle detected
LET loop = (
    FOR item in p.vertices
    FILTER IS_SAME_COLLECTION(Product, item)
    RETURN item.code
)
RETURN loop
```

**Purpose:** Prevents circular dependencies in Bill of Materials  
**Migration Difficulty:** HIGH - Cycle detection with path extraction is non-trivial in SQL

---

### 2. Serial Root Ancestor (`GET_SERIAL_ROOT_ANCESTOR`)
**File:** `backend/api/utils/serial.py`

```aql
FOR v, e, p IN 0..999 INBOUND @serial_id contains
FILTER v.deleted == false && e.replaced == false
SORT length(p.vertices) DESC
RETURN p.vertices[-1]
```

**Purpose:** Find the top-level parent serial in a component hierarchy  
**Migration Difficulty:** HIGH - Requires tracking path length during recursion

---

### 3. Serial Children with PRUNE (`GET_SERIAL_CHILDREN`)
**File:** `backend/api/utils/serial.py`

```aql
FOR v, e IN 1..999 OUTBOUND start contains
PRUNE e.replaced == true || e.confirmed == false
```

**Purpose:** Get all descendants, stopping traversal on replaced/unconfirmed branches  
**Migration Difficulty:** HIGH - SQL CTEs don't have native PRUNE semantics

---

### 4. Position/Inventory Hierarchies
**File:** `backend/api/utils/inventory.py`

Multiple queries traverse the position tree (warehouse → zone → rack → shelf → bin):
- `SEARCH_POSITIONS` - Find positions within hierarchy
- `GET_POSITION_HIERARCHY` - Get full ancestor/descendant tree
- `SEARCH_INVENTORY_GRAPH` - Find inventory with path information
- `SEARCH_MOVEMENTS` - Filter movements by position subtrees

**Migration Difficulty:** MEDIUM - Tree structures are well-supported by recursive CTEs, but path manipulation adds complexity

---

### 5. Serial Hierarchy (Bidirectional)
**File:** `backend/api/utils/serial.py`

```aql
FOR v, e IN 0..9999 ANY start contains OPTIONS { uniqueVertices: "path" }
```

**Purpose:** Get entire component tree (both parents and children)  
**Migration Difficulty:** MEDIUM - Two CTEs with UNION

---

## Alternative Database Options Evaluated

### PostgreSQL + Apache AGE
**License:** Apache 2.0 ✅

| Aspect | Assessment |
|--------|------------|
| Graph queries | Cypher language, handles traversals well |
| Cycle detection | Supported natively |
| Variable depth | Supported |
| PRUNE equivalent | Partial (requires careful query design) |
| Maturity | Active development, growing community |
| Migration effort | HIGH - Query rewrite required |

**Verdict:** Best open-source option if migration is necessary

---

### PostgreSQL with Recursive CTEs (No Extensions)
**License:** PostgreSQL License ✅

| Aspect | Assessment |
|--------|------------|
| Graph queries | Verbose but functional |
| Cycle detection | Possible with path arrays |
| Variable depth | Supported |
| PRUNE equivalent | Not native, requires workarounds |
| Maturity | Battle-tested |
| Migration effort | VERY HIGH - Significant query complexity |

**Verdict:** Feasible but queries become unwieldy for complex patterns

---

### SurrealDB
**License:** BSL 1.1 ⚠️ (Same issue as ArangoDB)

| Aspect | Assessment |
|--------|------------|
| Graph queries | Arrow syntax, intuitive |
| Multi-model | Document + Graph + Time-series |
| Maturity | Young (2022), still stabilizing |

**Verdict:** Same licensing concern, doesn't solve the problem

---

### EdgeDB / Gel
**License:** Apache 2.0 ✅ (but...)

| Aspect | Assessment |
|--------|------------|
| Graph queries | Elegant path expressions |
| Built on | PostgreSQL |
| Status | ⚠️ Company shut down, joined Vercel (2025) |

**Verdict:** Not recommended - uncertain future without commercial backing

---

### Neo4j Community Edition
**License:** GPL v3 ⚠️

| Aspect | Assessment |
|--------|------------|
| Graph queries | Cypher (industry standard) |
| Maturity | Very mature |
| Constraint | GPL requires open-sourcing derivative works |

**Verdict:** GPL may be more restrictive than BSL for commercial software

---

## Migration Effort Estimate

### If Migrating to PostgreSQL + Apache AGE

| Component | Effort | Notes |
|-----------|--------|-------|
| Schema design | 2-3 weeks | Design relational + graph hybrid |
| Critical queries (5) | 3-4 weeks | BOM loops, serial hierarchy, positions |
| Moderate queries (8) | 2 weeks | Fixed-depth traversals |
| Simple queries (50+) | 3-4 weeks | Mostly mechanical translation |
| Driver/ORM changes | 1-2 weeks | Replace python-arango |
| Testing & validation | 2-3 weeks | Data integrity verification |
| **Total estimate** | **13-18 weeks** | 1 senior engineer |

### Risk Factors
- Performance regression on deep traversals
- Edge cases in cycle detection
- Data migration complexity (ArangoDB → PostgreSQL)
- Learning curve for Apache AGE

---

## BSL License Clarification

### What BSL 1.1 Restricts
> You may not provide the Licensed Work to third parties as a hosted or managed service, where the service provides users with access to any substantial set of the features or functionality of the Licensed Work.

### What BSL 1.1 Allows
- ✅ Self-hosted deployments for internal use
- ✅ On-premises software sold to customers
- ✅ SaaS products where the database is an implementation detail (not the product)
- ✅ Development, testing, evaluation

### Conversion to Open Source
BSL automatically converts to Apache 2.0 after 4 years:
- ArangoDB 3.10 (released late 2022) → Apache 2.0 in late 2026
- ArangoDB 3.11+ → Apache 2.0 in 2027+

**⚠️ Warning:** Running 4-year-old database versions is not viable due to:
- Security vulnerabilities (unpatched CVEs)
- Driver compatibility issues
- No bug fixes or performance improvements
- Documentation and community support decay

---

## Recommendations

### If BSL is Acceptable
**Recommendation:** Continue using ArangoDB

- Our use case (self-hosted MOM system) is permitted under BSL
- ArangoDB handles our graph patterns excellently
- No migration effort required
- Focus engineering time on product features

### If BSL is Unacceptable

**Recommendation:** Migrate to PostgreSQL + Apache AGE

1. **Phase 1 - Preparation (4 weeks)**
   - Set up Apache AGE development environment
   - Prototype critical queries in Cypher
   - Design hybrid schema

2. **Phase 2 - Core Migration (8 weeks)**
   - Implement data access layer abstraction
   - Migrate critical graph queries
   - Migrate document queries to SQL

3. **Phase 3 - Validation (4 weeks)**
   - Parallel running (both databases)
   - Data consistency verification
   - Performance benchmarking

4. **Phase 4 - Cutover (2 weeks)**
   - Final data migration
   - Switch production traffic
   - Monitor and stabilize

---

## Decision Criteria Checklist

Before deciding to migrate, confirm:

- [ ] BSL actually blocks our intended use (hosting as DBaaS)
- [ ] Migration cost is justified vs. commercial ArangoDB license
- [ ] Team has capacity for 4-5 month migration project
- [ ] Acceptable performance regression risk for graph queries
- [ ] Apache AGE maturity is sufficient for production use

---

## References

- [ArangoDB BSL License FAQ](https://www.arangodb.com/bsl-faq/)
- [Apache AGE Documentation](https://age.apache.org/)
- [BSL License Text](https://mariadb.com/bsl11/)
- Internal: `backend/api/utils/bom.py`, `serial.py`, `inventory.py`
