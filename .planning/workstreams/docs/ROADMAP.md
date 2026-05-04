# Documentation Roadmap

**Workstream:** `docs`
**Milestone:** v1.0 Open-Source Launch Documentation (see [`PROJECT.md`](PROJECT.md))
**Target launch:** Friday May 15, 2026 (webinar-driven OSS public release)
**Working window:** ~16 days (2026-04-29 → 2026-05-15); pre-launch dry-run May 14
**Granularity:** coarse (4 phases, 1–3 plans each — see [`../../config.json`](../../config.json))
**Research input:** [`research/PITFALLS.md`](research/PITFALLS.md) — 38 pitfalls with prescriptive recommendations, mapped per-phase.

## Goal-Backward Frame

When May 15 arrives, an external visitor — an Industry-4.0 consultant pulled in by the Sparkplug B webinar — must be able to:

1. Land on the GitHub mirror and understand legally what they may do with the code (LICENSE, CONTRIBUTING, mirror banner).
2. Reach `https://progresslabit.github.io/progress-platform/` from the README and find the docs site live.
3. Read the **API reference** rendered inline (not Swagger-iframe) for any public endpoint, with parameters, responses, error contract, and emitted events linked.
4. Read the **events reference** with all 50+ events listed and the top ~10 with hand-crafted sequence diagrams that show the ArangoDB transaction boundary, post-commit NATS publish, and fan-out behavior.
5. Run the `progress init` quickstart from the README on a fresh VM and reach the same demo the webinar showed.
6. Browse a coarse but complete L2 user walkthrough of production / inventory / counting / user-hub and a deployment + configuration L3 admin reference.

The four phases below are the smallest cut that gets us there. Phase 1 is the scaffold (everything else writes into it). Phase 2 is the code-grounded reference (API + Events; tightly coupled because endpoints emit events and cross-link to them). Phase 3 is the human-facing AI-drafted prose (CLI + L2 + L3, similar authoring loops). Phase 4 is the freeze and the dry-run.

## Phases

- [ ] **Phase 1: Scaffold & Public Foundation** — Mirror, OSS table-stakes, VitePress skeleton, URL contract locked, GH Actions deploy live.
- [ ] **Phase 2: Code-Grounded Reference** — L0 API docstring sweep + vacuum CI gate + vitepress-openapi rendering + events auto-extract + top-10 Mermaid sequence diagrams.
- [ ] **Phase 3: Human-Facing Content** — CLI executable docs + L2 user walkthroughs (breadth > depth) + L3 admin/integrator reference.
- [ ] **Phase 4: Launch Readiness** — SHA-match freeze, dead-link/sitemap/accessibility final pass, May 14 dry-run, May 15 live.

## Phase Summary

| # | Phase | Goal | Requirements (count) | Success Criteria |
|---|-------|------|----------------------|-----------------:|
| 1 | Scaffold & Public Foundation | Public-facing skeleton exists at the locked URL contract, OSS table-stakes are in main repo, GH Actions ships every push to GitHub Pages. | MIR-01..07, SITE-01..10, SITE-12 (20) | 5 |
| 2 | Code-Grounded Reference | Every public-API endpoint and every event is documented from the source of truth (no hallucinated examples), with cross-tab navigation and CI lint gates. | API-01..08, EVT-01..06 (14) | 5 |
| 3 | Human-Facing Content | A coarse-but-complete walkthrough of the CLI, end-user features, and admin/integrator setup — drafted from source, human-curated, executable where applicable. | CLI-01..04, USER-01..07, ADM-01..04 (15) | 4 |
| 4 | Launch Readiness | Site is live at the GitHub Pages URL by May 14, mirror is verified in sync, no dead anchors, sitemap is published. | MIR-08, SITE-11 (2) | 4 |

**Total:** 49 / 49 v1 requirements mapped, 4 phases, 18 success criteria.

## Phase Details

### Phase 1: Scaffold & Public Foundation

**Goal**: A public-facing skeleton exists — GitHub mirror is live with OSS table-stakes (LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY-equivalent, README banner), the VitePress site under `docs/` builds and deploys to GitHub Pages on every push to `DEV`, and the URL contract (`/api/...`, `/events/...`, `/cli/...`, `/users/...`, `/admins/...`) is locked before any markdown is written. Every later phase depends on this scaffold.

**Depends on**: Nothing (first phase).

**Requirements**: MIR-01, MIR-02, MIR-03, MIR-04, MIR-05, MIR-06, MIR-07, SITE-01, SITE-02, SITE-03, SITE-04, SITE-05, SITE-06, SITE-07, SITE-08, SITE-09, SITE-10, SITE-12.

**Success Criteria** (what must be TRUE):

1. `git ls-remote https://github.com/ProgressLabIT/progress-platform DEV` resolves to the same SHA as `git ls-remote https://gitlab.com/progresslab/progress-platform DEV` within 30 seconds of any push to GitLab `DEV` (one-way mirror, tags propagate).
2. A first-time visitor opening the GitHub repo sees a banner identifying it as a read-only mirror, a working "Try it in 5 minutes" `progress init` block in the README, links to LICENSE / CONTRIBUTING / CODE_OF_CONDUCT, and a link to the docs site URL — Issues and Discussions are enabled, Wiki is disabled, `DEV` is branch-protected.
3. The deployed GitHub Pages site at `https://progresslabit.github.io/progress-platform/` returns HTTP 200 on every URL in the locked URL contract (skeleton pages may be one-line placeholders, but every `/api/*`, `/events/*`, `/cli/*`, `/users/*`, `/admins/*` route in the contract resolves), and the top-nav shows API · Events · CLI · Users · Admins.
4. A push to `DEV` on the GitHub mirror triggers the GitHub Actions VitePress build + GitHub Pages deploy, completing in under 10 minutes; `/sitemap.xml` returns content with the correct hostname and `themeConfig.search.provider = 'local'` (MiniSearch) is enabled.
5. The hand-written `themeConfig.sidebar` in `.vitepress/config.ts` is the only navigation source (no auto-sidebar plugin), all source-code permalinks template to `github.com/...` (not GitLab), `vitepress-openapi` is installed and wired against a placeholder `openapi.json`, the dead-link CI job (`lychee` against built `dist/`) runs on every PR, and an exported `openapi.json` build artifact is produced (will be populated by Phase 2).

**Plans**: TBD

**UI hint**: no

**Risks**:

- **Mirror push race** (Pitfall 4.7) — GitLab → GitHub mirror typically runs every 5 min; if the manual force-push trigger isn't documented in this phase, a stale mirror at webinar time is a launch-day failure mode. Mitigation: capture the GitLab `Repository → Mirroring → Update now` flow in `CONTRIBUTING.md` mirror section so Phase 4 can rely on it.
- **CONTRIBUTING.md dishonesty** (Pitfall 4.2) — defaulting to "Open a PR against DEV" is the #1 source of OSS-mirror confusion; the wording must match what the maintainer will actually do (close direct PRs, redirect to issue + patch). Treat the `CONTRIBUTING.md` text as a hard deliverable, not boilerplate.
- **URL-contract churn** — GitHub Pages has no server-side redirects. Any rename mid-Phase 2/3 breaks every external link. The contract MUST be locked in this phase before any markdown lands.
- **Custom-domain temptation** (Pitfall 4.8) — do not attempt `docs.progresslab.it` in this phase. Ship on `github.io` for v1; subdomain is post-launch.

---

### Phase 2: Code-Grounded Reference

**Goal**: A system integrator can read the API and Events references and learn what every public endpoint does, what fields it accepts, what it returns, what it can fail with, what events it emits, and what those events do to the database — entirely without reading source. Both references are generated and grounded in the source of truth (FastAPI introspection + Pydantic models for API; `BaseEvent` introspection for events) so AI-drafted prose cannot hallucinate fields. The vacuum lint gate enforces that every operation and every property has a description.

**Depends on**: Phase 1 (URL contract, deploy pipeline, `vitepress-openapi` wired, openapi.json build artifact slot).

**Requirements**: API-01, API-02, API-03, API-04, API-05, API-06, API-07, API-08, EVT-01, EVT-02, EVT-03, EVT-04, EVT-05, EVT-06.

**Success Criteria** (what must be TRUE):

1. An external visitor opening `https://progresslabit.github.io/progress-platform/api/production/jobs/start/` (and any other public endpoint URL from the contract) sees the endpoint rendered inline by `vitepress-openapi` with: a multi-line markdown description (not a one-line summary), every request field with description + example, every response with a typed `response_model` schema, every documented error code from `responses={...}`, a `::: code-group` block with curl + Python (httpx) examples drawn from the OpenAPI operation (no invented fields), and an "Emits:" link to the corresponding event page.
2. `vacuum lint docs/.vitepress/openapi.json --fail-severity error` reports zero violations, with the custom rule "every operation must have a description" and "every property must have a description" enforced; the `openapi.json` is exported via `scripts/export_openapi.py` calling `app.openapi()` directly (no running app, no DB, no NATS) and is committed (or generated build-time — pick one) and consumed by `vitepress-openapi`.
3. The events index at `/events/` lists every `BaseEvent` subclass found under `backend/api/events/` with auto-extracted metadata (event name, `EventType` enum value, info model, `get_tx_collections()`, post-processing summary, NATS subjects from `_notification_subtopic`); each non-flowchart event page follows the strict template (Trigger / Preconditions / State changes / Side effects / Notifications / Related events with "_None._" filler — never an omitted section).
4. The top ~10 critical events (selection coordinated with the Sparkplug demo workstream and the production critical-path: `JobStartedEvent`, `StepCompletedEvent`, `BatchCompletedEvent`, `JobClosedEvent`, `MovementCompletedEvent`, `CountSessionAppliedEvent`, `SerialCreatedEvent`, `IssueCreatedEvent`, plus 2 more selected jointly) each have a hand-crafted Mermaid `sequenceDiagram` rendering in production with: a `rect` highlighting the ArangoDB transaction boundary (`pre_processing` + `apply` + `store_event`), a `Note` marking `commit_transaction`, post-commit arrows for NATS publish and fan-out children. Diagrams with >20 nodes use `defaultRenderer: elk`; `BatchCompletedEvent`-class fan-outs are decomposed into multiple diagrams on the same page.
5. Cross-tab navigation works both directions: from any API endpoint page, "Emits:" links jump to the corresponding event page; from any event page, "Triggered by:" links jump back to the endpoint(s) that create the event; `tags_metadata` in `backend/api/main.py` provides `externalDocs` deep links into `/events/<domain>/`; events reference cross-links to NATS subjects from Sparkplug demo ADR-0002 where applicable.

**Plans**: TBD

**UI hint**: no

**Risks**:

- **Top-10 event selection requires Sparkplug demo coordination** — the joint cut needs S1/S5 sign-off (per Sparkplug demo PROJECT.md). Without that coordination the wrong 10 events get diagrams, weakening the webinar narrative. Surface this as a cross-workstream sync point at the start of this phase.
- **L0 sweep + sparse OpenAPI ordering** — `vitepress-openapi` against a sparse OpenAPI renders empty operations and visibly lies about the API. The L0 docstring + `Field(description=)` + `response_model=` + `responses={}` work MUST land before vitepress-openapi is enabled in production rendering. The vacuum CI gate is the forcing function: site won't deploy until lint passes.
- **Documented broken behavior** (Pitfall 2.6) — bare `except:` clauses returning 500 with traceback bodies are out of docs scope to fix, but the `responses={}` decorations ought to honestly document the actual error contract. A "Known Issues" admin page references the tracked issue. Reviewers may push back on shipping documented-as-broken behavior; handle in plan-phase.
- **AI hallucination on API examples** (Pitfall 5.1) — every code-block example must be validated against the OpenAPI operation (no invented fields). The validation script in CI is non-optional for this phase.

---

### Phase 3: Human-Facing Content

**Goal**: An end-user product manager and a system-integrator deploying for the first time both find what they need at coarse-but-complete granularity. CLI examples are executable (drift-fails CI). L2 walkthroughs cover the main visible features (production / inventory / counting / user-hub / warehouse mobile) at a screens-and-buttons level. L3 covers Compose stack basics, every `PROGRESS_*` env var, and integration touchpoints (NATS subjects, Sparkplug bridge HTTP API, OpenAPI consumer notes). Coverage breadth wins over depth — a deep tutorial on one feature with three other features missing is worse than coarse coverage of all five.

**Depends on**: Phase 1 (URL contract, deploy pipeline), Phase 2 (events reference exists for cross-linking from L2/L3 prose; OpenAPI consumer notes link into the API reference).

**Requirements**: CLI-01, CLI-02, CLI-03, CLI-04, USER-01, USER-02, USER-03, USER-04, USER-05, USER-06, USER-07, ADM-01, ADM-02, ADM-03, ADM-04.

**Success Criteria** (what must be TRUE):

1. A visitor opening `/cli/init/`, `/cli/restore/`, `/cli/tap/` sees a usage block, every option from the Typer command, examples mapping to the Sparkplug demo Compose stack, and `pytest --markdown-docs docs/cli/` runs all the example blocks against the actual `cli/` module in CI on every PR — drift fails the build (CLI-04). Examples mirror the Sparkplug demo S4 session's behavior (coordinated, not duplicated).
2. A visitor opening `/users/` reads a product overview ("what Progress Platform is, who it's for") and then walks five module sub-pages — `/users/production/`, `/users/inventory/`, `/users/counting/`, `/users/user-hub/`, `/users/warehouse/` — each describing the main screens, key buttons, and expected business logic at coarse granularity (no deep tutorials). The "coverage philosophy" page (USER-07) is published explaining breadth-over-depth and what's deferred to v2.
3. A visitor opening `/admins/deployment/` sees the Docker Compose stack overview (volumes, secrets, Traefik), `/admins/configuration/` lists every `PROGRESS_*` env var from `backend/api/utils/config.py` with type, default, and description (auto-extracted from the Pydantic settings model), `/admins/integrations/` covers NATS subject taxonomy + Sparkplug bridge HTTP read API + OpenAPI consumer notes (codegen pointers cross-linking into the API reference), `/admins/operations/` covers health checks, log locations, and `progress tap` as a diagnostic command.
4. A non-author human-curation pass has reviewed every page in `/cli/`, `/users/`, `/admins/` (curation gate per Pitfall 5.4); pages that didn't survive curation are explicitly marked "Coming soon" rather than shipped as un-reviewed AI prose. The same drafting prompt template (per Pitfall 5.3, encoded in CONVENTIONS.md) was used across all three sections.

**Plans**: TBD

**UI hint**: no

**Risks**:

- **AI bland-prose drift** (Pitfall 5.3, 5.4) — without a structured drafting prompt and a curation gate, this phase produces 30+ pages of generic "this module lets you manage your X" prose, which is more damaging than a missing page. The CONVENTIONS.md prompt scaffold must be in place at phase start.
- **CLI executable-docs coordination with Sparkplug demo S4** — `progress init/restore/tap` are owned by the Sparkplug demo workstream's S4 session. Docs prose must mirror behavior that's still being finalized in S4. Surface as a daily sync; pin docs to S4's locked CLI surface, not in-flight changes.
- **Coverage temptation** — the urge to "go deep on production because it's the demo highlight" sacrifices breadth. The USER-07 coverage philosophy page is the public commitment to coarse-but-complete; enforce it in curation.
- **Embedded delivery scope creep** — L2 docs in v1 are online-only (PROJECT.md locked decision); a reviewer may ask for in-app help drawer integration. Defer to v2 (EMBED-01/02 in REQUIREMENTS.md); do not let this phase grow into multi-week embed work.

---

### Phase 4: Launch Readiness

**Goal**: On May 14 the site is live at the GitHub Pages URL with every URL in the contract serving content, every internal link (including hash anchors) resolves, the sitemap is published and submitted, the GitLab → GitHub mirror is verified in sync via SHA-match, and a 24h GitLab `DEV` freeze is in effect. On May 15 the webinar opens against a public face that has been rehearsed.

**Depends on**: Phase 1 (mirror, deploy pipeline, OSS table-stakes), Phase 2 (API + Events content lives at expected URLs), Phase 3 (CLI + Users + Admins content lives at expected URLs).

**Requirements**: MIR-08, SITE-11.

**Success Criteria** (what must be TRUE):

1. By 18:00 May 14 (Thu), `https://progresslabit.github.io/progress-platform/` returns HTTP 200 and shows the full landing page with all five top-nav sections populated; a `lychee` crawl over the deployed `dist/` (anchor-aware, not just VitePress's built-in dead-link checker) reports zero broken links and zero broken hash fragments; `/sitemap.xml` is reachable and submitted to Google Search Console + Bing Webmaster Tools.
2. The pre-launch SHA-match script (`scripts/verify_mirror.sh` or equivalent) returns exit 0 confirming `git ls-remote gitlab DEV` and `git ls-remote github DEV` resolve to the same SHA; this script is run at 09:30 May 15 (30 minutes pre-webinar) after the manual GitLab → GitHub force-push trigger; GitLab `DEV` has been frozen since 09:30 May 14.
3. A fresh-VM rehearsal on May 14 confirms the README "5-minute" `progress init` quickstart works end-to-end against the public mirror — same script the Sparkplug demo S5 session is rehearsing for the webinar; the asciinema/SVG recording is committed and embedded in the README.
4. By the time the webinar opens 10:00 May 15, the docs site has been smoke-tested by a non-author against this checklist: dark-mode toggle works on Mermaid diagrams without flashbang; `vitepress-openapi` operations render with examples on the three "highlight" endpoints picked for the demo; the `/events/<top-10>` pages render their sequence diagrams without console errors; local search returns hits for "create work order", "Sparkplug", "progress init"; mobile-Safari rendering is acceptable on a phone.

**Plans**: TBD

**UI hint**: no

**Risks**:

- **Last-minute mirror freshness** (Pitfall 4.7) — the GitLab → GitHub mirror runs every 5 min by default. The 09:30 May 15 manual force-push and SHA-match verification are non-optional. If S1 or any other workstream pushes to GitLab `DEV` after the freeze, this phase has to re-run.
- **Anchor-fragment dead links** (Pitfall 1.4) — VitePress's built-in dead-link checker silently passes broken `#section` anchors. Without `lychee` (or equivalent) in the final pass, half the events-reference cross-references can ship broken. Make this a hard CI gate, not a manual smoke test.
- **Webinar-day pressure to fix things** — the temptation to push a "small content fix" to GitLab `DEV` at 09:55 May 15 will break the SHA freeze. Treat May 14 18:00 → May 15 11:00 as a no-deploy window. Any fixes go to a `post-launch` branch.
- **Custom domain ambition** (Pitfall 4.8) — surface this risk one final time: do NOT wire `docs.progresslab.it` in this phase. The DNS / HTTPS lead time exceeds the freeze window.

---

## Out of Scope

See [`REQUIREMENTS.md`](REQUIREMENTS.md) `## v2 Requirements` and `## Out of Scope` for the deferred-and-explicitly-excluded list. Notable exclusions surfaced during phase analysis:

- Embedded L2 (in-platform help drawer) — EMBED-01/02 — multi-week scope.
- km/ wiki conversion — KM-01/02 — internal-only.
- i18n / vue-i18n integration — I18N-01..03 — multi-week.
- Custom subdomain (docs.progresslab.it) — POL-01.
- Algolia DocSearch live (replacing MiniSearch) — POL-02.
- Mermaid flowcharts for all 50+ events — COV-02 — top ~10 only for v1.
- Backend `except:` / `print()` refactors — explicitly out of docs workstream scope; tracked elsewhere.

## Coverage Validation

| Category | Count | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|----------|------:|--------:|--------:|--------:|--------:|
| MIR | 8 | 7 (MIR-01..07) | — | — | 1 (MIR-08) |
| API | 8 | — | 8 (API-01..08) | — | — |
| EVT | 6 | — | 6 (EVT-01..06) | — | — |
| CLI | 4 | — | — | 4 (CLI-01..04) | — |
| USER | 7 | — | — | 7 (USER-01..07) | — |
| ADM | 4 | — | — | 4 (ADM-01..04) | — |
| SITE | 12 | 11 (SITE-01..10, SITE-12) | — | — | 1 (SITE-11) |
| **Total** | **49** | **18** | **14** | **15** | **2** |

**49 / 49 v1 requirements mapped, 0 unmapped ✓**

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Scaffold & Public Foundation | 3 / 3 | Plan files complete; live-deploy verification pending maintainer mirror push | — (live verify pending) |
| 2. Code-Grounded Reference | 0 / TBD | Not started | — |
| 3. Human-Facing Content | 0 / TBD | Not started | — |
| 4. Launch Readiness | 0 / TBD | Not started | — |

---

*Roadmap created: 2026-04-29 by `/gsd-roadmapper` against [`PROJECT.md`](PROJECT.md), [`REQUIREMENTS.md`](REQUIREMENTS.md), [`research/PITFALLS.md`](research/PITFALLS.md).*
