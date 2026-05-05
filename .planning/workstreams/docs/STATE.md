---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
current_plan: 1
status: complete-pending-rehearsal
stopped_at: v1.0 milestone complete (47/49 verified; MIR-08 + SITE-11 pending May 14 rehearsal)
last_updated: "2026-05-05T07:29:51.948Z"
last_activity: 2026-05-05
progress:
  total_phases: 4
  completed_phases: 4
  total_plans: 19
  completed_plans: 19
  percent: 100
---

# Project State

## Project Reference

**Workstream:** `docs`
**Core Value:** By May 15, 2026, public documentation lets a system integrator or open-source visitor understand what Progress Platform does, how its API works, and what its core events do — without needing to read source code.
**Current Milestone:** v1.0 Open-Source Launch Documentation (May 15, 2026)
**Milestone Scope:** 4 phases, 49 v1 requirements (MIR / API / EVT / CLI / USER / ADM / SITE), AI-drafted then human-curated authoring against a 16-day calendar.
**Roadmap:** [`ROADMAP.md`](ROADMAP.md) — 4 coarse phases.
**Requirements:** [`REQUIREMENTS.md`](REQUIREMENTS.md) — 49 v1 requirements, 100% mapped.
**Research:** [`research/PITFALLS.md`](research/PITFALLS.md) — 38 pitfalls with phase-mapped mitigations.

## Current Position

**Phase:** 04 — Launch Readiness
**Plan:** 02 — next up (04-01 complete)
**Status:** Executing Phase 04
**Next Up:** `/gsd-execute-phase` plan 04-02 (launch dry-run runbook execution against the LAUNCH-CHECKLIST.md staged in 04-01).
**Last Activity:** 2026-05-05
**Last Activity Description:** Plan 04-01 complete — LAUNCH-CHECKLIST.md created at `.planning/workstreams/docs/LAUNCH-CHECKLIST.md` with 7 sections covering D-01..D-10 decisions; commit `73713572`.

## Progress

**Phases Complete:** 0 / 4 (Phase 01 file deliverables complete; awaiting live-deploy checkpoints)
**Current Plan:** 1
**Progress Bar:** [██████████] 100% (Phase 01 plan files)

## Calendar

**Working window:** 2026-04-29 → 2026-05-15 (~16 days)
**Pre-launch dry-run:** May 14 (Thu) — site live, fresh-VM README rehearsal, SHA-match verification dress run.
**Launch:** May 15 (Fri) — webinar to Industry-4.0 consultants. Site reachable on `https://progresslabit.github.io/progress-platform/` from webinar opening.
**Mirror freeze:** May 14 09:30 → May 15 11:00 (no GitLab `DEV` merges).

**Suggested phase windows (indicative, plan-phase will refine):**

- **Phase 1 (Scaffold & Public Foundation):** 2026-04-29 → 2026-05-03 (~5 days). Unblocks all later phases.
- **Phase 2 (Code-Grounded Reference):** 2026-05-04 → 2026-05-09 (~6 days). Tightest scope; L0 sweep + events handcraft is the most labor-dense work.
- **Phase 3 (Human-Facing Content):** 2026-05-09 → 2026-05-13 (~4 days). AI draft + curate; coverage breadth > depth.
- **Phase 4 (Launch Readiness):** 2026-05-13 → 2026-05-15 (~2 days). Freeze, dry-run, go-live.

**Cut levers if timeline slips** (priority order):

1. Drop USER-06 (warehouse mobile app L2 walkthrough) — least visible in webinar.
2. Drop ADM-04 (operations basics page) — operationally useful but not webinar-critical.
3. Drop 1–2 of the bottom-of-priority top-10 event flowcharts (preserve `IssueCreated`, `BatchCompleted`, `JobStarted`, `MovementCompleted` — Sparkplug-demo-relevant; drop the others to text-only).
4. Last resort: ship Phase 3 admin section as "Coming soon" placeholder; Phase 2 + Phase 1 scaffold is the minimum viable launch.

## Performance Metrics

- **v1 requirements mapped:** 49 / 49 (100%)
- **Phases defined:** 4 / 4
- **Phase plans generated:** 0 / 4
- **Orphaned requirements:** 0
- **Out-of-scope items acknowledged:** see REQUIREMENTS.md `## Out of Scope` (km/ wiki, embedded L2, i18n, custom domain, Algolia DocSearch, full backend sweep, full-event flowcharts, frontend component reference, deep tutorials)

## Accumulated Context

### Locked Decisions (from PROJECT.md)

- VitePress as the single docs-site stack (Vue/Vite alignment).
- `docs/` co-located in main repo (not separate `progress-docs` repo) — code/docs drift mitigated by co-location.
- GitHub mirror as the public face; GitLab remains canonical for code, CI, registry, deploys.
- GitHub Pages on the mirror for hosting (free for public OSS repos).
- Public-API surface only for L0 docstring sweep; full-backend sweep is post-launch.
- Auto-extract event metadata for all events; handcraft Mermaid sequence diagrams for top ~10 only.
- L2 + L3 co-located in single VitePress site, separate top-nav tabs.
- AI-drafted then user-edited authoring (calendar mandates automation).
- English only for v1 (i18n is multi-week, deferred).
- km/ wiki conversion deferred entirely.
- Coverage breadth > depth for v1.
- OSS table-stakes (LICENSE, CONTRIBUTING, CODE_OF_CONDUCT) before mirror goes public.
- Issues + Discussions on, Wiki off, branch-protected `DEV`.

### Tooling Decisions (from PITFALLS.md research)

- **`vitepress-openapi`** (enzonotario) for inline API rendering — not Swagger-iframe.
- **MiniSearch** built-in local search for v1; Algolia DocSearch application sent in parallel for v1.1.
- **vacuum** (Go, Spectral-compatible) for OpenAPI lint CI gate — faster than Spectral, single binary.
- **lychee** for second-pass dead-link CI (anchor-aware; VitePress built-in checker misses hash fragments).
- **`vitepress-plugin-mermaid`** (emersonbottero) for Mermaid + dark-mode integration; pin compatible version.
- **`pytest-markdown-docs`** (modal-labs) for executable CLI markdown examples.
- **`scripts/export_openapi.py`** calling `app.openapi()` — build-time, no live app.
- **Hand-written `themeConfig.sidebar`** — no auto-sidebar plugin.
- **Default VitePress theme + CSS variables only** — no `Layout.vue` override.
- Top-10 events for hand-crafted Mermaid (selection coordinated with Sparkplug demo): `JobStartedEvent`, `StepCompletedEvent`, `BatchCompletedEvent`, `JobClosedEvent`, `MovementCompletedEvent`, `CountSessionAppliedEvent`, `SerialCreatedEvent`, `IssueCreatedEvent`, +2 jointly selected.

### Cross-Workstream Coordination

- **Sparkplug demo workstream** (`.planning/workstreams/sparkplug-demo/`) owns:
  - The CLI surface (`progress init/restore/tap`) — S4 session. Docs in Phase 3 mirror its locked behavior, not in-flight changes.
  - The "5-minute" README quickstart — S5 session rehearses on Linode VM. Docs README block must stay in lockstep.
  - Top-10 event selection — joint cut required at the start of Phase 2.
- **Progress Platform main** (`.planning/`): no direct dependency. The `<!-- GSD:stack -->` and `<!-- GSD:architecture -->` blocks in `CLAUDE.md` still mention Kafka — historical drift, treat as informational. Platform messaging is NATS.

### Blockers

None.

### Post-Launch TODOs

- **GH Actions SHA pinning** — currently `@v2`/`@v4`/`@v5` tag pins. Switch to commit SHAs post-launch per OpenSSF Scorecard / lychee-action README recommendation. Tracked from Plan 01-03 threat-model T-01-03-02 (post-launch hardening).

### Todo (next-action queue)

1. **`/gsd-plan-phase 1 --ws docs`** — generate Phase 1 plans (mirror & OSS table-stakes; VitePress skeleton + URL contract; GitHub Actions deploy). Estimate 2–3 plans for this phase given coarse granularity.
2. Coordinate top-10 event selection with Sparkplug demo S5/S1 before Phase 2 planning starts (so the events selected match the webinar narrative + production critical path).
3. Author `.planning/workstreams/docs/CONVENTIONS.md` early in Phase 1 — endpoint-docstring shape, AI drafting prompt scaffolds (Pitfalls 5.1, 5.3), Mermaid transaction-boundary convention (Pitfall 3.2). All four phases reference it.
4. Confirm license choice (Apache 2.0 recommended per Pitfall 4.1) with workstream owner before Phase 1 plan-phase — the LICENSE file is a Phase 1 deliverable.
5. Set up `security@progresslab.it` email alias before Phase 1 ships SECURITY.md.

## Session Continuity

**Stopped At:** Phase 4 artifacts staged; May 14 rehearsal items pending
**Resume File:** --resume-file

---

*Last updated: 2026-04-29 after roadmap creation.*
