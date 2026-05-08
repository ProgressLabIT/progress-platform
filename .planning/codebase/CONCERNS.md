# Codebase Concerns

**Analysis Date:** 2026-05-08

## Tech Debt

### Bare Exception Handling in Endpoints (62 occurrences)

**Issue:** Bare `except:` clauses (exception type swallowing) scattered across `backend/api/endpoints/*.py`

**Files affected:**
- `auth.py` (4): lines 171, 213, 276, 371
- `org.py` (7): lines 129, 155, 262, 340, 384, 430, 464
- `config.py` (3): lines 45, 127, 181
- `counting.py` (8): lines 95, 121, 181, 266, 292, 355, 393, 419
- `form.py` (4): lines 60, 126, 156, 232
- `media.py` (1): line 38
- `serial.py` (1): line 363
- `print.py` (1): line 229
- `process.py` (1): line 123
- 15+ additional endpoint files with similar patterns

**Examples:**
- `backend/api/endpoints/auth.py:171-172` — bare `except:` swallows password verification errors; falls through to `raise auth.credentials_exception`
- `backend/api/endpoints/auth.py:213-214` — bare `except:` in `/whoami` endpoint wraps credential validation
- `backend/api/endpoints/counting.py:95-419` — multiple bare `except:` in counting session creation paths

**Impact:** Silent error swallowing masks root causes. Debugging network, database, or permission errors becomes adversarial — clients receive 400/401 without context. Production operational debugging relies on guesswork. Also catches `SystemExit` and `KeyboardInterrupt`, preventing clean shutdowns.

**Fix approach:** Audit 62 sites. Replace each with specific exception type (e.g., `except ValueError:`, `except DatabaseError:`, `except Exception as e:`). Log exceptions at WARN/ERROR level before re-raising or translating to HTTPException with descriptive detail. Create centralized FastAPI exception handler for consistent error responses.

**Priority:** MEDIUM — affects operational visibility; not blocking functionality.

---

### Debug Print Statements in Production Code (44 occurrences)

**Issue:** Direct `print()` calls in `backend/api/` code (should use `logging` module)

**Files affected:**
- `endpoints/process.py:246` — `print(f'WARNING: Could not delete media...')`
- `endpoints/product.py:47` — `print(params.model_dump())`
- `endpoints/traceability.py:87, 172, 185` — bare `print(e)` on exception
- `utils/auth.py:257, 261, 275, 279, 287` — print statements in token validation paths (6 occurrences)
- `utils/dhr.py:465, 758, 798, 805, 810, 978, 981, 994` — many `print(f"🔍 DEBUG: ...")` statements (14 occurrences)

**Impact:** Print statements bypass logging infrastructure. Cannot be silenced in production; clutter stdout/container logs. No structured log levels or filtering. Hard to trace which component emitted the message. Makes debugging harder, not easier.

**Fix approach:** Replace `print(x)` with `logger.debug(x)` or `logger.error(x)` depending on context. Preserve the emoji markers (`🔍`) in the log message for visibility; they're part of the diagnostic signal. Remove dead commented-out print statement at `dhr.py:994`.

**Priority:** LOW — code works; this is technical polish. Keep stable unless explicitly refactoring a module.

---

### Legacy Vuex Store Parallel with Pinia (Bifurcated State)

**Issue:** Two state management systems coexist. Legacy Vuex store at `webapps/main/src/store/` (14 files); newer Pinia stores at `webapps/main/src/stores/`.

**Files:**
- Legacy Vuex: `store/bom.js`, `store/form.js`, `store/job.js`, `store/org.js`, `store/process.js`, `store/product.js`, `store/quality.js`, `store/serial.js`, `store/session.js`, `store/traceability.js`, `store/user.js` (plus `__tests__/` and `store-flag.d.ts`)
- Pinia (new): `stores/` (use for new state only)

**Impact:** State mutations can happen via two different frameworks, making it unclear which is authoritative. Components may mix Vuex/Pinia dispatches. Dependency injection becomes confusing. Testing state becomes harder. Migration debt accumulates, especially as features grow and state complexity increases.

**Fix approach:** No immediate action needed. Do NOT add new modules to Vuex store. All new state management must use Pinia. Gradual migration of Vuex modules to Pinia during feature work on affected components (not a dedicated cleanup phase).

**Priority:** LOW — operational stability not affected; architectural cleanliness concern only.

---

### Options API Vue Components (Legacy — 40 components)

**Issue:** 40 components in `webapps/main/src/components/` still use Options API (`export default { ... }`); Composition API (`<script setup>`) is the standard for new code.

**Example files:** `BaseTooltipIcon.vue`, `JobCard.vue`, `JobTimer.vue`, `WorkOrderArchive.vue`, `ProductAside.vue`, `JobRebalanceActionCard.vue`, `BaseAutocompleteOperation.vue`, `IconLibrary.vue`, `BaseDialog.vue`, `BaseActionCard.vue`, and 30+ others.

**Impact:** Options API components are harder to refactor incrementally. Logic is scattered across hooks (mounted, computed, methods, watchers). New developers must learn two patterns. Testing is less straightforward. IDE support and type checking work better with Composition API.

**Fix approach:** Do NOT refactor existing Options API components. Use Composition API for all new components. Refactor to Composition API only during feature work on the affected component (not a dedicated cleanup phase).

**Priority:** LOW — no functional issue; style/maintainability concern only.

---

## Previously-Fragile Areas (Now Hardened)

### Cross-Metric Value Contamination during NDEATH (Phase 999.3 — Complete & UAT-Verified)

**Status:** FIXED and UAT-verified 2026-05-07. Now hardened with operator recovery recipe.

**What was happening:** Two independent bugs in `backend/sparkplug_bridge/main.py` produced persistent KV bucket contamination:
- **Stratum B:** 15 orphan edge-scope keys (Bug A)
- **Stratum A:** 6 cross-session alias-resolution collisions (Bug B)

**Root causes:**
1. **Bug A:** NBIRTH handler writing device metrics to edge-scope KV keys instead of device-scope (lines 183–192, pre-fix). Device metrics should only be written by DBIRTH.
2. **Bug B:** DDATA frames from prior sessions resolving aliases against the new session's alias map (lines 275–353), producing type/value mismatches and cross-metric contamination.

**Fix deployed:** Three atomic commits on `backend/sparkplug_bridge/main.py`:
1. **Commit `d5ec2016`** — NBIRTH edge-scope filter. Skip device-scope metrics; let DBIRTH own device state. Prevents new Stratum B orphans.
2. **Commit `f48a2a14`** — DDATA wire-vs-map datatype check at decode. Defensive residual layer for alias-only frames.
3. **Commit `2d2f412a`** — Queue-drain at NBIRTH receipt (`_drain_data_for()` helper). Drops in-flight prior-session frames before alias-map repopulation. Primary fix for Stratum A.

**Operator recovery recipe:** Published in `.planning/workstreams/sparkplug-demo/phases/999.3-cross-metric-value-contamination-during-ndeath/999.3-SUMMARY.md`:
- **Option A:** Blanket purge via `docker exec progress-broker-1 nats kv purge sparkplug_last_values` (safest; repopulates within ~10s)
- **Option B:** Targeted delete of 21 known contaminated keys (preserves other KV state)
- Pre-purge verify step: `docker exec progress-sparkplug_bridge-1 python -c "import backend.sparkplug_bridge.main as m; assert hasattr(m, '_drain_data_for'), 'fix not loaded'"`

**UAT verification (2026-05-07) — PASS:**
- Steady-state KV state post-purge: **19 legitimate keys** (2 edge `NodeControl/Rebirth` + 17 device-scope, all type-correct)
- Zero Stratum A residue (no cross-metric contamination)
- Zero Stratum B residue (no orphan edge-scope keys)
- No regression in live-tick path, edge status signaling (🟢↔🔴 flip), banner state management, or freshness placeholder
- Sim-kill repro: every metric retains last-good value with correct type

**Scope impact:** Phase 999.4 (per-device session tracking, Sparkplug B § 5.4 compliance) deferred post-fix. Not a blocker for v1.0 demo (May 15 deadline).

**Takeaway:** Bridge daemon is now protected against the identified ordering edge cases. Monitor for related bugs during May 14 dress rehearsal.

---

## Known Scope Gaps

### Per-Device Session Tracking (Sparkplug B § 5.4 Compliance) — Backlogged as Phase 999.4

**Issue:** Sparkplug B spec § 5.4 ("no up-cascade" rule) requires per-device alive-tracking at bridge state level. Current implementation tracks only edge-level NDEATH; device-level alive/dead transitions are not enforced.

**Surfaced:** UAT during Phase 999.3 closure (2026-05-07). Spec gap, not a regression.

**Files affected:** `backend/sparkplug_bridge/main.py` (session state model), page state model (Streamlit Sparkplug page), ADR-0002 KV schema.

**Impact:** Demo v1.0 does not strictly enforce per-device session boundaries per Sparkplug B § 5.4. Affects stricter compliance validators. Not demo-blocking (deadline 2026-05-15). Deferred to Phase 999.4.

**Spec reference:** Sparkplug B v3.0.0 § 5.4 "Device/Edge alive detection"; backlog entry committed in `4e9083e7`.

**Priority:** DEFERRED — post-demo scope; currently in backlog at `.planning/workstreams/sparkplug-demo/phases/999.4-per-device-session-tracking-sparkplug-b-5-4-compliance/`.

---

## Code Complexity Hotspots

### `backend/api/utils/dhr.py` (1,307 lines)

**What it is:** PDF generation and assembly for Digital History Records (DHR) — serial traceability documents with images, phase summaries, and company branding.

**Concerns:**
- Multiple nested HTML/PDF generation paths (WeasyPrint + ReportLab + PyPDF2 combinations)
- Heavy reliance on exception-swallowing within nested try/except blocks (lines 55–78 wrap file I/O in bare `except`)
- 14 embedded `print(f"🔍 DEBUG: ...")` statements for diagnostic output (lines 465, 758, 798, 805, 810, 978, 981, 994)
- Complex image attachment logic with per-phase pagination and file I/O
- No transaction boundary — partial failures leave incomplete PDFs

**Fragility:** WeasyPrint/ReportLab edge cases (font loading, image embedding, page breaks, MIME type handling) are notoriously brittle. Changes to the template structure require careful testing. Image file I/O failures during generation can corrupt the output.

**Mitigation:** Stable in production. If modifying, add integration test against a real PDF reader (not just generation success). Test with various image formats and sizes.

**Files:** `backend/api/utils/dhr.py` lines 1–1,307

---

### `backend/api/endpoints/production.py` (1,082 lines)

**What it is:** Production domain endpoints — job creation, batch transitions, step completions. Core event entry points for the critical event chain (StepCompleted → BatchCompleted → JobClosed).

**Concerns:**
- Large file concentrates business logic for production workflow
- Multiple nested AQL queries with complex state checks
- Critical path for WIP cascades and inventory movements
- 8 bare `except:` clauses (lines 123, etc.)
- TODO at line 112: "replace default alias with default operation"
- TODO at line 287: "ensure job_updates are coherent with the work order update"

**Test coverage:** Implicit in Phase 999.3 UAT (cross-metric contamination surfaced via simulator + chart visualization). No dedicated unit test file visible.

**Impact:** Bugs here affect production workflow state. Regressions caught late (QA/UAT phase).

**Files:** `backend/api/endpoints/production.py` lines 1–1,082

---

### `backend/api/endpoints/process.py` (922 lines)

**What it is:** Process/operation definition endpoints — phase templates, operation links, step definitions, print template management.

**Concerns:**
- 7 TODO comments indicating incomplete features or deliberate workarounds:
  - Line 25: TODO optimize queries
  - Line 321: TODO selective copy of print templates instead of all phases
  - Line 426: TODO copy phase print templates (when implemented)
- Template copy-on-edit logic with custom field propagation
- Media attachment cleanup on deletion (not transactional across batch operations; see media.py TODO at line 41)

**Files:** `backend/api/endpoints/process.py` lines 1–922

---

### `backend/api/events/admin/progress_override_requested.py` (681 lines)

**What it is:** Admin override event for forced state mutations (WIP adjustment, batch restart, job reset, progress correction).

**Concerns:**
- Complex state machine for reversing prior transactions
- Re-application of intermediate state changes requires careful ordering
- Line 365: TODO refactor to avoid code duplication (suggests duplicated logic across multiple override paths)

**Impact:** Used for operator recovery scenarios. Bugs here can corrupt WIP state across multiple batches and linked inventory movements.

**Files:** `backend/api/events/admin/progress_override_requested.py` lines 1–681

---

## Top TODO/FIXME Density

**Backend `backend/api/` TODOs (40+ comments across 25 files):**

| File | Line | Comment | Category |
|------|------|---------|----------|
| `endpoints/media.py` | 41 | orphaned media cron job + created_at expiry | Media cleanup |
| `endpoints/config.py` | 111 | re-order job queues when site management implemented | Config defaults |
| `endpoints/admin.py` | 67 | delete all files linked to StepExecutionData | Batch cleanup |
| `endpoints/admin.py` | 225 | use named graphs for auto-deletion | Data cleanup |
| `endpoints/process.py` | 25 | optimize queries | Query optimization |
| `endpoints/process.py` | 321 | selective copy of print templates to phases | Features deferred |
| `endpoints/process.py` | 426 | copy phase print templates (when implemented) | Features deferred |
| `endpoints/product.py` | 293, 367 | verify workorder/active item related | State validation |
| `endpoints/traceability.py` | 345 | update falsely closed work sessions | State validation |
| `endpoints/production.py` | 112, 287 | replace alias with operation; ensure job_updates coherent | Logic design |
| `utils/file.py` | 90, 91 | check folder exists; clean copy_path before copying | File operations |
| `utils/traceability.py` | 236 | update material cost calculation | Cost tracking |
| `utils/process.py` | 226 | copy phase print templates | Features deferred |
| `utils/inventory.py` | 349 | add filter by product tag | Query features |
| `models/event.py` | 101 | add WORK_ORDER_CANCELED to endpoint | Event implementation |
| `models/process.py` | 80, 91, 104, 109, 134, 135, 160 | model split; serialization warnings; denormalization cleanup | Model design |
| `models/inventory/movement.py` | 244 | enforce consistency at model or merge_references | Data consistency |
| `models/traceability.py` | 11 | TODO status enum value | Enum design |
| `events/work_session/work_session_created.py` | 46 | use JOB_PAUSED event to close other sessions | Event design |
| `events/admin/progress_override_requested.py` | 365 | refactor to avoid code duplication | Code cleanup |
| `events/admin/job_reset.py` | 174, 190 | use event to add wip | Event composition |
| `events/inventory/movement_updated.py` | 43 | consider multiple events to confirm movement | Event design |
| `events/inventory/movement_completed.py` | 154 | handle serial creation if product requires it | Features deferred |
| `events/production/active_batch_changed.py` | 127 | use named graph with auto deletion | Data consistency |
| `events/production/base_production.py` | 79 | add WORK_ORDER events; include in QUEUE_UPDATED | Event completeness |
| `events/production/commons/job.py` | 45 | use TraceabilityQueries.UPDATE_JOB_PROGRESS | Query optimization |

**Density:** ~1 TODO per ~650 lines of backend code. Most are incremental enhancements or deferred features, not critical bugs.

---

## Testing Gaps

### Frontend Component Tests Disconnected from CI

**Issue:** 13 component tests exist (`webapps/main/src/**/*.component.test.js`) but `yarn test` is a stub:
```json
"test": "echo \"No test specified\" && exit 0"
```

**Actual test runner:** `yarn test:components` runs `vitest --config vitest.component.config.js run`

**Impact:** CI pipelines may not be running component tests. Developers must remember to run `yarn test:components` manually. No automated catch for component regressions in CI.

**Test files present (13):**
- `webapps/main/src/composables/useSSE.composable.test.js`
- `webapps/main/src/stores/rightDrawer.component.test.js`
- `webapps/main/src/stores/userHub.component.test.js`
- `webapps/main/src/components/ProgressBtn.component.test.js`
- `webapps/main/src/components/AppNotificationBridge.component.test.js`
- 8 additional component test files

**Fix approach:** Update `webapps/main/package.json` to invoke `yarn test:components` instead of stub. Add to CI gate if CI exists.

**Files:**
- `webapps/main/package.json` (test script definition)
- `webapps/main/vitest.component.config.js` (test config)
- 13 test files in `webapps/main/src/**/*.component.test.js`

**Priority:** MEDIUM — affects test automation discipline.

---

### Backend Endpoint Tests Sparse

**No visible unit tests for `backend/api/endpoints/` directory.**

**Implicit coverage via:** Phase 999.3 UAT (manual visual repro); Sparkplug simulator integration (Phase 2 scope). No pytest fixtures or test discovery patterns visible in repo structure.

**Impact:** Regressions in endpoint logic caught late (QA / UAT phase). Critical event chain (StepCompleted → BatchCompleted → JobClosed) relies on manual testing.

**Fix approach:** Not in scope of current codebase map. Testing strategy documented in project CLAUDE.md (BDD specs-first, pytest + testcontainers for backend integration).

**Priority:** DEFERRED — architectural concern; product risk accepted in Phase 1–4 schedule. Post-v1.0 consideration.

---

## Security Considerations

### JWT Token Handling and Validation

**Area:** Authentication token lifecycle

**Current posture:** 
- JWT tokens issued via `backend/api/utils/auth.py::issue_token()` with `TokenContext.API` scope
- Token verification at endpoint level via FastAPI dependency `Depends(auth.verify_token)`
- Token stored in OAuth2 Bearer scheme (`Authorization: Bearer <jwt>`)
- Token secret stored in Docker secrets (`progress_jwt_secret`)

**Concerns:**
- Multiple bare `except:` in token validation (`auth.py:257, 261, 275, 279, 287`) mask validation failures — could hide attacks
- No visible token rotation or expiry refresh logic in code
- No visibility into key management strategy (HSM, rotation policy, secure storage)
- Print statements in auth validation paths (`auth.py:257–287`) may leak token debug info

**Current mitigation:** Token-dependent endpoints via FastAPI dependency injection; `/hello` endpoint is public (per CLAUDE.md).

**Recommendations:** 
1. Replace bare `except:` in `auth.py` with specific exception types to log token validation failures
2. Document token expiry + refresh strategy (likely implicit in FastAPI/JWT standards)
3. Add token revocation check if not already present
4. Replace print statements with logger calls in auth paths

**Files:** `backend/api/utils/auth.py` (483 lines)

**Priority:** LOW — token model is standard FastAPI/OAuth2; no known exploits.

---

### Media File Upload and Access Control

**Area:** File upload and retrieval

**Current posture:**
- Uploads via `endpoints/media.py::POST /media` (multipart form)
- Files stored in Docker volume `/media` (`PROGRESS_MEDIA_PATH`)
- Retrieval via FastAPI static file serving (`/media/{path}`)

**Concerns:**
- `media.py:38` has bare `except:` wrapping the POST handler (masks upload failures)
- No visible path traversal validation in upload handler
- Orphaned media cleanup not implemented (TODO at media.py:41 — can accumulate over time)

**Current mitigation:** File path constrained by ArangoDB document references (can only be accessed if linked to a valid document). Implicit org-scoping via queries filtering by org_id.

**Recommendations:** 
1. Audit path traversal guards in media.py::POST handler; validate `filename` parameter against allowed characters
2. Implement orphaned media cleanup as cron job (per TODO media.py:41; use `created_at` field as expiry reference)
3. Replace bare `except:` with specific exception logging

**Files:** 
- `backend/api/endpoints/media.py` (media upload/retrieval)
- `backend/api/utils/file.py` (file operations with TODOs at lines 90–91)

**Priority:** LOW — implicit constraint via document linking is reasonable for a private platform. Monitor for access control regressions during feature work.

---

## Performance Bottlenecks

### DHR PDF Generation (WeasyPrint-Heavy, Blocking)

**Problem:** `dhr.py` orchestrates complex HTML → PDF conversions using WeasyPrint (CPU-intensive HTML rendering) + ReportLab (lower-level PDF). Image processing is synchronous and blocking on uvicorn event loop.

**Files:** `backend/api/utils/dhr.py` lines 19–1,307

**Cause:** No async I/O for image I/O or PDF generation. Blocking operations on the uvicorn event loop prevent other requests from being processed.

**Current behavior:** Endpoints calling DHR generation (e.g., serial download, DHR print) block the worker for duration of PDF generation. Under high concurrency or with large image attachments, can cause request timeouts.

**Improvement path:** 
1. Extract DHR generation to a Celery/RQ background task queue (if feasible within project infra)
2. Or: offload image I/O to a separate thread pool via `asyncio.run_in_executor()`
3. Or: switch to a faster PDF library (e.g., FPDF2 for simple documents; keep WeasyPrint for complex templates)

**Scale impact:** Single-digit PDF generation requests block the API. High contention under load. Not an issue at v1.0 usage levels (demo scope); becomes visible at scale.

**Priority:** MEDIUM — affects user experience if DHR generation is frequent. Post-v1.0 optimization.

---

### AQL Query Performance (TODO at endpoints/process.py:25)

**Problem:** `endpoints/process.py:25` marked with TODO: optimize queries

**Files:** 
- `backend/api/endpoints/process.py` (922 lines, multiple nested AQL queries)
- `backend/api/utils/production.py` (604 lines, complex query building)

**Current state:** Complex AQL queries with multiple nested LET clauses; no visible index strategy or query plan analysis in code.

**Improvement path:** 
1. Profile query execution times using ArangoDB profiler
2. Add indexes on frequently-filtered fields (state, org_id, product_key, created_at)
3. Consider materialized views or denormalized caches for complex lookups

**Priority:** MEDIUM — not urgent; becomes visible under load. Background optimization.

---

## Fragile Areas

### Sparkplug Bridge State Machine (`backend/sparkplug_bridge/`)

**Files:** 
- `backend/sparkplug_bridge/main.py` (33.3K, message handler + queue worker)
- `backend/sparkplug_bridge/session_state.py` (7.4K, state machine functions)
- `backend/sparkplug_bridge/kv_store.py` (4.6K, NATS KV operations)

**Why fragile:**
- NATS KV bucket serves as distributed state store for device sessions + last values
- State transitions triggered by MQTT message ordering (race conditions possible under QoS=1 + broker reorders)
- Bug A + Bug B (Phase 999.3) demonstrates how subtle ordering bugs leak across session boundaries
- Single asyncio worker (`_queue_worker`) — no parallelism; queue-drain logic depends on sequential processing

**Safe modification strategy:**
1. Add exhaustive inline comments documenting state machine invariants (pre-fix, post-fix)
2. Test changes against `simulator/` scenario with synthetic reorder cues (like `request_reorder_for_next_birth()`)
3. Verify KV bucket contents after each state transition (sample script provided in 999.3-SUMMARY.md § Verify)
4. Run Phase 3 + Phase 4 verification runbooks before deployment

**Test coverage:** Integration test against simulator (Phase 2 scope); UAT verified Phase 999.3. No unit tests visible.

**Priority:** MEDIUM — hardened by Phase 999.3 fix; monitor for edge cases during rehearsal (May 14). Before any changes to main.py, re-run `03-VERIFICATION-RUNBOOK.md` to confirm no regression.

---

### Admin Override Event (`backend/api/events/admin/progress_override_requested.py`)

**Files:** `backend/api/events/admin/progress_override_requested.py` (681 lines)

**Why fragile:**
- Reverses prior state mutations (WIP adjustments, batch restarts, job resets)
- Re-applies intermediate job state changes in specific order
- Line 365 marked TODO: refactor to avoid duplication (suggests duplicated logic across multiple override paths)
- Logic is hard to follow; easy to miss a side effect or dependency

**Safe modification strategy:**
1. Add detailed comments before each state mutation explaining the invariant being restored
2. Write a test matrix covering all override scenarios (job in each possible state, with/without children, with/without linked batches)
3. Dry-run against test DB before production use

**Test coverage:** Implicit (operator use only); no visible unit test.

**Priority:** MEDIUM — used only for operator recovery. Outages are low-frequency; high-severity when they occur. Test before deploying changes.

---

## Dependencies at Risk

### ArangoDB Python Client (`python-arango==8.*`)

**Risk:** Major version 8 is locked; upstream updates are non-breaking within v8. No visible upgrade path to v9 (if available).

**Current use:** All database queries via `utils/db.py` singleton at `backend/api/utils/db.py`.

**Impact:** Security patches within v8 range are captured; major version migration not planned. Dependency is stable and well-maintained.

**Recommendation:** Monitor `python-arango` releases. Plan upgrade to v9 if/when it adds critical features or security fixes. Document breaking changes before upgrade.

**Files:** 
- `backend/api/requirements.txt` (dependency declaration)
- `backend/api/utils/db.py` (usage)

---

### WeasyPrint (66.x) + ReportLab (4.x)

**Risk:** Both are PDF generation libraries with active development. WeasyPrint is especially sensitive to OS-level dependencies (Pango, cairo for font rendering).

**Current use:** DHR PDF generation (`utils/dhr.py`), sensitive data (traceability documents).

**Impact:** PDF generation failures are user-visible (can't generate traceability documents). Dependency hell in Docker image builds (Pango, cairo library versions).

**Mitigation:** Pinned versions in Dockerfile; use official `python:3.11-slim` base image. Dockerfile maintained at `backend/api/Dockerfile`.

**Recommendation:** Monitor for security updates to OS-level dependencies (Pango, cairo). Test DHR generation in CI before merge. Consider lighter-weight PDF library if performance becomes an issue.

---

## Architectural Constraints & Known Limitations

### Event Transaction Atomicity Boundary

**Constraint:** All DB mutations occur within `Event.save()` transaction scope. Fails ⇒ entire transaction aborts.

**Known limitation:** NATS publishing (KV updates, message publishing) is non-transactional (decoupled from DB transaction). Event semantics are "all-or-nothing" for DB; post_processing() side effects are not guaranteed to be visible on failure.

**Implication:** If DB commit succeeds but NATS publish fails, clients may not be notified of state changes immediately. Next poll/refresh will sync.

**Files:** `backend/api/events/base_event.py` (transaction management)

---

### Single-Threaded Event Loop (Bridge)

**Constraint:** Sparkplug bridge uses single asyncio worker (`_queue_worker` in main.py).

**Implication:** No parallelism. Queue depth limited to 256 (drop-oldest). High ingestion spikes may drop frames.

**Safe because:** Sparkplug MQTT QoS=1 ensures at-least-once delivery. Dropped frames are eventually retransmitted on reconnect.

**Scaling path:** Multi-worker pool if needed (not v1 demo scope; possible v2 optimization).

---

### Global Singletons (Managers)

**Files:** `backend/api/managers/` — NotificationManager, WebSocketManager, KafkaConsumerManager (if present)

**Pattern:** Managers use getInstance() pattern; initialized once on startup; closed on shutdown.

**Risk:** State shared across requests. Any race condition in manager logic affects all clients.

**Mitigation:** Managers are async-safe (use asyncio.Queue, nats-py client); no visible locks or shared mutable state beyond thread-safe queue abstractions.

---

## Summary Risk Matrix

| Category | Severity | Frequency | Effort to Fix | Priority |
|----------|----------|-----------|---------------|----------|
| Bare exception handling (62 sites) | LOW | High (every error) | HIGH (tedious audit + test) | MEDIUM |
| Print statements (44 sites) | LOW | High (dev/debug) | MEDIUM (mechanical replace) | LOW |
| Legacy Vuex + Pinia split | LOW | MEDIUM (new features) | MEDIUM (gradual migration) | LOW |
| Options API components (40) | LOW | MEDIUM (new components) | MEDIUM (gradual conversion) | LOW |
| Sparkplug bridge fragility | MEDIUM | LOW (edge cases) | MEDIUM (testing + comments) | MEDIUM |
| Admin override event fragility | MEDIUM | LOW (operator only) | MEDIUM (testing + comments) | MEDIUM |
| DHR PDF generation performance | MEDIUM | LOW (DHR infrequent) | HIGH (rearchitect) | MEDIUM |
| AQL query optimization (TODO) | MEDIUM | LOW (background) | HIGH (profiling + indexing) | MEDIUM |
| Frontend test automation gap | LOW | HIGH (every commit) | LOW (update yarn test) | MEDIUM |
| Per-device session tracking (spec gap) | MEDIUM | DEFERRED | LOW (Phase 999.4 scoped) | DEFERRED |

---

*Concerns audit: 2026-05-08*
