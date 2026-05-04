# Progress Platform Documentation

## What This Is

A documentation initiative for the Progress Platform open-source launch. Covers four tiers in a single VitePress site: code-level reference (enriched FastAPI OpenAPI from docstrings + Pydantic types), events reference with business-logic flowcharts, end-user product documentation, and admin/system-integrator documentation. Aimed at supporting the public OSS launch coordinated with the Sparkplug B webinar to Industry 4.0 consultants on **Friday May 15, 2026**.

## Core Value

By **May 15, 2026**, public documentation lets a system integrator or open-source visitor understand what Progress Platform does, how its API works, and what its core events do — without needing to read source code.

## Current Milestone: v1.0 Open-Source Launch Documentation

**Goal:** Ship a public VitePress site covering enriched API reference, events reference (all events documented; top ~10 with hand-crafted Mermaid flowcharts), `progress init/restore/tap` CLI reference, end-user product docs at coarse granularity, and admin/integrator basics. Site lives in `docs/` of the main repo. Published from a GitHub mirror via GitHub Pages. GitLab remains canonical for code, CI, and registry.

**Trigger:** Open-sourcing the platform around the **May 15, 2026** webinar.

## Requirements

### Validated

<!-- Reality at start of workstream — these already exist in the platform. -->

- ✓ FastAPI auto-generates OpenAPI schema at `/openapi.json` and serves Swagger UI at `/docs` and ReDoc at `/redoc` — to be **enriched** (not replaced) by the L0 sweep
- ✓ Backend has ~20+ endpoint files in `backend/api/endpoints/` with FastAPI route handlers
- ✓ Events system in `backend/api/events/` with 50+ event types, all extending `BaseEvent` (`pre_processing` → `apply` → `post_processing`)
- ✓ CLI demo commands `progress init`, `progress restore`, `progress tap` exist in `cli/` (Typer-based)
- ✓ Knowledge management folder `km/` exists with stub structure (`architecture/`, `auth/`, `domains/`, `testing/`, `README.md`) — out of v1.0 scope
- ✓ Code is on GitLab (`registry.gitlab.com/progresslab/progress-platform/...`) with `.gitlab-ci.yml` CI/CD pipeline
- ✓ A version of the codebase is already public on GitHub (mirror feasibility confirmed)

### Active

<!-- v1.0 scope — building toward May 15. -->

**Phase 0 — Mirror & OSS table stakes**
- [ ] GitHub mirror established as push-target from GitLab `DEV` (one-way, GitLab canonical)
- [ ] OSS table-stakes files in main repo: `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `README` banner clarifying mirror status
- [ ] GitHub repo settings: Issues enabled, Discussions enabled, Wiki disabled, branch protection on `DEV`

**L0 — API foundation (public-API surface)**
- [ ] Public-facing endpoints in `backend/api/endpoints/` have FastAPI route docstrings (summary + description)
- [ ] Public-facing endpoints have Pydantic input/output models with field descriptions
- [ ] OpenAPI schema is self-explanatory when read in Swagger/ReDoc
- [ ] Inline comments improved on cross-cutting backend code touched during sweep (no refactor)

**L1 — Events reference**
- [ ] All event types from `backend/api/events/` listed with auto-extracted metadata (event name, info model, transaction collections, post-processing notes)
- [ ] Top ~10 critical events have hand-crafted Mermaid flowcharts of business logic (selection driven by Sparkplug demo + production critical paths)
- [ ] Cross-references from API endpoints → events they emit

**CLI reference**
- [ ] `progress init` documented (usage, options, examples, mapping to compose stack)
- [ ] `progress restore` documented
- [ ] `progress tap` documented
- [ ] Pages aligned with Sparkplug demo workstream behavior

**L2 — User docs v1**
- [ ] Product overview: what Progress Platform is, who it's for
- [ ] Main feature walkthrough at coarse granularity (production, inventory, counting, jobs, assignments, user hub) — screens, buttons, business logic
- [ ] No deep tutorials yet; coverage breadth > depth

**L3 — Admin / system-integrator docs**
- [ ] Deployment basics (Docker Compose stack, volumes, secrets)
- [ ] Configuration reference (`PROGRESS_*` env vars from `backend/api/utils/config.py`)
- [ ] Integration touchpoints (NATS subjects, Sparkplug bridge endpoints, OpenAPI consumer notes)
- [ ] Co-located with L2 in same VitePress site under separate top-nav tab

**Site infrastructure**
- [ ] VitePress site under `docs/` in main repo (Vue/Vite stack alignment)
- [ ] Mermaid plugin enabled
- [ ] GitHub Actions workflow on mirror builds VitePress and deploys to GitHub Pages
- [ ] Permalinks in docs reference `github.com/...` source URLs (not GitLab)
- [ ] Co-located navigation: API · Events · CLI · Users · Admins (single deploy, shared search)

### Out of Scope (v1.0)

- **Embedded L2 docs in the platform** for airgapped delivery — multi-week project; deferred post-launch
- **km/ wiki conversion** — internal-only; markdown stubs stay as-is; revisit post-launch
- **i18n / multi-language docs** — vue-i18n integration is multi-week; English only for v1
- **Full GitLab → GitHub migration** (CI, container registry, deploy scripts, secrets) — keep mirror-only; revisit based on contribution velocity post-launch
- **Mermaid flowcharts for all 50+ events** — top ~10 only; remaining are text-only
- **Full event-class introspection tool** with auto-generated flowcharts — handcraft top events; auto-extract metadata only
- **Issue migration from private GitLab backlog to public GitHub** — fresh OSS issues only; backlog stays private
- **Custom domain** (e.g., `docs.progresslab.it`) — ship on `github.io` for v1; subdomain is post-launch polish
- **Accessibility audit, video walkthroughs, screenshot polish, search analytics** — post-launch enhancements
- **Backend code refactors** (bare `except:`, `print()` cleanup, Vuex → Pinia, etc.) — out of docs workstream scope; tracked elsewhere
- **Full backend docstring sweep** (internal helpers, managers, utils) — only public-API surface for v1; full sweep is post-launch

## Context

- **Trigger:** open-sourcing the Progress Platform around the **May 15, 2026** Sparkplug B webinar to Industry 4.0 consultants. Documentation is a launch blocker.
- **Backend:** FastAPI 0.x with ~20+ endpoint files. Current state: inconsistent docstrings, some endpoints with minimal type hints, OpenAPI schema is sparse, bare `except:` clauses common. L0 sweep adds docstrings + types only — no refactor.
- **Events:** 50+ event types organized by domain (production, inventory, counting, etc.) all extending `BaseEvent`. Pattern: `pre_processing` → `apply` (transactional state mutations) → `post_processing` (Kafka publish, side effects). Flowcharts will document business logic per event.
- **Webapps:** Vue 3 + Quasar 2.16 (`webapps/main/` + `webapps/warehouse/`). Existing vue-i18n strings — useful reference for L2 user docs but not duplicated.
- **CLI:** Typer-based commands under `cli/`. `progress init`, `restore`, `tap` are owned by the **Sparkplug demo workstream** (S4 session). Docs must mirror the demo's behavior at v1.0.
- **Knowledge management `km/`:** stub today; intended for core developers + agents. Will stay markdown-only for v1.0 launch — wiki/site conversion is a separate workstream decision.
- **Repo state:** GitLab is canonical (`registry.gitlab.com/progresslab/progress-platform/`). A mirror exists on GitHub. Mirror approach chosen over full migration to keep CI, registry, and existing scripts stable through the launch window.
- **Parallel workstream:** `sparkplug-demo` is the launch demo build. Docs workstream must reflect what's in the v1 demo (CLI, UNS topology browser, Sparkplug architecture, hardcoded automation).
- **Existing platform docs:** README.md, `km/README.md`, scattered comments — none of these target a public OSS audience; they're internal. v1.0 docs replace nothing; they extend.

## Constraints

- **Timeline:** Public site live by **May 15, 2026** — ~16 days from start (2026-04-29). Hard deadline tied to webinar marketing.
- **Tech stack:** VitePress (Vue/Vite), Mermaid for diagrams, GitHub Pages for hosting, GitHub Actions for build/deploy. No new vendors beyond GitHub.
- **Source canonicality:** GitLab remains canonical for code, CI, container registry, and deploys. GitHub is read-only mirror with public face. PRs and Issues curated; internal backlog stays private on GitLab.
- **Repo placement:** `docs/` folder in main `progress-platform` repo (not a separate `progress-docs` repo). Code/docs drift mitigated by co-location.
- **Authoring approach:** AI-drafted then user-edited. Agents read code/components, draft markdown, user reviews and curates. Calendar mandates automation.
- **No platform code changes** beyond docstrings, type hints, and minor inline comments during the L0 sweep. No refactors, no new endpoints, no behavior changes.
- **Coverage philosophy:** breadth > depth for v1. Cover main features at coarse granularity. Refinement, deep tutorials, accessibility, embedded delivery, and i18n are post-launch.
- **OSS table stakes:** LICENSE, CONTRIBUTING, CODE_OF_CONDUCT must land in main repo before mirror goes public.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Single docs site stack: **VitePress** | Vue/Vite alignment with platform; future embeddability for airgap; Mermaid plugin available | — Pending |
| **Public-API surface only** for L0 docstring sweep | Tight calendar; full backend sweep would slip launch; rest is post-launch | — Pending |
| **Auto-extract event metadata + handcraft Mermaid for top ~10 events** | Achieves coverage on all events without authoring 50+ flowcharts | — Pending |
| **Online-only L2** for v1; embedded delivery deferred | Airgap embed is multi-week scope on its own | — Pending |
| **L2 + L3 co-located** in single VitePress site (separate top-nav tabs) | Single deploy, shared search, easier cross-references; tabs separate audiences cleanly | — Pending |
| **Defer km/ wiki conversion entirely** | Internal-only; not OSS-launch critical; keeps scope tight | — Pending |
| **GitHub Pages on the mirror** for hosting | OSS-native URL; free Actions for public repos; zero risk to existing GitLab CI | — Pending |
| **`docs/` folder in main repo** (not separate repo) | Code/docs drift is the #1 risk; co-location fixes it; CI builds both | — Pending |
| **AI-drafted then user-edited** authoring | 16-day calendar requires automation; agents draft, user curates | — Pending |
| **English only** for v1 | i18n is multi-week project; vue-i18n integration is post-launch | — Pending |
| **GitHub mirror, not full migration** | Keep GitLab CI / registry / scripts intact; gain discoverability via mirror; defer migration question post-launch | — Pending |
| **GitHub: Issues + Discussions enabled, Wiki disabled, branch-protected `DEV`** | Curated fresh OSS engagement; private backlog stays on GitLab | — Pending |
| **Coverage breadth > depth for v1** | Tight deadline; visitors get a complete-feeling overview vs deep-but-incomplete | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-29 after initialization*
