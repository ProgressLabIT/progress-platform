# Progress Platform

Manufacturing Operations Management for discrete manufacturing — event-sourced, on-premise, single-tenant. Production tracking, inventory, traceability, quality. **FastAPI + ArangoDB + Vue 3/Quasar + NATS JetStream + Prefect 3.**

Canonical repo: GitLab (`progresslab/progress-platform`). GitHub is a **read-only mirror** for OSS visibility — direct PRs cannot be merged there.

## Active Milestone

**v1.0 Sparkplug B Demo — May 15, 2026.** Live MQTT Sparkplug B → bridge → NATS → Progress pipeline + UNS browser + Timescale history + threshold-triggered Issue automation. ADRs in `km/decisions/` (0001–0013). Demo scope/status docs remain on the retired `GSD` branch (e.g. `git show GSD:.planning/workstreams/sparkplug-demo/STATE.md`).

## Commands

**Backend tests** (pytest + testcontainers, ArangoDB spun up per-run — never mocked):
```bash
cd testing/pytest && uv sync && uv run pytest                  # full integration suite
cd testing/pytest && uv run pytest tests/unit/                 # pure-Python only, no Docker (~4s)
```

`tests/unit/` is reserved for pure-Python tests that do NOT touch ArangoDB / NATS / event-class chains — its conftest overrides the repo-root autouse fixtures with no-ops. Anything that needs a `db` parameter belongs under `tests/integration/` (or a sibling domain dir), not `tests/unit/`. See `testing/pytest/README.md` for the full subtree map and the macOS `DOCKER_HOST` gotcha.

**Webapp dev (main desktop SPA):**
```bash
cd webapps/main && yarn && yarn dev      # quasar dev server
yarn lint && yarn format                  # eslint + prettier
```

**Warehouse mobile app:** same pattern under `webapps/warehouse/`.

**Local Progress stack** (api/db/broker/historian/webapp — all-in-one on dev host): `docker compose -f deploy/compose/base.yaml -f deploy/compose/dev.yaml up`.

**Sparkplug local edge stack** (bridge + sim only, points at a remote Progress server per `deploy/compose/.env`): `docker compose -f deploy/compose/sparkplug.yaml up -d`. Topology revised 2026-05-11: cloud Progress + local Mac bridge/sim. Kill switch is Docker Desktop's stop button, or `.env` edit + `up -d --force-recreate sparkplug_bridge`.

**Install (user-facing 5-min path, locked from rehearsal):** see `readme.md` `## Try it in 5 minutes`.

## Architecture (1-paragraph)

Event-sourced backend (`backend/api/`): FastAPI endpoints instantiate **immutable Event objects** (`backend/api/events/`, 50+ types) which mutate state inside an ArangoDB transaction (`Event.save()` → `pre_processing()` → `apply()` → `store_event()` → commit/abort). Side effects (notifications, downstream domain events) flow through Managers (`backend/api/managers/`) and **NATS JetStream** — *not* Kafka, despite stale references elsewhere. Frontends are Quasar 2 / Vue 3 SPAs (`webapps/main/` desktop, `webapps/warehouse/` Capacitor mobile). Workflows on Prefect 3 (`backend/workflow/`). Demo-only code (HMIs, simulators, seeders, Streamlit reports) lives in `demos/`, **not** `backend/` — `backend/` holds shippable services only; all orchestration (incl. demo compose stacks) stays in `deploy/`. See [ADR-0018](km/decisions/0018-demos-dir-and-backend-service-layout.md).

Full layer map: `.planning/codebase/STACK.md` and `.planning/codebase/ARCHITECTURE.md` (regenerable via `/gsd-map-codebase`; current copies still mention Kafka in places — historical drift, NATS is canonical).

## Knowledge Graph

`graphify-out/GRAPH_REPORT.md` exists (6148 nodes, 656 communities). For codebase questions — especially Sparkplug, Events, NATS, or cross-domain flows — prefer `/graphify` over raw `grep` first. Community hubs include `Sparkplug Bridge Main`, `Event Apply Pattern`, `Event Bus & NATS Client`, `Production Events`, `Inventory Movement Events`.

## Conventions (project-specific)

**Backend (Python 3.11):** snake_case files/functions, PascalCase Pydantic models, one endpoint file per domain in `backend/api/endpoints/`. Pydantic v2 for all boundary validation. Use `logging` — never `print()` (legacy `print()` exists; do not add more). Avoid bare `except:` (legacy issue; new code catches specifically).

**Frontend (Vue 3):** PascalCase `.vue` components, Composition API + `<script setup>` for new code (Options API legacy — leave unless touching). **Pinia for new state** (`webapps/main/src/stores/`); legacy Vuex (`webapps/main/src/store/`) is read-only. API calls via store actions or composables, not direct in components. Always add i18n strings to `src/i18n/` when adding user-facing text.

**Event logging (frontend):** `sendEvent()` from `webapps/main/src/composables/event.js`.

## NATS

Project messaging is **NATS** (JetStream + KV). Two skills available globally:
- `nats:python` — nats-py SDK patterns (pub/sub, request/reply, JS, KV)
- `nats:general` — concept reference

Subject taxonomy is locked per ADR `km/decisions/0002-nats-subject-taxonomy.md`. Sparkplug↔NATS subject mapping: `km/decisions/0008-natsmqtt-subject-mapping.md`.

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.

## Workstream Workflow

### Decision Records

Architecture Decision Records live in **`km/decisions/`** on `DEV` — one project-level, globally-numbered ledger (`NNNN-kebab-title.md`), code-tracked so every worktree inherits it at fork and it survives squash-to-DEV. Index + conventions: `km/decisions/index.md`. Status pipeline: `discussion → decided → implemented → superseded`.

A worktree may keep purely feature-internal decisions in its own `.planning/`; anything touching a cross-worktree contract (NATS subject taxonomy, event/data schema, API shape, config-file shape) belongs in the shared `km/decisions/` ledger. When a decision affects such a contract, its ADR must reach `decided` before implementation begins on the affected files — this is what lets multiple worktrees fork against frozen contracts.

## Branching & Integration

`DEV` is the trunk and the GitLab → GitHub mirror source. (`master` is a dead 2022 branch — ignore it.) Each feature is developed in its own git worktree off `DEV`, carrying its own GSD `.planning/` project (worktree-as-project).

**Before committing, run `git branch --show-current` and follow the regime for that branch** — the session may start anywhere, so don't assume:
- **On `DEV` directly:** small, self-contained fixes may land as a single atomic commit. Stage only that fix's files — never `git add -A` while unrelated changes are pending. (This still goes through `/gsd-quick`.)
- **On a `feature/<name>` worktree branch:** accumulate WIP atoms, then squash to `DEV` per the rules below.

### Worktree convention

Worktrees live under `.worktrees/` (gitignored), each on a `feature/<short-name>` branch with a defined file-ownership scope to avoid merge collisions. The workstream's `PROJECT.md` records the per-session file-ownership map.

A session that needs to deviate from its phase plan or the locked ADR contracts must stop and surface the deviation to the orchestrator (the user, or the lead session) — AGENTS.md's "explain first, change after" stance, within an approved plan. Conflicts are resolved against the locked ADRs, not session-local preference.

### Squashing to DEV

**Always squash related changes into ship-grained commits on `DEV`** — aggregate by feature / phase / fix scope, not by individual file edits.

- Do NOT cherry-pick a feature branch's atomic commits one-by-one — DEV's history is for ship-grained units, not WIP atoms.
- Prefer a 3-way `git merge --squash <feature>` so DEV-side fixes are preserved, then `git reset` and commit by scope. Avoid `git checkout <feature> -- <paths>`, which silently reverts any file where DEV is ahead of the feature branch.
- Exclude `.planning/` from DEV — planning artifacts stay on the feature branch. After a squash merge, `git checkout HEAD -- .planning` restores DEV's own planning state and drops the feature's.
- Compare with the two-dot diff (`git diff DEV <feature>`) for the true net delta — the three-dot `DEV...<feature>` over-counts content DEV already has via shared history.
- Commit message: short title + bullet body documenting what shipped. Reference "Squashed from N atomic commits" if N > 5.
- Atomic commits remain on the feature branch for forensics (review, bisect, undo); DEV stays clean.

**Multiple parallel sessions:** each session commits its worktree branch end-of-day; the orchestrator merges them with `git merge --no-ff` into a short-lived per-feature/milestone parent branch (`ms/<name>`, off `DEV` — not a perpetual shared branch). That parent is then squashed to `DEV` per the rules above and retired.

> Legacy: the long-lived `GSD` branch was the old single-track integration branch (pre-worktree model). Retained as an archived ref for the v1.0 sparkplug milestone's atomic history, no longer the active integration target.

**Why:** DEV drives the GitLab → GitHub mirror. GitHub viewers (and Dependabot, GitHub Releases auto-changelogs, anyone reading `git log DEV`) see one commit per shipped unit, not 30 micro-commits.

## Behavioral

- Do not add Claude as co-author of commits.
- Solo-maintainer project: no SLAs, no triage scaffolding, prefer toggles over commitments.
- See `AGENTS.md` for the "explain first, change after" stance on multi-line edits.
- Developer profile lives in global `~/.claude/CLAUDE.md` — not duplicated here.
- Always check the /km folder for knowledge about architecture, patterns, etc. before searching autonomously
- Whenever you find new information about platform architecture, design choices, patterns, quirks, risks, that were not present in the km, notify th euser and propose an update, adding/amending content in the most appropriate document or creating a new one if necessary.
