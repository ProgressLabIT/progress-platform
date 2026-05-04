# Pitfalls & Best Practices — Progress Platform Docs Workstream

**Domain:** OSS technical documentation site (VitePress + FastAPI/Pydantic + Mermaid + GitHub-mirror)
**Researched:** 2026-04-29 (16 days to May 15 launch)
**Overall confidence:** HIGH on tooling specifics; MEDIUM on launch-window judgement calls
**Locked decisions (not revisited):** VitePress, GitHub Pages on mirror, `docs/` co-located, Mermaid for events, AI-drafted authoring, English only, online-only L2, km/ deferred

---

## Section 1 — VitePress for technical/API docs

### 1.1 Picking the wrong OpenAPI renderer for VitePress

**What goes wrong:** Wiring Swagger UI / RapiDoc / ReDoc into VitePress as an iframe or via a custom Vue component, then losing client-side routing, search indexing, frontmatter integration, and dark-mode parity. End up with two visual languages on one site.

**Why it happens:** Default reflex is "Swagger UI is the API docs". VitePress is Vue-native; iframes break it.

**Mitigation:** Use **`vitepress-openapi`** (enzonotario, v0.1.20 as of Apr 2026, MIT, used in production since 2023). It's the only VitePress-native option with a mature component set (`OASpec`, `OAOperation`, `useSidebar`, `groupByTags`), playground, code samples, and deep-link `$ref` resolution. Avoid Swagger-UI-in-iframe and the unmaintained `vitepress-plugin-openapi`.

**Confidence:** HIGH. **Phase:** L0 (API foundation).

---

### 1.2 Auto-sidebar plugins as a false economy

**What goes wrong:** Drop in `vitepress-plugin-auto-sidebar` or `vitepress-sidebar`, get "free" navigation, then fight ordering bugs, mis-titled folders, and excluded-page rules for the rest of the project. Page order becomes alphabetical when narrative order matters.

**Why it happens:** The directory tree is a poor source of truth for documentation flow. "Getting Started" must come before "Architecture" regardless of filename.

**Mitigation:** **Hand-write `themeConfig.sidebar`** as a typed array in `.vitepress/config.ts`. ~20 entries × 5 sections is trivially maintainable for v1. Auto-sidebar is a post-launch optimization once content stabilizes. If you must auto-generate, use frontmatter `order:` + `noneArticle:` and clear `themeConfig.sidebar = []` first or it silently fails.

**Confidence:** HIGH. **Phase:** Site infrastructure.

---

### 1.3 Local search vs Algolia DocSearch — picking the wrong default

**What goes wrong:** Apply for Algolia DocSearch (free tier for OSS) the day before launch, application is queued, ship without search.

**Why it happens:** DocSearch approval is community-curated and not instant — typical wait is days-to-weeks.

**Mitigation:** **Ship v1 with the built-in MiniSearch local provider** (`themeConfig.search.provider = 'local'`, zero config, indexes at build time, works offline). Apply for Algolia DocSearch in parallel; switch post-launch when approved. MiniSearch is what the Vite, Vitest, Pinia, VueUse, and UnoCSS docs all use as their starter; it's good enough for 100s of pages.

**Confidence:** HIGH. **Phase:** Site infrastructure.

---

### 1.4 Trusting VitePress's dead-link checker

**What goes wrong:** `vitepress build` reports "0 dead links", site ships, half the events-reference cross-links 404 because they were hash-fragment links to anchors that didn't exist.

**Why it happens:** VitePress dead-link detection ignores hash fragments (`./events.html#job_started` is not validated against the target page's anchors — confirmed bug, multiple open issues #354, #3774, #4419).

**Mitigation:** Add a **second-pass crawler in CI** — `lychee` or the `gaurav-nelson/github-action-markdown-link-check` GitHub Action, run against the built `dist/` after `vitepress build`. Treat any dead anchor link as a build failure. Do **not** use `ignoreDeadLinks: true` to silence the warnings — that hides real breakage.

**Confidence:** HIGH. **Phase:** Site infrastructure (CI step).

---

### 1.5 Custom theme override creep

**What goes wrong:** Start with one custom Vue component slot, end up with a forked default theme, then VitePress 1.x → 2.x bumps break the site.

**Why it happens:** Theme overrides are seductive — they look like Vue, devs treat them like app code.

**Mitigation:** **Stay on the default theme for v1**. Use `Layout.vue` slots (`doc-before`, `doc-after`, `nav-bar-content-before`) — never replace `Layout` or `Theme.enhanceApp` until post-launch. A single brand color via CSS variables (`--vp-c-brand-1`) is fine; component overrides are not.

**Confidence:** HIGH. **Phase:** Site infrastructure.

---

### 1.6 Code-block UX: shipping without tabs, copy, and language groups

**What goes wrong:** Single-language code blocks for Python-only examples, then the integrator audience asks "how do I curl this" and there's no answer.

**Mitigation:** Use VitePress's built-in `::: code-group` for **curl + Python + JS** triplets on every public-API endpoint sample. Enable `markdown.lineNumbers = true` site-wide. Copy button is on by default in default theme — verify it doesn't include line numbers in the clipboard payload (open issue #884 — fixed in recent versions, validate on whichever VitePress major you pin).

**Confidence:** HIGH. **Phase:** L0 (when authoring endpoint examples).

---

### 1.7 No sitemap → invisible to Google after launch

**What goes wrong:** Site goes live, GitHub Pages serves it, no `/sitemap.xml`, search engines don't crawl, the OSS launch gets ~zero organic traffic.

**Why it happens:** VitePress sitemap generation is not on by default — has to be configured under `sitemap: { hostname: 'https://...' }` in site config (built-in since 1.0).

**Mitigation:** Set `sitemap.hostname` in `.vitepress/config.ts` from day one. Add a `robots.txt` to `public/` with the sitemap URL. Submit to Google Search Console + Bing Webmaster Tools the day the site goes live.

**Confidence:** HIGH. **Phase:** Site infrastructure.

---

### 1.8 No redirect strategy on a static host

**What goes wrong:** Mid-launch you rename `events/inventory.md` to `events/warehouse.md` because the audience says "warehouse", every external link breaks.

**Why it happens:** GitHub Pages is pure static — no `.htaccess`, no `_redirects` (that's Netlify), no server-side 301s.

**Mitigation:** Adopt a **stable URL contract** before publishing: `/api/<router>/<endpoint>`, `/events/<domain>/<event>`, `/cli/<command>`, `/users/<area>`, `/admins/<area>`. Encode this in PROJECT.md. Treat URL renames as breaking changes post-launch. If a rename is unavoidable, ship a thin client-side redirect via a `.vitepress/theme/index.ts` `enhanceApp` hook reading a hand-maintained redirect map (community pattern, see vitepress issue #4160).

**Confidence:** HIGH. **Phase:** Phase 0 + L0 (URL conventions locked before authoring).

---

## Section 2 — FastAPI docstring + Pydantic patterns producing excellent OpenAPI

### 2.1 Endpoint docstrings as the only documentation source

**What goes wrong:** Devs write `"""Create a work order."""` as the docstring, ship it, OpenAPI shows a one-line summary and nothing else. Audience reads `/redoc`, sees nothing actionable, leaves.

**Why it happens:** FastAPI uses the **first line** as `summary` and the **rest** as `description` (markdown rendered). One-liners produce one-liners.

**Mitigation:** Adopt a **mandatory docstring shape** for every public endpoint:

```python
@router.post("/work-order", response_model=APIResponse[WorkOrderRecord], responses={
    409: {"model": ErrorDetail, "description": "Work order code already exists"},
    404: {"model": ErrorDetail, "description": "Product not found"},
})
async def create_work_order(new_wo: WorkOrderNew):
    """
    Create a new work order.

    Generates a `wo_code` from the system counter if not supplied; rejects
    duplicates with HTTP 409. On success, persists a `WorkOrder` document
    and any phase-specific `Job` documents in a single ArangoDB transaction.

    **Emits:** `WorkOrderCreatedEvent`

    **Required scope:** `production` or `admin`
    """
```

Encode this shape in a `.planning/workstreams/docs/CONVENTIONS.md` snippet so all four sessions write to the same template.

**Confidence:** HIGH. **Phase:** L0.

---

### 2.2 `response_model=` missing → OpenAPI shows raw `Any`

**What goes wrong:** Endpoint returns a hand-built dict; OpenAPI declares `additionalProperties: true`; consumers see no schema; `vitepress-openapi` shows a useless "object" placeholder.

**Why it happens:** Legacy endpoints (this codebase has plenty — see `auth.py`, `production.py`) return `JSONResponse(content=jsonable_encoder(...))` with no `response_model=`.

**Mitigation:** For the **L0 sweep**, every public endpoint must declare `response_model=APIResponse[X]` in the decorator (already a pattern in `utils/api.py`). Generic envelope avoids reshaping handler logic. If response_model is genuinely impossible (e.g. file streaming), declare `responses={200: {"content": {"application/octet-stream": {}}}}` so the schema is intentional, not accidental.

**Confidence:** HIGH. **Phase:** L0.

---

### 2.3 Pydantic `Field(description=…)` neglect

**What goes wrong:** `class WorkOrderNew(BaseModel): wo_code: str | None = None` produces an OpenAPI field with no description. Consumer guesses what `wo_code` is.

**Mitigation:** **Every field** on a public-surface model gets `Field(default, description="...", examples=[...])`. Skip docstrings on Pydantic models — they're harder to surface in OpenAPI than `Field()` metadata. For Pydantic v2, use `model_config = ConfigDict(json_schema_extra={"examples": [...]})` for whole-model examples (the v1 `Config.schema_extra` syntax is deprecated and produces sparse output — discussed in fastapi/fastapi#11137).

**Confidence:** HIGH. **Phase:** L0.

---

### 2.4 Pydantic v2 `Optional[X]` regression in OpenAPI

**What goes wrong:** Upgrade from Pydantic v1 to v2, OpenAPI now produces `anyOf: [{type: string}, {type: null}]` instead of the v1 `{type: string, nullable: true}`. Generated SDKs and Swagger UI render this awkwardly. Discussed in fastapi/fastapi#9900.

**Mitigation:** Already on Pydantic v2 (per STACK.md, `pydantic==2.*`). Accept the `anyOf`-with-null shape — it's correct OpenAPI 3.1, and `vitepress-openapi` handles it. Do not try to "fix" it back to nullable. If a consumer complains, tell them to upgrade their generator.

**Confidence:** HIGH. **Phase:** None — informational.

---

### 2.5 `tags` strings without `tags_metadata`

**What goes wrong:** Endpoints declare `tags=['Production']`, Swagger UI groups them, but the group has no description, no order, no external link. ReDoc sidebar is alphabetical and unfriendly.

**Why it happens:** Many tutorials skip `tags_metadata` because it's optional.

**Mitigation:** Define `openapi_tags` once in `main.py`:

```python
tags_metadata = [
    {"name": "Production", "description": "Work orders, jobs, phases. Emits production events.",
     "externalDocs": {"description": "Events reference", "url": "/events/production/"}},
    # ...
]
app = FastAPI(openapi_tags=tags_metadata, root_path=config.api_root_path)
```

Pin tag order — Swagger UI respects `tags_metadata` order. The `externalDocs` entries become deep links from the API reference into the events reference, satisfying L1's "cross-references from API endpoints → events they emit" requirement.

**Confidence:** HIGH. **Phase:** L0.

---

### 2.6 Bare `except:` clauses re-raising as 500 with `traceback.format_exc()` in the body

**What goes wrong:** Existing endpoints in this codebase (audit: `auth.py:49–56`, `production.py:108–118`, many more) catch every exception, return 500 with the **server traceback in the response body**. This is both a security problem (information disclosure) and an OpenAPI documentation problem (the actual error responses aren't documented).

**Mitigation (within docs scope):** L0 is **docstrings + types only, no refactor** — per locked PROJECT.md constraint. So: do **not** rip these out. Instead, document the *actual* error contract on each endpoint via `responses={...}` so consumers know to expect 4xx for known cases and 5xx with opaque payloads otherwise. Add a top-level "Error Handling" page in admin docs noting the known issue is tracked separately (point at the issue tracker). Note this in PITFALLS for the post-launch full-sweep workstream.

**Confidence:** HIGH on the constraint; MEDIUM on whether reviewers will accept "documented broken behavior" — surface this risk to the workstream owner. **Phase:** L0 (document) + post-launch (fix).

---

### 2.7 Skipping OpenAPI quality validation in CI

**What goes wrong:** Schema looks fine on May 14, ships, then a consumer points out 30 endpoints have no descriptions, three have duplicate operationIds, two reference non-existent schemas.

**Mitigation:** Add **Spectral** or **vacuum** to CI as a docs-build gate:

- **Spectral** (Stoplight, JS, official OpenAPI ruleset) — well-known, works with custom rulesets.
- **vacuum** (Go, Spectral-compatible rulesets, ~10× faster, single binary, no Node) — better for a Python repo's CI image.

Recommendation: **vacuum** with the default ruleset + a custom rule requiring `description` on every operation and `description` on every property. CI step: `vacuum lint openapi.json --ruleset .spectral.yaml --fail-severity error`. `openapi-format` is a separate tool for sorting/normalizing the spec — useful but not a quality gate; skip for v1.

**Confidence:** HIGH. **Phase:** L0 (CI gate).

---

### 2.8 Generating OpenAPI from a running app vs build-time export

**What goes wrong:** Docs site CI starts the FastAPI app + ArangoDB + NATS just to fetch `/openapi.json`. CI gets slow, flaky, and Sparkplug-demo's parallel docker-stack creates port conflicts.

**Mitigation:** Use `app.openapi()` directly in a small **build-time script** (`scripts/export_openapi.py`) that imports `from main import app` and dumps `json.dumps(app.openapi())` to `docs/.vitepress/openapi.json`. No DB or NATS needed because OpenAPI generation is pure introspection. The script runs in the docs CI job, output is committed (or generated on each build — pick one and stick with it; committed avoids drift confusion at the cost of merge churn).

**Confidence:** HIGH. **Phase:** L0 (CI step).

---

## Section 3 — Mermaid flowcharts for event-sourcing/state-machine systems

### 3.1 Choosing `flowchart` when `sequenceDiagram` is correct (and vice versa)

**What goes wrong:** Document `JobStartedEvent` as a flowchart with arrows from "User" to "Endpoint" to "Event" to "DB" to "NATS", lose all temporal/transactional information. Audience can't tell what's atomic vs what's async.

**Why it happens:** Flowchart is the default mental model for "diagrams". For an event with `pre_processing → apply (transactional) → post_processing → NATS publish (post-commit)`, flowcharts hide the transaction boundary.

**Mitigation:** **Default to `sequenceDiagram` for events**. Sequence diagrams have native primitives for the exact concerns:

- `participant` for actor / endpoint / event / DB / NATS
- `Note over Event,DB: ArangoDB transaction` to mark the atomic boundary
- `rect rgb(...)` block to shade the transactional region
- `-->` for async (post_processing → NATS)
- `alt / else` for precondition branches

Use `flowchart` only when the event has **no temporal structure** (rare for this codebase). Use `stateDiagram-v2` for documenting Job state machine, Batch lifecycle — places where the *entity* has states, not where the *event* runs.

**Confidence:** HIGH. **Phase:** L1 (events reference handcraft).

---

### 3.2 Implicit transaction boundaries

**What goes wrong:** Diagram shows `apply()` and `post_processing()` as two arrows; reader doesn't know the first is inside a transaction and the second is fire-and-forget after commit. When `post_processing` fails (NATS disconnected), the reader assumes the event rolled back. It didn't (per `BaseEvent.save()` finally clause).

**Mitigation:** **Always render the transaction boundary explicitly.** Convention for this workstream:

- Open `rect rgb(232, 245, 233)` (light green) around `pre_processing` + `apply` + `store_event` calls.
- A `Note right of Event: commit_transaction` line marks the boundary.
- Anything after the rect is post-commit (NATS publish, fan-out events).
- Annotate `try/finally abort_transaction` for the failure path with `alt error`.

Document this convention once in `docs/events/_conventions.md` and link from every event page.

**Confidence:** HIGH. **Phase:** L1 (define convention before authoring top-10).

---

### 3.3 Mermaid render performance / correctness on large diagrams

**What goes wrong:** Top-10 events include `BatchCompletedEvent` which fans out 8 child events; the resulting flowchart has 50+ nodes and 4 levels of subgraphs. Renders at 2 fps on a phone, errors with "Cannot set properties of undefined" in nested subgraphs.

**Why it happens:** Default Dagre layout engine has known issues with deeply nested subgraphs. ELK is the workaround.

**Mitigation:** For any event diagram with `>20 nodes` or `>2 subgraph levels`, set `%%{init: {"flowchart": {"defaultRenderer": "elk"}}}%%` at the top of the diagram. Better: **decompose**. If `BatchCompletedEvent` fans out to 8 children, render the parent diagram showing one "spawns 8 child events (see below)" node, then render each child as its own diagram on the page. Avoid the temptation to put everything on one canvas.

**Confidence:** HIGH on technical fix; MEDIUM on decomposition guidance (judgement call). **Phase:** L1.

---

### 3.4 Mermaid in dark mode

**What goes wrong:** Site has a dark-mode toggle; Mermaid diagrams render with white background, look like a flashbang on dark theme.

**Mitigation:** Use `vitepress-plugin-mermaid` (emersonbottero) with VitePress's `appearance: 'dark'` integration — auto-detects body theme and re-renders. Validate on each diagram that text remains legible in both themes (subgraph labels and stroke colors are the usual offenders). For custom palettes, define them as CSS variables, don't hardcode hex into the diagram source.

Note: `vitepress-plugin-mermaid` has had dependency-version compatibility issues with newer VitePress majors (multiple GH discussions); pin compatible versions in `package.json`. Alternative: `vitepress-plugin-diagrams` (vuesence) generates SVG at build time with caching — no runtime Mermaid bundle, faster pages, no dark-mode toggle (would need rebuild). Pick `vitepress-plugin-mermaid` for v1 (interactive, simpler) and migrate to build-time SVGs post-launch if performance complaints arrive.

**Confidence:** MEDIUM (plugin compat is moving target — verify package.json compatibility before committing). **Phase:** Site infrastructure.

---

### 3.5 Auto-extracted "text-only" event entries become unstructured prose

**What goes wrong:** PROJECT.md says "all events documented; top ~10 with hand-crafted Mermaid; rest text-only". The auto-extractor produces 40 pages of `event_type | tx_collections | post_processing notes` blobs with no consistent shape.

**Mitigation:** **Define a strict template** for the auto-extracted pages. Every non-flowchart event page has the same H2 sections: `## Trigger`, `## Preconditions`, `## State changes`, `## Side effects (post_processing)`, `## Notifications (NATS subjects)`, `## Related events`. The extractor populates these by parsing `BaseEvent` subclass: docstring → trigger, `get_tx_collections()` → state changes, `post_processing()` source → side effects, `_notification_subtopic` → NATS subjects. Sections with no data are auto-filled with "_None._" — never omitted, so the page shape is uniform.

**Confidence:** HIGH. **Phase:** L1 (events reference).

---

## Section 4 — OSS launch under a 16-day window

### 4.1 Missing LICENSE → not actually open source

**What goes wrong:** Repo is public on GitHub on May 15. No LICENSE file. Legally, default copyright applies — visitors **cannot** legally use, copy, or redistribute. Industry-4.0 consultant audience notices immediately.

**Mitigation:** **Pick a license in week 1, not week 3.** Recommendation: **Apache 2.0** for a B2B platform (explicit patent grant, contributor-friendly, compatible with most enterprise legal review). MIT is fine if you want maximum permissiveness with no patent clause. Do **not** ship AGPL-3.0 if the goal is industry-consultant adoption — many enterprises have AGPL bans. Add `LICENSE` file in repo root + `license: Apache-2.0` in `package.json` + license badge in README.

**Confidence:** HIGH. **Phase:** Phase 0 (mirror & OSS table-stakes).

---

### 4.2 CONTRIBUTING.md that promises a flow you can't fulfill

**What goes wrong:** CONTRIBUTING.md says "Open a PR against `main`" — but `main` on GitHub is read-only mirror, PRs can't be merged. Contributors fork, send PRs, wait, get confused.

**Mitigation:** **CONTRIBUTING.md must be honest about the mirror.** Template:

> Progress Platform's canonical home is GitLab at `https://gitlab.com/progresslab/progress-platform`. **GitHub is a read-only mirror** maintained for discoverability. We accept contributions through:
>
> 1. **GitHub Issues** — bug reports and feature requests. Maintainers triage and may file the corresponding work item on internal GitLab.
> 2. **GitHub Discussions** — questions and design conversations.
> 3. **Patches** — please open an issue first; for code contributions, attach a patch to the issue. Direct PRs against the mirror cannot be merged here and will be closed with a pointer to the issue flow.
>
> We expect to revisit this flow once contribution velocity warrants a full GitLab→GitHub migration.

Pin this as the README banner too. This is the #1 source of confusion for visitors at OSS-mirror projects (per Mozilla, GNOME, FreeBSD historical patterns and GitLab issue gitlab-org#5823).

**Confidence:** HIGH. **Phase:** Phase 0.

---

### 4.3 No SECURITY.md → vulnerabilities reported as public issues

**What goes wrong:** Researcher finds a CVE-worthy bug, files a GitHub Issue, the bug becomes public before a patch ships. Reputational damage on launch week.

**Mitigation:** Ship `SECURITY.md` in repo root from day one. GitHub auto-links it from the security tab. Minimum content: contact email (`security@progresslab.it` — set up the alias before publishing), statement that you'll acknowledge in 72h, supported-version table. Enable **GitHub Private Vulnerability Reporting** in repo settings (free, no setup beyond the toggle). Reference: github.com/upptime/.github/SECURITY.md as a 30-line template.

**Confidence:** HIGH. **Phase:** Phase 0.

---

### 4.4 README that fails the "5-minute test"

**What goes wrong:** README is a wall of architecture text. Visitor lands, can't find how to *run the thing*, leaves. Webinar-driven traffic is the highest-bounce-rate audience you'll ever get.

**Mitigation:** README structure (top-down, max ~150 lines for v1):

1. **One-sentence pitch** + screenshot/GIF
2. **Status badges** — license, GitHub release tag, link to docs site, Discord/Discussions link
3. **Mirror banner** — "Canonical: GitLab. This is the public mirror."
4. **Try it in 5 minutes** — copy-pasteable `progress init` block
5. **Documentation** — single link to the VitePress site
6. **Architecture** (1 paragraph + 1 link to ARCHITECTURE.md)
7. **Contributing** (1 paragraph + 1 link to CONTRIBUTING.md)
8. **License**

The "Try it in 5 minutes" block must actually work on a fresh Linode VM — the Sparkplug-demo workstream's S5 session is rehearsing this; the docs README block is the public version of the same script. Coordinate with S5 to keep them in lockstep.

**Confidence:** HIGH. **Phase:** Phase 0.

---

### 4.5 Demo GIF / screenshots deferred to post-launch

**What goes wrong:** Webinar audience watches a polished live demo, clicks the GitHub link, lands on a README with no visuals, drop-off is severe.

**Mitigation:** Capture **one** terminal recording (asciinema → SVG via `agg`, or a 30s GIF) of `progress init` → web UI loading → UNS topology browser. Embed in the README "5 minutes" section. Uses the Sparkplug-demo S5 walkthrough script as source material — record once during a rehearsal, commit the SVG/GIF. Cost: 1 hour. Conversion uplift: substantial. Skipping this is the #1 regret of post-webinar OSS launches.

**Confidence:** MEDIUM (impact estimate, not the technique). **Phase:** Phase 0 / launch-week polish.

---

### 4.6 GitHub repo settings forgotten before going public

**What goes wrong:** Mirror repo goes public May 15. Wiki was never disabled — random old internal commits' wiki pages are crawlable. Discussions were never enabled — community has nowhere to ask questions, defaults to issues.

**Mitigation:** Pre-launch settings checklist (matches PROJECT.md §Active Phase 0):

- [ ] Wiki disabled
- [ ] Issues enabled, with **issue templates** (`bug`, `feature`, `question` — customized to mention "we triage from GitHub to GitLab")
- [ ] Discussions enabled with categories: Announcements (maintainers post), Q&A, Show and Tell, Ideas
- [ ] Branch protection on `main` (no force pushes, no deletions, status checks required even though merges happen via mirror push)
- [ ] Private Vulnerability Reporting on
- [ ] Sponsorship link off (unless you have one) — empty link is worse than no link
- [ ] Topics set: `manufacturing`, `mes`, `iiot`, `sparkplug-b`, `industry40`, `fastapi`, `vue3` — drives discoverability
- [ ] About-section URL points to the docs site, not back to GitLab (the canonical ref is in README, the link is for docs)

**Confidence:** HIGH. **Phase:** Phase 0.

---

### 4.7 Mirror push race against the webinar

**What goes wrong:** Last commit lands on GitLab `main` at 09:55 May 15; the GitLab→GitHub push mirror runs every 5 minutes; webinar starts 10:00 with a stale public mirror; first visitor on a screenshare hits a 404 on a doc link to a page that exists only on GitLab.

**Mitigation:** Three protections:

1. **Webinar freeze** — no merges to GitLab `main` for the 24h before the webinar. Coordinate with sparkplug-demo workstream.
2. **Manual trigger** — GitLab `Repository → Mirroring repositories → Update now` button is a one-click force-push. Hit it 30 minutes before the webinar.
3. **Verification** — script that diffs `git ls-remote gitlab main` vs `git ls-remote github main` and bails if SHAs don't match. Run as the webinar opens.

**Confidence:** HIGH. **Phase:** Launch-week.

---

### 4.8 Custom domain ambition

**What goes wrong:** Day before launch, attempt to wire `docs.progresslab.it` to GitHub Pages. DNS propagation, HTTPS cert via GitHub takes hours, lands at 09:30 May 15 with broken HTTPS warning.

**Mitigation:** **Ship on `progresslab.github.io/progress-platform/`** as PROJECT.md already locks. Custom domain is post-launch polish. If a vanity URL is non-negotiable, set up the CNAME **two weeks before launch**, not two days — GitHub's HTTPS provisioning can take up to 24h and is not retriable.

**Confidence:** HIGH. **Phase:** None — informational.

---

## Section 5 — AI-drafted docs at speed

### 5.1 Hallucinated parameters / fabricated examples

**What goes wrong:** Agent drafts an endpoint reference for `POST /work-order`, invents a `priority: int` field that doesn't exist in `WorkOrderNew`, fabricates a `curl` example using it. Visitor copies the curl, gets 422, loses trust.

**Why it happens:** LLMs interpolate from similar APIs they've seen; "priority on a work order" is a high-prior pattern.

**Mitigation:** **Generate from the source of truth, not from the prompt.** Pipeline:

1. Build-time: export `openapi.json` from FastAPI (per Section 2.8).
2. AI drafting prompt is constrained: "You are documenting endpoint X. Here is its **exact** OpenAPI operation object (JSON below). You may **not** introduce fields, status codes, or types that are not in this object. If a description is missing, write one based on the request body schema; do not infer behavior beyond what is documented."
3. Post-draft validation: run an automated check that every code-block parameter in the markdown appears in the operation's request schema. Tooling: a small Python script using `jsonschema` against extracted code blocks, run in CI.

This is the single highest-leverage practice for AI-drafted docs. AI generation rates of 29–45% for security-vulnerable code (per AI hallucination 2026 research) translate to similar rates for "wrong-API examples" without source-grounding.

**Confidence:** HIGH on the principle; MEDIUM on the validation script's coverage. **Phase:** L0 (drafting workflow).

---

### 5.2 Drift between code and prose

**What goes wrong:** Three weeks after launch, an endpoint adds a field. Docs site is not regenerated. Prose says "WorkOrderNew has fields A, B, C". Reality is A, B, C, D. Drift compounds; trust erodes.

**Mitigation:**

1. **Co-location alone is not enough** — PROJECT.md's claim that `docs/` in main repo "fixes drift" only fixes *spec-level* drift (the OpenAPI export tracks code). Prose drift is a separate problem.
2. **CI gate**: every PR that touches `backend/api/endpoints/**` or `backend/api/models/**` triggers an `openapi.json` regeneration. If the diff is non-trivial, CI fails until the docs PR updates the corresponding markdown. Use `openapi-diff` (Tufin) to surface the structured diff; fail when "added/removed operation" or "added required property" appears.
3. **Executable docs** for the CLI section: use **`pytest-markdown-docs`** to run all `cli/` markdown examples as tests. CI gate: `pytest --markdown-docs docs/cli/`. Catches drift in `progress init`, `progress restore`, `progress tap` examples — coordinated with sparkplug-demo S4.

**Confidence:** HIGH on the technique; HIGH on the tooling (pytest-markdown-docs is mature, used by Modal). **Phase:** L0 + CLI reference.

---

### 5.3 Drafting prompts that produce bland, generic prose

**What goes wrong:** Agent drafts every endpoint description as "This endpoint creates a new resource. It validates the input and returns a response." Site is technically accurate, completely useless.

**Mitigation:** Prompt scaffolding for endpoint drafts (encode in `.planning/workstreams/docs/CONVENTIONS.md`):

```
Goal: Draft VitePress markdown for FastAPI endpoint <PATH> <METHOD>.

You will receive:
1. The endpoint's source code (the Python function).
2. The Pydantic request model source.
3. The Pydantic response model source.
4. Source code of any utility functions called (e.g. utils.production.Queries.*).
5. The OpenAPI operation object (authoritative).

Output structure (mandatory):
- One-paragraph "What it does" describing business intent (not implementation).
- "When to use" — the user/integrator scenario this endpoint serves.
- "Preconditions" — bullet list of state requirements (extracted from the Queries.* calls).
- "On success" — what state changes (link to the events emitted).
- "On error" — bullet of each `responses` status code with when it fires.
- "Example" — single curl, single Python (httpx), built from the OpenAPI operation. Do not invent fields.

Do not:
- Invent parameters not in the request model.
- Speculate on rate limits, retries, or pagination unless they appear in source.
- Use hedging language ("might", "could", "typically"). State what the code does.
```

Same pattern for events: source-of-truth is the `BaseEvent` subclass, prompt is constrained to its `apply()` and `post_processing()` source.

**Confidence:** MEDIUM-HIGH (prompt design is empirical; this scaffold reflects current best-practice from API-docs-at-scale shops like Stripe, Twilio, Stoplight). **Phase:** L0 + L1.

---

### 5.4 No human-edit pass scheduled

**What goes wrong:** "AI-drafted then user-edited" turns into "AI-drafted then shipped" because the calendar is tight and the drafts look fine.

**Mitigation:** Treat the human-edit pass as a **separate phase** in the roadmap with its own time box, not a step at the end of authoring. Calendar-wise, plan for: 50% AI draft, 30% human curation, 20% executable validation. If the AI draft hits 80% on May 5 and a human curation pass is impossible by May 10, **cut scope** (drop a domain section to "coming soon") rather than ship un-reviewed AI prose. Generic AI prose is more damaging than a missing page — visitors recognize it instantly and downgrade trust in everything else on the site.

**Confidence:** MEDIUM (judgement call). **Phase:** L1, L2, L3 (per-section curation gate).

---

### 5.5 No "llms.txt" / machine-readable summary for downstream AI consumers

**What goes wrong:** Industry-4.0 consultants increasingly use AI assistants to evaluate platforms. Without a structured summary, the AI hallucinates what Progress Platform does.

**Mitigation:** Add `/llms.txt` at the docs site root (proposed standard, adopted by Anthropic, Mintlify, others as of 2026). Format: short markdown with H2 sections "What it is", "Architecture", "Endpoints" (linking to OpenAPI), "Events" (linking to events page). Generate at build time from PROJECT.md + openapi.json. Low cost, real upside given the audience.

**Confidence:** MEDIUM (standard is emerging, adoption growing — not yet universal). **Phase:** Site infrastructure (post-L0, low priority).

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip `response_model=` on a public endpoint | Saves 5 min | OpenAPI shows `additionalProperties: true`, breaks vitepress-openapi rendering, trust erosion | Never on a public endpoint |
| Auto-sidebar plugin for everything | Free navigation | Wrong order, fights with frontmatter rules, breaks on rename | When content is fully alphabetic-friendly (rare) |
| Iframe Swagger UI in VitePress | Familiar UX | Loses search, theming, routing, dark mode | Never for a co-located docs site |
| `ignoreDeadLinks: true` to fix CI | Build passes | Real broken links ship | Only for known external flaky URLs, narrow allowlist |
| "Document broken behavior" (bare `except` returning 500) | Honest within docs scope | Still a security/UX problem | L0 only, tracked for post-launch fix |
| Generate openapi.json at runtime via running app | Fewer scripts | Slow CI, port conflicts, flaky | Never — use `app.openapi()` build-time |
| Custom theme override for "branding" | Looks unique | Breaks on VitePress major bumps | Post-launch, after 2.x stabilizes |
| Algolia DocSearch as v1 launch dependency | Better search | Application queue blocks launch | Never — start on MiniSearch |

---

## "Looks Done But Isn't" Checklist

- [ ] **Endpoint has docstring:** Often missing **`response_model=`** — verify Swagger UI shows a real schema, not `{}`.
- [ ] **Pydantic model has fields:** Often missing **`Field(description=...)`** — verify `vitepress-openapi` shows descriptions, not just types.
- [ ] **Mermaid diagram renders:** Often missing **transaction-boundary annotation** — verify `rect` or `Note over` shows the atomic region.
- [ ] **Dead-link check passes:** Often missing **anchor-fragment validation** — VitePress built-in skips them; lychee in CI catches them.
- [ ] **GitHub repo public:** Often missing **issue templates and discussion categories** — verify both render on a fresh visit.
- [ ] **README has a 5-minute path:** Often missing **a working copy-pasteable command block** — verify on a fresh Linode VM.
- [ ] **OpenAPI is published:** Often missing **vacuum/Spectral lint pass** — verify CI gate fails on a missing description.
- [ ] **Mirror is fresh:** Often missing **manual force-push 30 min before launch** — verify SHA match between GitLab and GitHub.
- [ ] **AI-drafted page:** Often missing **a human curation pass** — verify a non-author reviewed every public-surface page.
- [ ] **CLI example in markdown:** Often missing **executable validation** — verify `pytest-markdown-docs` runs on every CLI page.
- [ ] **Custom domain ambition:** Often missing **24h DNS lead time** — verify `progresslab.github.io/progress-platform/` is the launch URL unless DNS is set 14d ahead.
- [ ] **Sitemap exists:** Often missing **`sitemap.hostname` config** — verify `/sitemap.xml` returns content on the deployed site.

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 1.1 Wrong OpenAPI renderer | Site infrastructure | `vitepress-openapi` listed in package.json; sample endpoint renders inline |
| 1.2 Auto-sidebar drift | Site infrastructure | `themeConfig.sidebar` is hand-written in config.ts |
| 1.3 Search application queue | Site infrastructure | `provider: 'local'` shipped; Algolia application sent in parallel |
| 1.4 Dead-link false negatives | Site infrastructure (CI) | `lychee` job in GH Actions, blocking |
| 1.5 Theme override creep | Site infrastructure | No `Layout.vue` override in repo; only CSS variables |
| 1.6 Code-block UX | L0 | `::: code-group` pattern in CONVENTIONS.md; sample uses curl + Python |
| 1.7 No sitemap | Site infrastructure | `/sitemap.xml` returns 200 on staging |
| 1.8 No URL contract | Phase 0 | URL contract in PROJECT.md before any markdown is written |
| 2.1 Single-line docstrings | L0 | Spectral/vacuum rule fails on missing `description` |
| 2.2 Missing `response_model=` | L0 | OpenAPI schema has typed responses for every public endpoint |
| 2.3 Pydantic Field neglect | L0 | vacuum rule fails on missing property `description` |
| 2.4 Pydantic v2 nullable form | None (informational) | — |
| 2.5 No tags_metadata | L0 | `app = FastAPI(openapi_tags=...)` set; `externalDocs` cross-link to events |
| 2.6 Documented broken errors | L0 + post-launch | Each public endpoint has explicit `responses={...}`; tracked issue exists for the fix |
| 2.7 No OpenAPI lint gate | L0 (CI) | vacuum runs in CI, fails on rule violations |
| 2.8 Runtime openapi.json fetch | L0 (CI) | `scripts/export_openapi.py` exists, no live app needed |
| 3.1 Wrong diagram type | L1 | `sequenceDiagram` is default for events; convention doc enforces |
| 3.2 Implicit tx boundaries | L1 | Convention doc requires `rect` for tx region; reviewer checklist |
| 3.3 Mermaid render perf | L1 | Diagrams >20 nodes use `defaultRenderer: elk`; large flows decomposed |
| 3.4 Mermaid dark mode | Site infrastructure | `vitepress-plugin-mermaid` pinned + dark-mode toggle test |
| 3.5 Auto-extracted prose drift | L1 | Strict template enforced by extractor; sections always present |
| 4.1 No LICENSE | Phase 0 | `LICENSE` file in repo root; license badge in README |
| 4.2 Misleading CONTRIBUTING | Phase 0 | Mirror banner in README + CONTRIBUTING; matches PR-close behavior |
| 4.3 No SECURITY.md | Phase 0 | `SECURITY.md` exists; Private Vuln Reporting on |
| 4.4 README fails 5-min test | Phase 0 | Fresh-VM rehearsal of the README block (S5 coordinates) |
| 4.5 No GIF/screenshot | Phase 0 / launch-week | Asciinema recording committed; embedded in README |
| 4.6 GitHub repo settings | Phase 0 | Pre-launch checklist run; templates rendered on fresh visit |
| 4.7 Mirror push race | Launch-week | 24h freeze + manual force-push; SHA-match script |
| 4.8 Custom domain | None (informational) | Ship on github.io for v1 |
| 5.1 Hallucinated examples | L0 (drafting workflow) | Drafts are constrained to OpenAPI source; example-validation script in CI |
| 5.2 Code/prose drift | L0 + CLI | openapi-diff CI gate; `pytest-markdown-docs` on cli/* |
| 5.3 Bland prompts | L0 + L1 | Drafting prompt template in CONVENTIONS.md; spot-check by curator |
| 5.4 No human-edit pass | L1, L2, L3 | Curation gate per section; cut scope rather than ship un-reviewed |
| 5.5 No llms.txt | Site infrastructure | `/llms.txt` returns content; sourced from PROJECT.md + openapi.json |

---

## Sources

**Primary (HIGH confidence):**
- VitePress official docs — [Sidebar](https://vitepress.dev/reference/default-theme-sidebar), [Search](https://vitepress.dev/reference/default-theme-search), [Markdown extensions](https://vitepress.dev/guide/markdown), [Site config](https://vitepress.dev/reference/site-config), [Routing](https://vitepress.dev/guide/routing)
- [vitepress-openapi (enzonotario)](https://github.com/enzonotario/vitepress-openapi) — v0.1.20, Apr 2026
- [vitepress-plugin-mermaid (emersonbottero)](https://github.com/emersonbottero/vitepress-plugin-mermaid)
- FastAPI official docs — [Metadata](https://fastapi.tiangolo.com/tutorial/metadata/), [Custom response](https://fastapi.tiangolo.com/advanced/custom-response/), [Extending OpenAPI](https://fastapi.tiangolo.com/advanced/extending-openapi/)
- FastAPI discussions — [Pydantic v2 OpenAPI examples broken (#11137)](https://github.com/fastapi/fastapi/discussions/11137), [v2 anyOf-with-null (#9900)](https://github.com/fastapi/fastapi/discussions/9900), [HTTPException in OpenAPI (#9124)](https://github.com/fastapi/fastapi/discussions/9124)
- VitePress dead-link issues — [#354](https://github.com/vuejs/vitepress/issues/354), [#3774](https://github.com/vuejs/vitepress/issues/3774), [#4419](https://github.com/vuejs/vitepress/issues/4419)
- [Spectral (Stoplight)](https://github.com/stoplightio/spectral) and [vacuum (daveshanley)](https://github.com/daveshanley/vacuum)
- [Mermaid official docs](https://mermaid.js.org/) — sequence diagrams, state diagrams, ELK renderer
- [GitHub: Adding a security policy](https://docs.github.com/en/code-security/getting-started/adding-a-security-policy-to-your-repository)
- [Open Source Guides — Starting a project](https://opensource.guide/starting-a-project/) and [Legal side](https://opensource.guide/legal/)
- [Contributor Covenant](https://www.contributor-covenant.org/)
- [GitLab repository mirroring docs](https://docs.gitlab.com/user/project/repository/mirror/) and [issue gitlab-org#5823](https://gitlab.com/gitlab-org/gitlab/-/issues/5823)
- [pytest-markdown-docs (modal-labs)](https://github.com/modal-labs/pytest-markdown-docs)

**Secondary (MEDIUM confidence — patterns/comparisons):**
- [Speakeasy: Choosing a docs vendor (Mintlify vs Scalar vs Bump vs ReadMe vs Redocly)](https://www.speakeasy.com/blog/choosing-a-docs-vendor)
- [Speakeasy: OpenAPI with Pydantic v2](https://www.speakeasy.com/openapi/frameworks/pydantic) and [FastAPI](https://www.speakeasy.com/openapi/frameworks/fastapi)
- [ZenUML: Sequence diagrams for event-driven architectures](https://zenuml.com/blog/2024/02/11/2024/sequence-diagram-in-event-driven-architecture/) and [practical examples](https://zenuml.com/blog/2024/05/17/2024/practical-examples-event-driven-system-design-sequence-diagrams/)
- [Three Dots Labs: Event-Driven Architecture: The Hard Parts](https://threedots.tech/episode/event-driven-architecture/)
- [Fern: API documentation best practices](https://buildwithfern.com/post/api-documentation-best-practices-guide) and [FastAPI instrumentation](https://buildwithfern.com/learn/api-definitions/openapi/frameworks/fastapi)
- [Open Source launch checklist 2026 (LaunchTry)](https://launchtry.com/resources/launch-checklist/open-source) and [diggsweden template](https://github.com/diggsweden/open-source-project-template/blob/main/docs/Open_Source_Checklist.md)
- AI hallucination 2026 research — [diffray on LLM hallucinations in code review](https://diffray.ai/blog/llm-hallucinations-code-review/), [AI hallucination testing 2026](https://medium.com/ai-in-quality-assurance/ai-hallucination-testing-in-2026-how-qa-engineers-detect-confidently-wrong-ai-answers-cb978ec6cc26), [Suprmind benchmarks](https://suprmind.ai/hub/ai-hallucination-rates-and-benchmarks/)

**Codebase-specific evidence (HIGH confidence — read at research time):**
- `/Users/luca/dev/progress/progress-platform/.planning/workstreams/docs/PROJECT.md` — locked decisions
- `/Users/luca/dev/progress/progress-platform/.planning/workstreams/sparkplug-demo/PROJECT.md` — parallel workstream context
- `backend/api/main.py` — current FastAPI app, no `openapi_tags`, no metadata
- `backend/api/events/base_event.py` — confirms tx → publish-after-commit pattern (`_publish_collected_events` runs after `commit_transaction`); informs Section 3 conventions
- `backend/api/endpoints/auth.py` and `backend/api/endpoints/production.py` — confirms bare-except + traceback-in-body pattern (Section 2.6)

---

*Pitfalls research for: Progress Platform OSS docs workstream, v1.0 launch (May 15, 2026)*
*Researched: 2026-04-29*
