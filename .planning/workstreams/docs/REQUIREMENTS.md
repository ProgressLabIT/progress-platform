# Requirements: Progress Platform Documentation

**Defined:** 2026-04-29
**Core Value:** By May 15, 2026, public documentation lets a system integrator or open-source visitor understand what Progress Platform does, how its API works, and what its core events do — without needing to read source code.

## v1 Requirements

Requirements for the v1.0 OSS launch. Every item maps to exactly one roadmap phase.

### Mirror & OSS Table Stakes (MIR)

- [ ] **MIR-01**: GitHub mirror configured to receive one-way push from GitLab `DEV` (GitLab remains canonical)
- [ ] **MIR-02**: Mirror propagates tags (matters for `v*.*.*` releases)
- [ ] **MIR-03**: GitHub repo settings: Issues enabled, Discussions enabled, Wiki disabled, branch protection on `DEV`
- [ ] **MIR-04**: `LICENSE` file in main repo root (license choice locked separately)
- [ ] **MIR-05**: `CONTRIBUTING.md` honestly explains the mirror workflow — direct GitHub PRs cannot merge; contribution path is "open issue + attach patch"
- [ ] **MIR-06**: `CODE_OF_CONDUCT.md` in main repo root (Contributor Covenant v2.1)
- [ ] **MIR-07**: `README.md` includes a banner clarifying mirror status, link to docs site, and quickstart pointer
- [ ] **MIR-08**: Pre-launch mirror push verification — SHA-match script confirms GitLab and GitHub `DEV` are in sync; GitLab `DEV` frozen for 24h before May 15

### API Reference (API) — L0 sweep + site rendering

- [ ] **API-01**: Every public-facing endpoint in `backend/api/endpoints/` has a FastAPI route docstring (one-line summary + multi-line markdown description)
- [ ] **API-02**: Every public-facing endpoint declares `response_model=` and `responses={...}` for non-200 paths (errors, validations)
- [ ] **API-03**: Pydantic input/output models on public endpoints have `Field(..., description=, examples=)` on every field
- [ ] **API-04**: `tags_metadata` defined in `backend/api/main.py` — every tag has a description and `externalDocs` link to the relevant events / users / admins page
- [ ] **API-05**: OpenAPI schema validated by **Vacuum** (Spectral-compatible Go binary) in CI; lint thresholds defined and enforced
- [ ] **API-06**: **`vitepress-openapi`** integrated to render API reference inline in the docs site (not Swagger UI iframe)
- [ ] **API-07**: API reference deep-links from each endpoint to events it emits (cross-tab navigation between API ↔ Events sections)
- [ ] **API-08**: `openapi.json` is exported as a build artifact and grounds AI-drafted prose (prevents hallucinated parameters)

### Events Reference (EVT)

- [ ] **EVT-01**: Events index page lists every event type from `backend/api/events/` with auto-extracted metadata (event name, `EventType` enum value, info model, transaction collections, post-processing summary)
- [ ] **EVT-02**: Top ~10 critical events identified (jointly with Sparkplug demo workstream) and documented with hand-crafted Mermaid `sequenceDiagram` flowcharts
- [ ] **EVT-03**: Each handcrafted event flowchart shows pre-conditions, transactional `apply` boundary as `rect`, and post-processing (NATS subjects emitted)
- [ ] **EVT-04**: Each documented event has its own page with: name, `EventType`, info model schema, transaction collections, business preconditions, post-processing side effects
- [ ] **EVT-05**: Events with >20 nodes use the ELK renderer (`%%{init: {"flowchart": {"defaultRenderer":"elk"}}}%%`); fan-out events (e.g., `BatchCompletedEvent`) decomposed into multiple diagrams
- [ ] **EVT-06**: Events reference cross-links to NATS subject taxonomy (Sparkplug demo ADR 0002) where applicable

### CLI Reference (CLI)

- [ ] **CLI-01**: `progress init` page documents usage, options, examples, and mapping to Compose stack
- [ ] **CLI-02**: `progress restore` page documents usage, options, examples
- [ ] **CLI-03**: `progress tap` page documents usage, options, examples
- [ ] **CLI-04**: CLI examples are validated executable via `pytest-markdown-docs` (or equivalent) so docs/code drift fails CI

### User Docs v1 (USER) — L2

- [ ] **USER-01**: Product overview — what Progress Platform is, who it's for, where it fits (MES + Industry 4.0 + Sparkplug ingestion)
- [ ] **USER-02**: Production module walkthrough — jobs, batches, steps; main screens, key buttons, expected business logic
- [ ] **USER-03**: Inventory module walkthrough — positions, movements; main screens
- [ ] **USER-04**: Counting module walkthrough — sessions, application; main screens
- [ ] **USER-05**: User Hub / Assignments walkthrough — assignment tab flow
- [ ] **USER-06**: Warehouse mobile app overview — Vue SPA app, scanning, missions/movement-lists/counting-sessions
- [ ] **USER-07**: Coverage philosophy v1: breadth > depth; main features visible in the UI; deep tutorials deferred

### Admin / Integrator Docs (ADM) — L3

- [ ] **ADM-01**: Deployment basics — Docker Compose stack overview, volumes, secrets, Traefik
- [ ] **ADM-02**: Configuration reference — every `PROGRESS_*` env var from `backend/api/utils/config.py` with type, default, description
- [ ] **ADM-03**: Integration touchpoints — NATS subject taxonomy, Sparkplug bridge HTTP read API, OpenAPI consumer notes (codegen pointers)
- [ ] **ADM-04**: Operations basics — health checks, log locations, common diagnostic commands (e.g., `progress tap`)

### Site Infrastructure (SITE)

- [x] **SITE-01**: VitePress site initialized under `docs/` in main repo (Vue/Vite stack alignment)
- [x] **SITE-02**: Mermaid plugin enabled in VitePress config; ELK renderer available
- [x] **SITE-03**: Hand-written `themeConfig.sidebar` (no auto-sidebar plugins) for narrative-ordered navigation
- [x] **SITE-04**: Co-located top-nav: API · Events · CLI · Users · Admins
- [x] **SITE-05**: Local search via **MiniSearch** (built-in VitePress provider) for v1; Algolia DocSearch application submitted in parallel for v1.1
- [x] **SITE-06**: Sitemap enabled (`sitemap.hostname`) for SEO/discoverability
- [x] **SITE-07
**: GitHub Actions workflow on the mirror builds VitePress and deploys to GitHub Pages on push to `DEV`
- [x] **SITE-08**: Every in-docs source-code permalink points to `github.com/...` (not `gitlab.com/...`)
- [x] **SITE-09
**: Dead-link CI job (`lychee` or VitePress built-in) runs on every PR; fails build on broken links
- [x] **SITE-10**: URL contract locked before any markdown is written (`/api/...`, `/events/...`, `/cli/...`, `/users/...`, `/admins/...`); GitHub Pages has no server-side redirects, so renames are expensive
- [ ] **SITE-11**: Site reachable at the GitHub Pages URL **by May 14, 2026** (one-day pre-launch dry-run)
- [x] **SITE-12**: AI-drafted prose grounded in exported `openapi.json` and source code; CI check enforces "examples must exist in OpenAPI"

## v2 Requirements

Deferred to post-launch. Acknowledged but not in current roadmap.

### Embedded Delivery

- **EMBED-01**: L2 user docs embedded in the platform shell for airgapped delivery
- **EMBED-02**: In-app help drawer / contextual help tied to current screen

### km/ Wiki Conversion

- **KM-01**: Decide on km/ structure (markdown stubs vs Docusaurus vs VitePress sub-site vs Logseq/Obsidian vault)
- **KM-02**: Migrate stubs into chosen structure with templates

### Internationalization

- **I18N-01**: vue-i18n integration for L2 user docs
- **I18N-02**: Translation infrastructure (Crowdin / Transifex / Weblate)
- **I18N-03**: Initial language pack (likely Italian, given progresslab origin)

### Polish & Reach

- **POL-01**: Custom subdomain (e.g., `docs.progresslab.it`) with Cloudflare CNAME
- **POL-02**: Algolia DocSearch live (replacing MiniSearch)
- **POL-03**: Versioned docs (per-release snapshots)
- **POL-04**: Search analytics (DocSearch analytics or Plausible)
- **POL-05**: Accessibility audit + WCAG 2.2 AA compliance pass
- **POL-06**: Video walkthroughs / screencasts embedded inline

### Coverage Expansion

- **COV-01**: Full backend docstring sweep (internal helpers, managers, utils — beyond public-API surface)
- **COV-02**: Mermaid flowcharts for all 50+ events (beyond top ~10)
- **COV-03**: Auto-generated event flowcharts via `BaseEvent` introspection tool
- **COV-04**: Frontend component reference (Quasar/Vue components)
- **COV-05**: Deep tutorials per module (vs coarse v1 walkthroughs)

## Out of Scope

Explicitly excluded from v1 and v2 (or excluded entirely from the docs workstream).

| Feature / Decision | Reason |
|--------------------|--------|
| Full GitLab → GitHub migration (CI, registry, scripts) | Mirror-only is the launch-window decision; revisit based on contribution velocity |
| Issue migration from private GitLab backlog to GitHub | Internal backlog stays private; fresh OSS issues only |
| Backend code refactors (`except:`, `print()`, Vuex → Pinia) | Out of docs workstream scope; tracked elsewhere |
| New endpoints / behavior changes during L0 sweep | Docstring + type addition only; no functional changes |
| Custom VitePress theme | Default theme + minor overrides only; theme work is rabbit hole |
| Comment system on doc pages (Giscus, etc.) | Use GitHub Discussions instead |
| PDF export of docs | Not requested; web-first |
| Searchable AI-chat assistant on docs site | Out of scope; can revisit post-launch |
| Auto-generated event flowcharts (introspection tool) for v1 | Tool development is its own project; handcraft for v1, automate post-launch |
| Translation of CLI / API / Events / Admin sections | English only across all sections for v1 |
| Architecture decision records (ADRs) outside the docs workstream's own decisions/ folder | Workstream-internal ADRs OK; project-wide ADR system is separate |

## Traceability

Filled by `/gsd-roadmapper` 2026-04-29. Every v1 REQ-ID maps to exactly one phase.

| Requirement | Phase | Status |
|-------------|-------|--------|
| MIR-01 | Phase 1 (Scaffold & Public Foundation) | Pending |
| MIR-02 | Phase 1 (Scaffold & Public Foundation) | Pending |
| MIR-03 | Phase 1 (Scaffold & Public Foundation) | Pending |
| MIR-04 | Phase 1 (Scaffold & Public Foundation) | Pending |
| MIR-05 | Phase 1 (Scaffold & Public Foundation) | Pending |
| MIR-06 | Phase 1 (Scaffold & Public Foundation) | Pending |
| MIR-07 | Phase 1 (Scaffold & Public Foundation) | Pending |
| MIR-08 | Phase 4 (Launch Readiness) | Pending |
| API-01 | Phase 2 (Code-Grounded Reference) | Pending |
| API-02 | Phase 2 (Code-Grounded Reference) | Pending |
| API-03 | Phase 2 (Code-Grounded Reference) | Pending |
| API-04 | Phase 2 (Code-Grounded Reference) | Pending |
| API-05 | Phase 2 (Code-Grounded Reference) | Pending |
| API-06 | Phase 2 (Code-Grounded Reference) | Pending |
| API-07 | Phase 2 (Code-Grounded Reference) | Pending |
| API-08 | Phase 2 (Code-Grounded Reference) | Pending |
| EVT-01 | Phase 2 (Code-Grounded Reference) | Pending |
| EVT-02 | Phase 2 (Code-Grounded Reference) | Pending |
| EVT-03 | Phase 2 (Code-Grounded Reference) | Pending |
| EVT-04 | Phase 2 (Code-Grounded Reference) | Pending |
| EVT-05 | Phase 2 (Code-Grounded Reference) | Pending |
| EVT-06 | Phase 2 (Code-Grounded Reference) | Pending |
| CLI-01 | Phase 3 (Human-Facing Content) | Pending |
| CLI-02 | Phase 3 (Human-Facing Content) | Pending |
| CLI-03 | Phase 3 (Human-Facing Content) | Pending |
| CLI-04 | Phase 3 (Human-Facing Content) | Pending |
| USER-01 | Phase 3 (Human-Facing Content) | Pending |
| USER-02 | Phase 3 (Human-Facing Content) | Pending |
| USER-03 | Phase 3 (Human-Facing Content) | Pending |
| USER-04 | Phase 3 (Human-Facing Content) | Pending |
| USER-05 | Phase 3 (Human-Facing Content) | Pending |
| USER-06 | Phase 3 (Human-Facing Content) | Pending |
| USER-07 | Phase 3 (Human-Facing Content) | Pending |
| ADM-01 | Phase 3 (Human-Facing Content) | Pending |
| ADM-02 | Phase 3 (Human-Facing Content) | Pending |
| ADM-03 | Phase 3 (Human-Facing Content) | Pending |
| ADM-04 | Phase 3 (Human-Facing Content) | Pending |
| SITE-01 | Phase 1 (Scaffold & Public Foundation) | Pending |
| SITE-02 | Phase 1 (Scaffold & Public Foundation) | Pending |
| SITE-03 | Phase 1 (Scaffold & Public Foundation) | Pending |
| SITE-04 | Phase 1 (Scaffold & Public Foundation) | Pending |
| SITE-05 | Phase 1 (Scaffold & Public Foundation) | Pending |
| SITE-06 | Phase 1 (Scaffold & Public Foundation) | Pending |
| SITE-07 | Phase 1 (Scaffold & Public Foundation) | Pending |
| SITE-08 | Phase 1 (Scaffold & Public Foundation) | Pending |
| SITE-09 | Phase 1 (Scaffold & Public Foundation) | Pending |
| SITE-10 | Phase 1 (Scaffold & Public Foundation) | Pending |
| SITE-11 | Phase 4 (Launch Readiness) | Pending |
| SITE-12 | Phase 1 (Scaffold & Public Foundation) | Pending |

**Coverage:**
- v1 requirements: 49 total
- Mapped to phases: 49 (100%)
- Unmapped: 0 ✓

**Distribution:**
- Phase 1 (Scaffold & Public Foundation): 18 requirements (MIR-01..07, SITE-01..10, SITE-12)
- Phase 2 (Code-Grounded Reference): 14 requirements (API-01..08, EVT-01..06)
- Phase 3 (Human-Facing Content): 15 requirements (CLI-01..04, USER-01..07, ADM-01..04)
- Phase 4 (Launch Readiness): 2 requirements (MIR-08, SITE-11)

---
*Requirements defined: 2026-04-29*
*Last updated: 2026-04-29 — traceability filled by `/gsd-roadmapper`.*
