# Phase 1: Scaffold & Public Foundation - Context

**Gathered:** 2026-04-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Public-facing skeleton exists. By the end of this phase:

- GitHub mirror at `github.com/ProgressLabIT/progress-platform` is live, branch-protected, with Issues + Discussions on, Wiki off, Private Vulnerability Reporting on, and topics set for discoverability.
- OSS table-stakes ship in main repo root: Apache 2.0 `LICENSE`, mirror-honest `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` (Contributor Covenant v2.1), minimal `SECURITY.md`, `README.md` rewritten to Pitfall 4.4 structure with mirror banner.
- VitePress site at `docs/` of main repo (canonical: `docs/` is owned exclusively by VitePress — no internal content under it). Site builds and deploys to `https://progresslabit.github.io/progress-platform/` via GitHub Actions on every push to mirror `DEV`, in under 10 minutes.
- URL contract is locked: `/api/<router>/<endpoint>/`, `/events/<domain>/<event>/`, `/cli/<command>/`, `/users/<area>/`, `/admins/<area>/`. Phase 1 ships top-nav landings + one representative stub per section (5 + 5 = 10 routable pages); deeper enumeration is Phase 2/3 work that fills into the contract.
- Hand-written `themeConfig.sidebar` is the only navigation source; default theme + CSS-variable brand color only; MiniSearch local search enabled; `vitepress-plugin-mermaid` (with ELK renderer available) wired; `vitepress-openapi` installed against a placeholder `openapi.json` artifact slot (populated in Phase 2); sitemap configured against the canonical hostname; lychee CI gate against built `dist/` runs on every PR.

Every later phase writes content into this scaffold — they do not touch infrastructure.

</domain>

<decisions>
## Implementation Decisions

### License & OSS scaffolding

- **D-01:** **License = Apache 2.0** (replaces existing MIT `LICENSE`). Rationale: Pitfall 4.1 — explicit patent grant for B2B/Industry-4.0 enterprise audience, contributor-friendly, AGPL-bans-friendly. Update `LICENSE` file, add `license: Apache-2.0` to any package metadata in `docs/package.json` (VitePress) and a SPDX header pattern is **not** required for v1 (post-launch tooling).
- **D-02:** **Private Vulnerability Reporting (PVR) toggle on**, plus a minimal **`SECURITY.md`** (≤15 lines) that points at PVR, states "best-effort response, no SLA", and lists the supported version as "current `DEV` only". **No 72h ack commitment** — solo-maintainer footgun. **No supported-version table** — single shipping line.
- **D-03:** **`.github/PULL_REQUEST_TEMPLATE.md`** included — explicit "direct PRs against this mirror cannot be merged; please file an issue and attach a patch" notice. This is automation, not a commitment.
- **D-04:** **No issue templates** for v1. Plain Issues form. Triage capacity is solo-maintainer; templates create overpromise. Revisit post-launch when contribution velocity warrants.

### docs/ directory layout

- **D-05:** **`docs/superpowers/`** (existing 2-file directory: `specs/2026-04-15-custom-data-design.md` and `plans/2026-04-15-custom-data.md`) is **deleted** early in Phase 1 (`git rm -r docs/superpowers/`). Rationale: shipped feature, planning artifacts no longer needed. Result: VitePress owns `docs/` root with no collision.
- **D-06:** **VitePress lives at `docs/` root**, **not** `docs/site/`. Source path `docs/api/...` maps to URL path `/progress-platform/api/...` (project Pages base). Confirms PROJECT.md / ROADMAP.md as written.

### Skeleton page strategy

- **D-07:** **Section landings + 1 representative stub each.** Phase 1 ships 10 routable pages:
  - 5 top-nav landings: `/api/`, `/events/`, `/cli/`, `/users/`, `/admins/`
  - 5 representative stubs (concrete URLs that prove contract resolution & exercise lychee):
    - `/api/production/jobs/start/` (representative public-API endpoint)
    - `/events/production/job-started/` (representative event)
    - `/cli/init/` (representative CLI command)
    - `/users/production/` (representative module walkthrough)
    - `/admins/deployment/` (representative admin page)
  Each stub is one-line "Coming soon — Phase 2/3" frontmatter + visible heading. **lychee CI gate validates real cross-link patterns** in Phase 1 so the dead-link contract is exercised, not just compiled.
- **D-08:** **URL contract = patterns + the 10 example anchors above.** Full enumeration of all endpoints / all events / all modules is Phase 2/3 generator output, not Phase 1 deliverable. Phase 1 locks the **shape** of every URL; Phase 2/3 fills the contents.

### README rewrite & Sparkplug demo S5 coordination

- **D-09:** **Phase 1 ships full README structure** per Pitfall 4.4: one-sentence pitch + status badges (license, docs site, GitHub release placeholder, Discussions) + mirror banner (Pitfall 4.2 wording) + "Try it in 5 minutes" `progress init` block + single docs-site link + 1-paragraph architecture pointer + 1-paragraph contributing pointer + license footer. Cap at ~150 lines.
- **D-10:** **5-minute `progress init` block** is a **placeholder** pinned to the Sparkplug demo workstream's currently-locked CLI surface (`progress init`, `progress restore`, `progress tap`). **Daily sync with S5** to re-pin during phase 2/3 if S5 changes. **Phase 4 launch-prep does the final lock** against the May 14 fresh-VM rehearsal script. Phase 1 is not blocked on S5 timing.
- **D-11:** **Demo GIF / asciinema recording is Phase 4 deliverable** (captured during the May 14 fresh-VM rehearsal — same script as the README block). Phase 1 README has a placeholder image slot only. Avoids re-recording churn.

### GitHub org / Pages URL canonical

- **D-12:** **Canonical org = `ProgressLabIT`** (matches existing local git remote). PROJECT.md / ROADMAP.md / REQUIREMENTS.md / STATE.md currently reference `progresslab` (lowercase, no `IT` suffix) — these are corrected as a Phase 1 sub-task before any URL is hardcoded into VitePress config or success criteria.
- **D-13:** **Pages URL = `https://progresslabit.github.io/progress-platform/`**. **VitePress `base` = `/progress-platform/`**. **Sitemap `hostname` = `https://progresslabit.github.io/progress-platform/`**. **Source-code permalink template = `https://github.com/ProgressLabIT/progress-platform/blob/<sha>/<path>`** — never gitlab.com (SITE-08).

### CONVENTIONS.md (folded from STATE.md todo)

- **D-14:** **`.planning/workstreams/docs/CONVENTIONS.md`** is authored as part of Phase 1 (folded from STATE.md todo #3). Initial scope:
  - Endpoint docstring shape (one-line summary + multi-line markdown description; Pitfall 2.x)
  - AI drafting prompt scaffold (Pitfall 5.1 grounding rule + Pitfall 5.3 anti-bland-prose template)
  - Mermaid `sequenceDiagram` transaction-boundary convention (Pitfall 3.2 — `rect` for `apply`, `Note` for commit)
  - Curation gate definition (Pitfall 5.4 — non-author review pass)
  Initial version stubs the prompt scaffold; Phase 2/3 sessions fill it in as patterns crystallize.

### Mirror push trigger (folded from STATE.md todo)

- **D-15:** **`CONTRIBUTING.md` mirror section** explicitly documents the GitLab `Repository → Mirroring repositories → Update now` flow (Pitfall 4.7) so Phase 4's launch-day SHA-match script can rely on it. Includes the verification command `git ls-remote https://github.com/ProgressLabIT/progress-platform DEV` for any maintainer to run.

### Claude's Discretion

- **GitHub Actions workflow specifics** — concurrency `cancel-in-progress`, build cache strategy (npm cache + VitePress cache), pnpm vs yarn vs npm pin (likely npm to match existing `package.json` patterns elsewhere; researcher will check). No PR preview deploys for v1 (cost vs value; revisit post-launch).
- **VitePress version pin** — researcher selects latest stable VitePress 1.x with confirmed `vitepress-openapi` + `vitepress-plugin-mermaid` compatibility (Pitfalls 1.1 + 3.x).
- **Mermaid plugin version pin** — researcher selects an `vitepress-plugin-mermaid` version that supports both default and ELK renderer (Pitfall 3.x dark-mode / >20-node patterns) and pins it.
- **Topics set on GitHub repo** — Pitfall 4.6 list (`manufacturing`, `mes`, `iiot`, `sparkplug-b`, `industry40`, `fastapi`, `vue3`) is the default; user can edit during launch-prep.
- **Branch protection rule details** — minimum: no force-push, no deletions on `DEV`, status checks required (Pages deploy + lychee). Researcher confirms exact GitHub UI rule names.

### Folded Todos

- **CONVENTIONS.md authoring** (STATE.md todo #3) — folded into D-14 above.
- **`security@progresslab.it` email alias** (STATE.md todo #5) — folded into D-02 (PVR replaces email-channel SLA so the alias is now optional, not blocking).
- **Confirm license choice** (STATE.md todo #4) — resolved by D-01 (Apache 2.0).
- **Document mirror-update trigger** (STATE.md todo derived from PROJECT.md Phase 0 risk) — folded into D-15.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Workstream-locked context

- `.planning/workstreams/docs/PROJECT.md` — milestone goal, locked decisions, constraints, OSS table-stakes scope.
- `.planning/workstreams/docs/REQUIREMENTS.md` — 49 v1 requirements; Phase 1 owns MIR-01..07 + SITE-01..10 + SITE-12.
- `.planning/workstreams/docs/ROADMAP.md` §"Phase 1: Scaffold & Public Foundation" — goal, success criteria (5), risks, depends-on.
- `.planning/workstreams/docs/STATE.md` §"Locked Decisions" + §"Tooling Decisions (from PITFALLS.md research)" — VitePress, MiniSearch, vacuum, lychee, vitepress-openapi, vitepress-plugin-mermaid, hand-written sidebar, default theme.

### Pitfalls research (phase-scoped)

- `.planning/workstreams/docs/research/PITFALLS.md` §1.2 — auto-sidebar plugins as false economy → hand-written `themeConfig.sidebar`.
- `.planning/workstreams/docs/research/PITFALLS.md` §1.3 — MiniSearch as v1 default; Algolia DocSearch parallel application.
- `.planning/workstreams/docs/research/PITFALLS.md` §1.4 — `lychee` as second-pass dead-link CI (VitePress built-in checker misses anchors).
- `.planning/workstreams/docs/research/PITFALLS.md` §1.5 — default theme + CSS variables only; no `Layout.vue` override.
- `.planning/workstreams/docs/research/PITFALLS.md` §1.7 — sitemap hostname configured day one; submit to Search Console + Bing post-launch.
- `.planning/workstreams/docs/research/PITFALLS.md` §1.8 — URL contract locked before any markdown lands; GitHub Pages has no server-side redirects.
- `.planning/workstreams/docs/research/PITFALLS.md` §4.1 — Apache 2.0 license rationale (D-01).
- `.planning/workstreams/docs/research/PITFALLS.md` §4.2 — mirror-honest CONTRIBUTING.md template (verbatim).
- `.planning/workstreams/docs/research/PITFALLS.md` §4.3 — SECURITY.md + PVR; **D-02 deviates** (no SLA, no version table).
- `.planning/workstreams/docs/research/PITFALLS.md` §4.4 — README "5-minute test" structure (D-09).
- `.planning/workstreams/docs/research/PITFALLS.md` §4.5 — demo GIF deferred to Phase 4 (D-11) — **deviation from "Phase 0" recommendation, justified by S5 rehearsal capture**.
- `.planning/workstreams/docs/research/PITFALLS.md` §4.6 — GitHub repo settings checklist (Issues, Discussions, Wiki, branch protection, topics, About URL).
- `.planning/workstreams/docs/research/PITFALLS.md` §4.7 — GitLab mirror-update trigger (D-15).
- `.planning/workstreams/docs/research/PITFALLS.md` §4.8 — no custom domain in v1 (informational).

### Codebase maps (read for scaffold integration)

- `.planning/codebase/STACK.md` — Vue/Vite stack alignment confirms VitePress as natural fit.
- `.planning/codebase/STRUCTURE.md` — repo layout (where `docs/` sits relative to `backend/`, `webapps/`, `cli/`).
- `.planning/codebase/CONVENTIONS.md` — existing project conventions (frontend patterns); informs D-14 authoring style.

### Cross-workstream

- `.planning/workstreams/sparkplug-demo/PROJECT.md` — owns CLI surface (S4) + 5-minute README quickstart (S5). Phase 1 placeholder block (D-10) syncs against S5's currently-locked CLI surface.
- `.planning/workstreams/sparkplug-demo/decisions/0002-*.md` (NATS subject taxonomy, if present) — not Phase 1 critical, but events-reference cross-links (Phase 2) will reference it; mention in skeleton placeholders.

### Source code touch points

- `LICENSE` — current MIT, replaced by Apache 2.0 (D-01).
- `README.md` — current architecture-wall, rewritten per Pitfall 4.4 (D-09).
- `docs/superpowers/` — deleted (D-05).
- `cli/` (Typer commands `progress init / restore / tap`) — Phase 1 reads to lock the README placeholder block; does not modify.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- **Existing `LICENSE` (MIT)** — git-tracked file; Apache 2.0 replacement is a single-file change with a clear blame trail.
- **Existing `README.md`** — architecture content (lines 1-80+ inspected) is high-quality but mis-structured for OSS visitor; reusable as the linked `ARCHITECTURE.md` after extraction. Trim to a 1-paragraph pointer in the new README.
- **`.gitlab-ci.yml`** — tag-triggered Docker image build pipeline (`v*.*.*`). Phase 1 leaves this unchanged. The mirror sync is GitLab-side configuration (Repository → Mirroring), not a `.gitlab-ci.yml` job.
- **Local git remote `github`** — already points at `https://github.com/ProgressLabIT/progress-platform.git`. Mirror push target exists; the GitLab → GitHub mirror configuration on the GitLab repo settings UI is the missing wiring (one-time admin step).

### Established Patterns

- **Single-source-of-truth markdown convention** — `.planning/`, `km/`, `CLAUDE.md`, and existing `docs/superpowers/` all use plain markdown. VitePress preserves the convention for the public site.
- **Vue/Vite stack alignment** — webapps already on Vue 3 + Quasar/Vite; VitePress (Vue 3 + Vite) is the natural fit and what PROJECT.md locks.
- **Existing GitLab CI tag-triggered builds** — Phase 1 does not touch this. GitHub Actions deploy runs only on the GitHub mirror, triggered by mirror push.

### Integration Points

- **`docs/` ↔ `backend/api/endpoints/`** — Phase 1 stub `/api/production/jobs/start/` references `backend/api/endpoints/production.py:start_job` for the source-link template (not yet wired; concrete in Phase 2 via `vitepress-openapi`).
- **`docs/` ↔ `backend/api/events/`** — Phase 1 stub `/events/production/job-started/` references `backend/api/events/production/job_started.py` for the source-link template.
- **`docs/` ↔ `cli/`** — Phase 1 stub `/cli/init/` references `cli/` Typer command for the source-link template; deeper integration via `pytest-markdown-docs` is Phase 3.
- **README ↔ Sparkplug S5** — placeholder block reads S5's currently-locked `progress init` invocation; daily sync.
- **`.github/` ↔ GitLab CONTRIBUTING.md** — CONTRIBUTING.md mirror section documents the GitLab-side mirror trigger; the script `scripts/verify_mirror.sh` is Phase 4 deliverable but its existence is committed-to-be in CONTRIBUTING.md prose.

</code_context>

<specifics>
## Specific Ideas

- **README structure verbatim from Pitfall 4.4** — the 8-section structure (pitch + badges + mirror banner + 5-min block + docs link + arch link + contributing link + license) is treated as the contract; planner may not reorder sections without surfacing as a deviation.
- **CONTRIBUTING.md banner wording verbatim from Pitfall 4.2** — the three-paragraph template (canonical GitLab + read-only mirror + Issues/Discussions/Patches flow) ships as-is. This is the #1 OSS-mirror confusion source; pinned.
- **Repo topics from Pitfall 4.6** — `manufacturing`, `mes`, `iiot`, `sparkplug-b`, `industry40`, `fastapi`, `vue3`. Discoverability default; user can refine during launch-prep.
- **`themeConfig.search.provider = 'local'`** — explicit MiniSearch invocation, not Algolia; codified in `docs/.vitepress/config.ts`.
- **`base: '/progress-platform/'`** — VitePress base path locked in this phase. Any future custom-domain switch is post-launch and changes this single config field.
- **Solo-maintainer reality is a first-class constraint** — D-02 / D-04 / D-15 are all sized against "what one person can credibly deliver". Future scope creep that adds SLAs or template overhead must surface as an explicit deviation.

</specifics>

<deferred>
## Deferred Ideas

- **Custom domain `docs.progresslab.it`** — Pitfall 4.8; post-launch only. Listed for completeness; do not wire in v1.
- **Algolia DocSearch live** — POL-02 in REQUIREMENTS.md v2. Application sent in parallel with v1 (per STATE.md); switch when approved post-launch.
- **Versioned docs (per-release snapshots)** — POL-03; not v1.
- **`/v1/` URL prefix for future versioning** — considered, rejected. v1 ships at root; if versioning is added post-launch, the v1 docs become `/v1/` via a one-time content move + 301-equivalent client-side redirect map (Pitfall 1.8 community pattern).
- **PR preview deploys** — extra GitHub Actions cost + complexity; not v1. Production deploy on push-to-DEV is sufficient.
- **Issue templates** — D-04 deferred; revisit post-launch when contribution velocity warrants.
- **SECURITY.md SLA / supported-version table** — D-02 deferred; revisit when team size > 1.
- **Demo GIF / asciinema in Phase 1** — D-11 deferred to Phase 4; rehearsal capture avoids re-record churn.
- **Sponsorship link / FUNDING.yml** — Pitfall 4.6 mentions; user has no sponsorship intent for v1, skip.
- **Auto-sidebar plugin** — Pitfall 1.2; post-launch optimization once content stabilizes.
- **`Layout.vue` theme override** — Pitfall 1.5; post-launch only.
- **embedded L2 docs in platform shell** — EMBED-01/02; multi-week scope, deferred entirely (PROJECT.md locked).

### Reviewed Todos (not folded)

- (none — all STATE.md todos either folded or already covered by Phase 1 deliverables.)

</deferred>

---

*Phase: 01-scaffold-public-foundation*
*Context gathered: 2026-04-29*
