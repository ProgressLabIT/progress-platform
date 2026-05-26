# Progress Platform

Manufacturing Operations Management for discrete manufacturing — event-sourced, on-premise, single-tenant. Production tracking, inventory, traceability, quality. **FastAPI + ArangoDB + Vue 3/Quasar + NATS JetStream + Prefect 3.**

Canonical repo: GitLab (`progresslab/progress-platform`). GitHub is a **read-only mirror** for OSS visibility — direct PRs cannot be merged there.

## Active Milestone

**v1.0 Sparkplug B Demo — May 15, 2026.** Live MQTT Sparkplug B → bridge → NATS → Progress pipeline + UNS browser + Timescale history + threshold-triggered Issue automation. Status + scope: `.planning/workstreams/sparkplug-demo/STATE.md`, `ROADMAP.md`, `REQUIREMENTS.md`. ADRs in `decisions/`.

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

Event-sourced backend (`backend/api/`): FastAPI endpoints instantiate **immutable Event objects** (`backend/api/events/`, 50+ types) which mutate state inside an ArangoDB transaction (`Event.save()` → `pre_processing()` → `apply()` → `store_event()` → commit/abort). Side effects (notifications, downstream domain events) flow through Managers (`backend/api/managers/`) and **NATS JetStream** — *not* Kafka, despite stale references elsewhere. Frontends are Quasar 2 / Vue 3 SPAs (`webapps/main/` desktop, `webapps/warehouse/` Capacitor mobile). Workflows on Prefect 3 (`backend/workflow/`).

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

Subject taxonomy is locked per ADR `.planning/workstreams/sparkplug-demo/decisions/0002-nats-subject-taxonomy.md`. Sparkplug↔NATS subject mapping: ADR 0008.

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.

## Workstream Workflow

### Decision Records

Workstreams under `.planning/workstreams/<name>/` may include a `decisions/` folder holding ADR-style records that capture cross-phase decisions and trade-offs ahead of, alongside, or after `/gsd-plan-phase` outputs. They complement GSD artifacts; they do not bypass GSD execution.

Filename convention: `NNNN-kebab-title.md`. Status pipeline: `discussion → decided → implemented → superseded`. The workstream's `decisions/index.md` lists them in creation order.

When a decision affects file structure or cross-session contracts (NATS subject taxonomy, data schema, API shape, config-file shape), the corresponding ADR must reach `decided` status before implementation work begins on the affected files. This is what allows multiple sessions to fork against frozen contracts.

### Parallel Worktree Convention

For workstreams that run multiple AI coding sessions in parallel, use git worktrees under `.worktrees/` (gitignored). Each session works on a `feature/<short-name>` branch with a defined file-ownership scope to avoid merge collisions. The workstream's `PROJECT.md` records the per-session file-ownership map.

A session that needs to deviate from its workstream phase plan or the locked ADR contracts must stop and surface the deviation back to the orchestrator (the user, or the lead session). This preserves AGENTS.md's "explain first, change after" stance while permitting autonomous execution within an approved plan.

Daily integration cadence: each session commits its branch end-of-day; the orchestrator runs a `git merge --no-ff` round into the feature's short-lived parent branch (a per-feature/milestone branch off `DEV` — e.g. `ms/<name>` — not a perpetual shared branch). Conflicts are resolved against the locked ADRs, not session-local preference.

## Feature → DEV Integration

`DEV` is the trunk and the GitLab → GitHub mirror source. (`master` is a dead 2022 branch — ignore it.) Each feature is developed in its own git worktree off `DEV` carrying its own GSD `.planning/` project (worktree-as-project). Atomic WIP commits accumulate on the feature branch; ship-grained units are squashed onto `DEV`.

**Always squash related changes into ship-grained commits on DEV.**

- Do NOT cherry-pick a feature branch's atomic commits one-by-one — DEV's history is for ship-grained units, not WIP atoms.
- Aggregate by feature / phase / fix scope, not by individual file edits.
- Prefer a 3-way `git merge --squash <feature>` so DEV-side fixes are preserved, then `git reset` and commit by scope. Avoid `git checkout <feature> -- <paths>`, which silently reverts any file where DEV is ahead of the feature branch.
- Exclude `.planning/` from DEV — planning artifacts stay on the feature branch. After a squash merge, `git checkout HEAD -- .planning` restores DEV's own planning state and drops the feature's.
- Compare with the two-dot diff (`git diff DEV <feature>`) to see the true net delta — the three-dot `DEV...<feature>` over-counts content DEV already has via shared history.
- Commit message: short title + bullet body documenting what shipped. Reference "Squashed from N atomic commits" in the body if N > 5.
- Atomic commits remain on the feature branch for forensics (review, bisect, undo); DEV stays clean.

For features spanning multiple parallel sessions, the session worktrees merge into a short-lived per-feature/milestone parent branch (`ms/<name>`), which is squashed to DEV and then retired.

> Legacy: the long-lived `GSD` branch was the old single-track integration branch (pre-worktree model). It is retained as an archived ref for the v1.0 sparkplug milestone's atomic history, but is no longer the active integration target — new work integrates feature-worktree → DEV directly.

**Why:** DEV drives the GitLab → GitHub mirror. GitHub viewers (and Dependabot, GitHub Releases auto-changelogs, anyone reading `git log DEV`) see one commit per shipped unit, not 30 micro-commits.

## Behavioral

- Do not add Claude as co-author of commits.
- Solo-maintainer project: no SLAs, no triage scaffolding, prefer toggles over commitments.
- See `AGENTS.md` for the "explain first, change after" stance on multi-line edits.
- Developer profile lives in global `~/.claude/CLAUDE.md` — not duplicated here.
