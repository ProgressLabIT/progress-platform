---
phase: 01-scaffold-public-foundation
verified: 2026-04-29T00:00:00Z
re_verified: 2026-05-04T00:00:00Z
status: human_needed
score: 15/18 must-haves verified (5 ROADMAP SC: 2 pass / 0 fail / 3 human-deferred)
overrides_applied: 0
re_verification: editLink gap closed by code-review-fix commit 6a520fc0; source + dist now correctly template `edit/DEV/docs/`
gaps: []
deferred: []
resolved_gaps:
  - truth: "All source-code permalinks template to `github.com/ProgressLabIT/progress-platform/.../DEV/...` (never gitlab.com, branch ref must be DEV not main) — ROADMAP SC #5 / SITE-08 / D-13."
    status: resolved
    resolution: "Code-review-fix commit `6a520fc0` swapped `edit/main/docs/:path` → `edit/DEV/docs/:path` in `docs/.vitepress/config.ts:102`. Rebuilt; `docs/.vitepress/dist/index.html` now embeds `edit/DEV/docs/index.md`. Verified post-fix."
human_verification:
  - test: "Verify GitLab → GitHub mirror sync on DEV branch (ROADMAP SC #1 / MIR-01 / MIR-02)"
    expected: "After fixing the editLink gap above, merging GSD into DEV, pushing GitLab DEV, and clicking GitLab → Settings → Repository → Mirroring repositories → Update now: `git ls-remote https://gitlab.com/progresslab/progress-platform DEV` and `git ls-remote https://github.com/ProgressLabIT/progress-platform DEV` resolve to the same SHA within 30 seconds. Tag-propagation parity holds for any v* tag."
    why_human: "Mirror trigger is a GitLab UI button; canot be invoked from this checkout. Local docs P01 commits live on GSD branch only — they have not been merged into DEV nor pushed to GitLab/GitHub. Without the merge+push+Update-now sequence, GitHub mirror still has stale state."
  - test: "Verify Pages site live at every URL in the contract (ROADMAP SC #3 / SITE-04 / SITE-10)"
    expected: |
      After mirror sync completes and GitHub Actions `Deploy VitePress site to Pages` workflow run finishes:
      ```bash
      BASE=https://progresslabit.github.io/progress-platform
      for path in / /api/ /api/production/jobs/start/ /events/ /events/production/job-started/ \
                  /cli/ /cli/init/ /users/ /users/production/ /admins/ /admins/deployment/ /openapi.json; do
        STATUS=$(curl -fsS -o /dev/null -w "%{http_code}" "${BASE}${path}")
        echo "${BASE}${path} → ${STATUS}"
      done
      ```
      All 12 paths return HTTP 200. Top-nav of `${BASE}/` shows API · Events · CLI · Users · Admins.
    why_human: "Pages site requires propagation of workflow files (`deploy-docs.yml`, `lychee.yml`) to GitHub mirror first. Until first deploy succeeds, no live URL exists to test."
  - test: "Verify deploy completes in under 10 minutes; sitemap + MiniSearch live (ROADMAP SC #4 / SITE-06 / SITE-05 / SITE-07)"
    expected: |
      ```bash
      gh run list --repo ProgressLabIT/progress-platform --workflow=deploy-docs.yml --limit 1 \
        --json status,conclusion,startedAt,updatedAt \
        | jq -e '.[0].conclusion == "success"
                 and ((.[0].updatedAt | fromdateiso8601) - (.[0].startedAt | fromdateiso8601)) < 600'
      curl -fsS https://progresslabit.github.io/progress-platform/sitemap.xml | grep -F "https://progresslabit.github.io/progress-platform/"
      curl -fsS https://progresslabit.github.io/progress-platform/ | grep -E "VPLocalSearch|provider.+local|local-search"
      ```
      Latest run conclusion is `success`, elapsed < 600s, sitemap hostname matches, MiniSearch widget rendered.
    why_human: "Requires live deploy run — local build is verified (`docs/.vitepress/dist/sitemap.xml` already has correct hostname and 11 pages locally), but actual <10-min CI deploy can only be measured after first GitHub Actions run."
  - test: "Verify lychee CI runs on every PR + DEV push and gates on broken links (ROADMAP SC #5 / SITE-09)"
    expected: |
      ```bash
      gh run list --repo ProgressLabIT/progress-platform --workflow=lychee.yml --branch=DEV --limit 1 \
        --json conclusion | jq -e '.[0].conclusion == "success"'
      gh api /repos/ProgressLabIT/progress-platform/contents/.github/workflows/lychee.yml \
        -H "Accept: application/vnd.github.raw" | grep -F -- "--include-fragments"
      gh api /repos/ProgressLabIT/progress-platform/commits/DEV/check-runs \
        --jq '.check_runs[] | select(.name == "build" or .name == "linkChecker") | "\(.name):\(.conclusion)"' | sort -u
      ```
      Lychee workflow latest run on DEV is `success`, file contains `--include-fragments` / `--root-dir` / `--base`, and both `build` and `linkChecker` check-runs report `success`. After re-arming `required_status_checks` on ruleset id 15731781, both contexts are listed.
    why_human: "Lychee can only run on GitHub once workflows propagate via mirror. Workflow YAML is verified locally (`.github/workflows/lychee.yml` contains `--include-fragments`, `--root-dir`, `--base`, `--config` per CP-10), but live execution is post-mirror-push only."
---

# Phase 01: Scaffold & Public Foundation Verification Report

**Phase Goal:** A public-facing skeleton exists — GitHub mirror is live with OSS table-stakes (LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY-equivalent, README banner), the VitePress site under `docs/` builds and deploys to GitHub Pages on every push to `DEV`, and the URL contract (`/api/...`, `/events/...`, `/cli/...`, `/users/...`, `/admins/...`) is locked before any markdown is written.

**Verified:** 2026-04-29
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement Summary

Local artifacts are 14/18 verified. One real codebase gap blocks ROADMAP SC #5: the `editLink.pattern` in `docs/.vitepress/config.ts` references the wrong git branch (`main` instead of `DEV`), contradicting D-13/SITE-08 and the plan body. The 01-02 SUMMARY makes a false claim that this is wired to `DEV` — a textbook SUMMARY-vs-code drift that goal-backward verification is designed to catch.

The remaining four ROADMAP success criteria (#1 mirror sync, #3 Pages-200 contract, #4 deploy <10min + sitemap + MiniSearch live, parts of #5 lychee CI run) cannot be verified locally because docs P01 commits live on GSD branch only — they have not been merged to DEV, pushed to GitLab, or mirrored to GitHub. Those four are routed to `human_verification` with the exact resume-time commands the maintainer must run after the GSD → DEV merge + GitLab push + `Update now` mirror trigger.

**Recommended sequence:** fix the editLink gap and rebuild before running the maintainer propagation flow. Otherwise the broken Edit-on-GitHub link will ship live and need a second deploy round-trip to correct.

## Observable Truths (against ROADMAP SC + plan must-haves)

### ROADMAP Success Criteria (5)

| # | Truth (ROADMAP SC) | Status | Evidence |
|---|---------------------|--------|----------|
| SC1 | `git ls-remote https://github.com/ProgressLabIT/progress-platform DEV` resolves to same SHA as GitLab DEV within 30s of any push (one-way mirror, tags propagate). | ? UNCERTAIN — needs human | Local commits not yet merged to DEV / pushed / mirrored. Mirror flow documented verbatim in `CONTRIBUTING.md` lines 13-26 (verified). PAT-scope checkpoint outstanding (CP-7). Routed to human_verification #1. |
| SC2 | First-time visitor on GitHub repo sees mirror banner + 5-min progress init + LICENSE/CONTRIBUTING/COC links + docs site URL; Issues+Discussions on, Wiki off, DEV branch-protected. | ✓ VERIFIED | `README.md` line 11 contains "read-only mirror" banner; lines 22-29 contain `progress init` block; lines 47, 51, 55 link CONTRIBUTING/SECURITY/CODE_OF_CONDUCT/LICENSE; line 33 contains docs URL `https://progresslabit.github.io/progress-platform/`. Per init context (autonomous-mode delivered), `gh repo edit` settings + PVR + ruleset id 15731781 already applied with Issues+Discussions on, Wiki off, default-branch ruleset active (verified by 01-01 SUMMARY against `gh repo view --json` and `gh api /repos/.../rulesets`). |
| SC3 | Pages site at `https://progresslabit.github.io/progress-platform/` returns HTTP 200 on every URL in contract; top-nav shows API · Events · CLI · Users · Admins. | ? UNCERTAIN — needs human | Live deploy not yet triggered. Local build (`docs/.vitepress/dist/`) verified to emit all 11 contract pages + sitemap with 11 entries. Built `dist/index.html` confirms top-nav renders API · Events · CLI · Users · Admins via `VPNavBarMenuLink` anchors. Routed to human_verification #2. |
| SC4 | Push to GH `DEV` triggers Actions deploy in <10 min; sitemap.xml correct hostname; MiniSearch enabled. | ? UNCERTAIN — needs human | `.github/workflows/deploy-docs.yml` triggers on `push: branches: [DEV]` (verified line 6). `docs/.vitepress/dist/sitemap.xml` contains `https://progresslabit.github.io/progress-platform/` for all 11 URLs (verified locally). `themeConfig.search.provider: 'local'` (MiniSearch) verified in `config.ts` line 78. Local-side ready; <10-min wall-clock can only be measured after first live deploy. Routed to human_verification #3. |
| SC5 | Hand-written `themeConfig.sidebar` only; source-code permalinks template github.com (not GitLab); `vitepress-openapi` wired against placeholder; lychee CI on every PR; openapi.json build artifact slot exists. | ✗ FAILED — partial | Hand-written sidebar verified (`config.ts` lines 43-74 — no auto-sidebar plugin in deps); `vitepress-openapi` import verified (`theme/index.ts` line 4); placeholder `docs/public/openapi.json` valid OpenAPI 3.0.4 with `paths: {}` (verified); lychee workflow file exists with `--include-fragments`, `--root-dir`, `--base`, `--config` flags (verified `.github/workflows/lychee.yml` lines 47-51); openapi.json artifact slot exists at `docs/public/openapi.json`. **BUT** `editLink.pattern` references `edit/main/docs/:path` instead of `edit/DEV/docs/:path` — every "Edit on GitHub" link in the live site will 404 because `main` is not the active branch. Built dist/index.html embeds `edit/main/docs/` (live test). See gaps section. |

### Plan must_haves cross-check (sample of high-value local truths)

| # | Truth (plan must_have) | Status | Evidence |
|---|------------------------|--------|----------|
| L1 | LICENSE = Apache 2.0; no MIT residue at repo root; webapps declare Apache-2.0. | ✓ VERIFIED | `head -2 LICENSE` shows "Apache License" + "APPENDIX: How to apply..."; `webapps/main/package.json` and `webapps/warehouse/package.json` both declare `"license": "Apache-2.0"`. |
| L2 | README ≤150 lines, Pitfall 4.4 8-section structure, NATS not Kafka, mirror banner verbatim. | ✓ VERIFIED | `wc -l README.md` = 55 (well under cap). Sections present: badges, tagline, mirror banner, demo placeholder, Try-it-in-5-min, Documentation, Architecture, Contributing, Security, License (8 functional sections). Architecture paragraph says "NATS JetStream" — no Kafka in README. |
| L3 | CONTRIBUTING.md has Pitfall 4.2 verbatim text + GitLab `Update now` flow + `git ls-remote` SHA-match command. | ✓ VERIFIED | All three present in `CONTRIBUTING.md` lines 1-27 (verbatim from plan Task 1). |
| L4 | SECURITY.md ≤15 body lines, no SLA, no version table, points at PVR. | ✓ VERIFIED | `wc -l SECURITY.md` = 13 lines total; non-blank body = 7. Contains "Private Vulnerability Reporting", "best-effort", "no committed acknowledgment window", current-`DEV`-only support clause. |
| L5 | CODE_OF_CONDUCT.md = Contributor Covenant 2.1. | ✓ VERIFIED | First line "Contributor Covenant Code of Conduct"; pledge text matches Covenant 2.1. |
| L6 | `.github/PULL_REQUEST_TEMPLATE.md` includes mirror-PR closure notice. | ✓ VERIFIED | File present with "read-only mirror" notice + issue+patch flow + CONTRIBUTING.md link. |
| L7 | ARCHITECTURE.md exists at repo root with extracted overview. | ✓ VERIFIED | `wc -l` = 100 lines; covers system diagram, layered backend, data flow, frontends, repo layout, tech stack. |
| L8 | VitePress 1.6.4 builds 11 pages locally. | ✓ VERIFIED | `docs/.vitepress/dist/` contains all 11 expected HTML pages (homepage + 5 landings + 5 stubs); sitemap.xml emitted with 11 URLs. Per 01-02-SUMMARY, build completed in 19.52s exit 0. |
| L9 | URL contract locked: 10 markdown contract files + homepage at exact D-07/D-08 paths. | ✓ VERIFIED | `find docs -maxdepth 5 -name '*.md'` (excluding node_modules) returns exactly: `docs/index.md`, `docs/{api,events,cli,users,admins}/index.md` (5), `docs/api/production/jobs/start.md`, `docs/events/production/job-started.md`, `docs/cli/init.md`, `docs/users/production.md`, `docs/admins/deployment.md` (5) = 11 files. |
| L10 | Hand-written `themeConfig.sidebar` only; no auto-sidebar plugin. | ✓ VERIFIED | `config.ts` lines 43-74 contain inline sidebar object; `package.json` devDependencies do not contain auto.sidebar / vitepress-sidebar. |
| L11 | Top-nav order = API · Events · CLI · Users · Admins (D-07). | ✓ VERIFIED | `config.ts` lines 33-39 declare nav array in exactly that order. |
| L12 | MiniSearch local search configured. | ✓ VERIFIED | `config.ts` line 78: `provider: 'local'`. |
| L13 | Sitemap hostname matches base path (CP-3). | ✓ VERIFIED | `config.ts` line 17: `hostname: 'https://progresslabit.github.io/progress-platform/'`. Built sitemap.xml uses this hostname for all 11 URLs. |
| L14 | `vitepress-openapi` wired against `docs/public/openapi.json` placeholder; build does not throw. | ✓ VERIFIED | `theme/index.ts` line 4 imports from `vitepress-openapi/client`; line 12 imports placeholder spec; line 22 calls `useOpenapi({ spec })`. Build completed without throw per 01-02-SUMMARY. |
| L15 | Mermaid plugin loads with ELK loader behind SSR-safe `typeof window` guard (CP-5). | ✓ VERIFIED | `theme/index.ts` line 15: `if (typeof window !== 'undefined')` wraps `mermaid.registerLayoutLoaders(elkLayouts)`. |
| L16 | docs/superpowers/ deleted (D-05). | ✓ VERIFIED | `test -d docs/superpowers` returns absent. |
| L17 | `.planning/workstreams/docs/CONVENTIONS.md` authored with D-14 initial scope (6 sections). | ✓ VERIFIED | File present, 112 lines, contains all six required sections (endpoint docstring, AI prompt scaffold STUB, Mermaid transaction-boundary, curation gate, source-code permalink template, kebab-case URL). |
| L18 | Workflow files exist with correct triggers and CP-10 lychee flags. | ✓ VERIFIED | `deploy-docs.yml` triggers `push: branches: [DEV]`; `lychee.yml` triggers on PR + DEV push with `--include-fragments` + `--root-dir` + `--base` + `--config`; `dependabot.yml` configured for npm/github-actions/gitlab-ci; `lychee.toml` exists with localhost excludes. |

**Score:** 14/18 plan-level truths VERIFIED + 1 ROADMAP SC VERIFIED, 1 ROADMAP SC FAILED, 3 ROADMAP SC routed to human verification.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `LICENSE` | Apache 2.0 (~202 lines) | ✓ VERIFIED | `head -2` shows "Apache License" boilerplate. |
| `README.md` | 8-section Pitfall 4.4 structure ≤150 lines | ✓ VERIFIED | 55 lines; mirror banner, 5-min block, OSS links, docs URL, NATS-not-Kafka all present. |
| `ARCHITECTURE.md` | Extracted overview at repo root | ✓ VERIFIED | 100 lines; covers system diagram + tech stack; explicitly clarifies NATS-not-Kafka legacy refs. |
| `CONTRIBUTING.md` | Pitfall 4.2 verbatim + D-15 mirror flow | ✓ VERIFIED | 27 lines; Pitfall 4.2 wording + GitLab Update-now flow + `git ls-remote` command verbatim from plan. |
| `CODE_OF_CONDUCT.md` | Contributor Covenant 2.1 | ✓ VERIFIED | 85 lines; Covenant 2.1 wording confirmed. |
| `SECURITY.md` | ≤15 body lines, PVR pointer, no SLA | ✓ VERIFIED | 13 total / 7 body lines; PVR pointer + best-effort + DEV-only support. |
| `.github/PULL_REQUEST_TEMPLATE.md` | Mirror PR closure notice | ✓ VERIFIED | 7 lines; mirror notice + issue/patch flow. |
| `.github/workflows/deploy-docs.yml` | Build+deploy on push to DEV; OIDC; concurrency cancel-in-progress=false; fetch-depth: 0 | ✓ VERIFIED | All gates present (lines 5-7, 12-15, 18-20, 31-32, 56-72). |
| `.github/workflows/lychee.yml` | PR+DEV push trigger; --include-fragments + --root-dir + --base + --config; fail:true | ✓ VERIFIED | All gates present (lines 4-14, 45-52). |
| `.github/dependabot.yml` | npm /docs + github-actions / + gitlab-ci / | ✓ VERIFIED | All three ecosystems declared. |
| `lychee.toml` | Excludes localhost variants; cache; exclude_all_private | ✓ VERIFIED | All gates present. |
| `docs/package.json` | vitepress 1.6.4, plugin-mermaid 2.0.17, openapi 0.1.20, mermaid+layout-elk; type:module; engines.node 20.19.0; license Apache-2.0 | ✓ VERIFIED | All exact pins present; type:module added (per Rule 3 deviation in 01-02-SUMMARY). |
| `docs/.vitepress/config.ts` | base, sitemap, nav (D-07), sidebar (hand-written, no .html), search.provider='local', editLink → github.com (NEVER gitlab), withMermaid | ⚠️ STUB-LIKE | All elements present EXCEPT editLink branch ref is `main` (must be `DEV`). See gaps. |
| `docs/.vitepress/theme/index.ts` | vitepress-openapi import + ELK loader behind SSR guard | ✓ VERIFIED | Both present. Note: relative import path was corrected from plan template's `../public/...` to `../../public/...` per 01-02-SUMMARY deviation #2. |
| `docs/public/openapi.json` | Placeholder OpenAPI 3.0.4 with paths:{} | ✓ VERIFIED | Exact content matches plan; valid OpenAPI 3.x. |
| `docs/public/robots.txt` | Allow-all + sitemap pointer | ✓ VERIFIED | Present. |
| `docs/index.md` | Homepage with 5-link section overview | ✓ VERIFIED | 15 lines; 5 section links + description. |
| 5 section landings + 5 stubs | "Coming soon" frontmatter + Related cross-links | ✓ VERIFIED | All 10 files present at locked paths; uniform `> 🚧 Coming soon — populated in Phase X` + Related: Events · API · Home pattern. |
| `.planning/workstreams/docs/CONVENTIONS.md` | D-14 initial scope, 6 sections | ✓ VERIFIED | 112 lines; all six required sections present. |
| `webapps/main/package.json`, `webapps/warehouse/package.json` | `"license": "Apache-2.0"` | ✓ VERIFIED | Both files confirmed. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `README.md` | `CONTRIBUTING.md` | markdown link | ✓ WIRED | Lines 11, 47 link to `[CONTRIBUTING.md](CONTRIBUTING.md)`. |
| `README.md` | `SECURITY.md` | markdown link | ✓ WIRED | Line 51 links to `[SECURITY.md](SECURITY.md)`. |
| `README.md` | `ARCHITECTURE.md` | markdown link | ✓ WIRED | Line 43 links to `[ARCHITECTURE.md](ARCHITECTURE.md)`. |
| `README.md` | docs site URL | absolute URL | ✓ WIRED | Line 33: `https://progresslabit.github.io/progress-platform/`. |
| `CONTRIBUTING.md` | GitLab mirror UI verification | `git ls-remote` commands | ✓ WIRED | Lines 22-25: both `git ls-remote` commands present. |
| `docs/.vitepress/config.ts` | 10 stub pages | sidebar entries (no .html) | ✓ WIRED | All 10 contract paths in sidebar, no `.html` suffixes. |
| `docs/.vitepress/theme/index.ts` | `docs/public/openapi.json` | JSON import with `with { type: 'json' }` | ✓ WIRED | Line 12: `import spec from '../../public/openapi.json' with { type: 'json' }`. |
| `docs/.vitepress/theme/index.ts` | `@mermaid-js/layout-elk` | `registerLayoutLoaders(elkLayouts)` inside SSR guard | ✓ WIRED | Lines 9, 15-17 confirmed. |
| `config.ts` | GitHub Pages base | `base: '/progress-platform/'` | ✓ WIRED | Line 10. |
| `config.ts` | sitemap | `sitemap.hostname` matches base path (CP-3) | ✓ WIRED | Line 17: hostname includes `/progress-platform/`. |
| Every stub page | section landings + home | `Related: [Events](/events/) · [API](/api/) · [Home](/)` | ✓ WIRED | Pattern present in every stub. |
| `editLink.pattern` | GitHub source-code permalink with branch=DEV | github.com URL with `/edit/DEV/` | ✗ NOT_WIRED | Branch ref is `main`, not `DEV`. See gap. |
| `.github/workflows/deploy-docs.yml` | GitHub Pages CDN | `actions/deploy-pages@v4` OIDC publish | ✓ WIRED | Line 72. Live execution pending mirror push. |
| `.github/workflows/lychee.yml` | `docs/.vitepress/dist` | `--root-dir + --base + --include-fragments` | ✓ WIRED | Lines 47-51. |
| Branch ruleset | workflow job names | `required_status_checks` contexts `build` + `linkChecker` | ⚠️ PARTIAL | Job names match locally; ruleset re-arm against id 15731781 is a maintainer step post-deploy (per 01-03-SUMMARY). |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|---------|
| `docs/index.md` | static markdown | hand-authored | Yes (static intentional — Phase 1 scaffold) | ✓ FLOWING |
| 5 section landings + 5 stubs | static markdown | hand-authored "Coming soon" placeholders | Yes by design (Phase 2/3 fills content) | ✓ FLOWING |
| `vitepress-openapi` rendering | `spec` from `openapi.json` | `paths: {}` placeholder | Empty by design — Phase 2 swaps real export | ⚠️ STATIC (intentional, scope-correct) |
| Sitemap | 11 contract pages from VitePress build | autoderived from markdown files | Yes — sitemap.xml has 11 entries | ✓ FLOWING |
| Top-nav | hand-written `themeConfig.nav` array | `config.ts` lines 33-39 | Yes — built HTML embeds 5 nav anchors | ✓ FLOWING |
| Edit-on-GitHub link | `editLink.pattern` template | `config.ts` line 102 | Wrong-branch URL — links will 404 in production | ✗ HOLLOW (broken-by-construction) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| VitePress build emits 11 pages | `ls docs/.vitepress/dist/api/production/jobs/start.html` | file present 14.6K | ✓ PASS |
| Sitemap embeds correct hostname for all 11 URLs | `grep -F 'progresslabit.github.io/progress-platform' docs/.vitepress/dist/sitemap.xml` | 11 URLs found | ✓ PASS |
| README mirror banner present | `grep -F 'read-only mirror' README.md` | match line 11 | ✓ PASS |
| README ≤ 150 lines | `wc -l README.md` | 55 | ✓ PASS |
| LICENSE = Apache 2.0 | `head -2 LICENSE` | "Apache License" | ✓ PASS |
| webapp package.json declares Apache-2.0 | `grep '"license"' webapps/{main,warehouse}/package.json` | both Apache-2.0 | ✓ PASS |
| editLink branch ref = DEV (per plan + ROADMAP) | `grep -E "edit/(main\|DEV)/docs" docs/.vitepress/config.ts` | match `edit/main/docs` | ✗ FAIL — wrong branch |
| Built HTML edit link uses DEV | `grep -oE "edit/[^/]+/docs/" docs/.vitepress/dist/index.html` | `edit/main/docs/` | ✗ FAIL — wrong branch baked in |
| docs/superpowers/ deleted | `test -d docs/superpowers` | absent | ✓ PASS |
| Workflow triggers on `[DEV]` | `grep "branches:" .github/workflows/*.yml` | both `[DEV]` | ✓ PASS |
| Lychee CLI flags present | `grep -F '\-\-include-fragments' .github/workflows/lychee.yml` | match | ✓ PASS |
| CONTRIBUTING.md verification command | `grep -F 'git ls-remote' CONTRIBUTING.md` | both gitlab + github lines | ✓ PASS |
| SECURITY.md ≤15 body lines | non-blank line count | 7 | ✓ PASS |
| Live mirror SHA match | `git ls-remote ... DEV` both remotes | not testable here | ? SKIP — human |
| Live deploy <10min | `gh run list --workflow=deploy-docs.yml` | not testable here | ? SKIP — human |
| Live Pages 200 on every URL | `curl ${BASE}${path}` × 12 | not testable here | ? SKIP — human |
| Live lychee gate green | `gh run list --workflow=lychee.yml` | not testable here | ? SKIP — human |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| MIR-01 | 01-01 | GitHub mirror configured one-way push from GitLab DEV | ? NEEDS HUMAN | Mirror flow documented; live verification deferred to Task 8 checkpoint. |
| MIR-02 | 01-01 | Mirror propagates tags | ? NEEDS HUMAN | GitLab default-on; live verification post-push. |
| MIR-03 | 01-01 | GH repo settings: Issues+Discussions on, Wiki off, branch-protect on DEV | ✓ SATISFIED | 01-01-SUMMARY records `gh repo view --json` outputs and ruleset id 15731781. |
| MIR-04 | 01-01 | Apache 2.0 LICENSE at repo root | ✓ SATISFIED | LICENSE verified. |
| MIR-05 | 01-01 | CONTRIBUTING.md mirror-honest workflow | ✓ SATISFIED | Pitfall 4.2 verbatim verified. |
| MIR-06 | 01-01 | CODE_OF_CONDUCT.md = Contributor Covenant 2.1 | ✓ SATISFIED | Verified. |
| MIR-07 | 01-01 | README mirror banner + docs site link + quickstart | ✓ SATISFIED | All elements present. |
| SITE-01 | 01-02 | VitePress site initialized under `docs/` | ✓ SATISFIED | package.json + config.ts + 11 pages + dist build. |
| SITE-02 | 01-02 | Mermaid plugin enabled, ELK renderer available | ✓ SATISFIED | `withMermaid` wrap + `registerLayoutLoaders(elkLayouts)` behind SSR guard. |
| SITE-03 | 01-02 | Hand-written sidebar (no auto-sidebar plugin) | ✓ SATISFIED | Inline sidebar in config.ts; no auto-sidebar dep. |
| SITE-04 | 01-02 | Top-nav: API · Events · CLI · Users · Admins | ✓ SATISFIED | nav array verified in correct D-07 order. |
| SITE-05 | 01-02 | MiniSearch local search | ✓ SATISFIED | `provider: 'local'` verified. |
| SITE-06 | 01-02 | Sitemap with hostname | ✓ SATISFIED | `sitemap.hostname` = correct; built sitemap.xml has 11 entries with correct hostname. |
| SITE-07 | 01-03 | GH Actions workflow deploys to Pages on push to DEV | ? NEEDS HUMAN | Workflow file exists + correct triggers; live deploy pending mirror push. |
| SITE-08 | 01-02 | Source-code permalinks point to github.com (not gitlab) | ✗ BLOCKED | editLink template points at github.com (good) BUT branch ref is `main` not `DEV` (bad) — links will 404 because the active branch is DEV. ROADMAP SC #5 calls out the GitHub-not-GitLab requirement; the branch part is fundamental to making the link work. |
| SITE-09 | 01-03 | Dead-link CI on every PR (lychee or built-in) | ? NEEDS HUMAN | Workflow file present with correct flags + triggers; live execution pending mirror push. |
| SITE-10 | 01-02 | URL contract locked before any markdown lands | ✓ SATISFIED | 11 pages at locked paths; sidebar + sitemap match. |
| SITE-12 | 01-02 | AI-drafted prose grounded in openapi.json | ✓ SATISFIED | Placeholder openapi.json wired; CONVENTIONS.md §2 documents grounding rule. |

**Coverage:** 18/18 phase requirements addressed by plans; 12 SATISFIED, 1 BLOCKED (SITE-08), 4 NEEDS HUMAN (MIR-01, MIR-02, SITE-07, SITE-09), 1 SATISFIED with caveat (SITE-08-companion: github.com pattern is correct, only branch ref is wrong).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `docs/.vitepress/config.ts` | 102 | `editLink.pattern: '...edit/main/docs/...'` — stale `main` branch ref where plan + ROADMAP specify `DEV` | 🛑 Blocker | Every "Edit on GitHub" link in the live docs site will 404 once deployed. SUMMARY narrative claims this is fixed (it isn't). |
| `docs/.vitepress/dist/index.html` | (built) | Same `edit/main/docs/` baked into rendered HTML | 🛑 Blocker | Inherited from config.ts — fixed by rebuilding after config fix. |
| `01-02-SUMMARY.md` | 23, 106, 226 | False claim that editLink targets `/edit/DEV/docs/:path` | ⚠️ Warning | SUMMARY drift — not load-bearing, but flags a class of issue. SUMMARY needs correction once code is fixed. |

No other anti-patterns found. The local artifacts are otherwise high-fidelity to the plans, with two intentional deviations (type:module + theme import path) explicitly documented in 01-02-SUMMARY §Deviations.

### Human Verification Required

See frontmatter `human_verification` for the four items routed to maintainer:

1. **Mirror sync verification** (ROADMAP SC #1 / MIR-01 / MIR-02) — after GSD → DEV merge + GitLab push + GitLab `Update now`, confirm both `git ls-remote` calls return same SHA.
2. **Pages-200 contract** (ROADMAP SC #3 / SITE-04 / SITE-10) — curl all 11 contract URLs + verify top-nav.
3. **Deploy <10min + sitemap + MiniSearch live** (ROADMAP SC #4 / SITE-06 / SITE-05 / SITE-07) — `gh run list --workflow=deploy-docs.yml` elapsed under 600s; sitemap reachable; MiniSearch widget renders.
4. **Lychee CI live + ruleset re-arm** (ROADMAP SC #5 / SITE-09) — `gh run list --workflow=lychee.yml` green on DEV; check-runs `build` + `linkChecker` both `success`; re-arm `required_status_checks` on ruleset id 15731781.

Each item lists exact bash commands to run.

### Gaps Summary

**One real codebase gap** blocks ROADMAP SC #5 (and consequently SITE-08 in spirit, even though the github.com-vs-gitlab.com part is correct):

`docs/.vitepress/config.ts` line 102 references the wrong git branch in the `editLink.pattern`. The plan body, the ROADMAP success criteria (with branch refs explicitly rewritten to DEV), and the entire workflow stack (`branches: [DEV]`, ruleset on `~DEFAULT_BRANCH=DEV`) all point at DEV — but the editLink template hardcodes `main`. The 01-02-SUMMARY claims (in three places) that this is wired to `/edit/DEV/docs/:path`, but the actual file says `/edit/main/docs/:path`. The built `dist/index.html` confirms the wrong branch is baked into the rendered "Edit this page" links.

This is precisely the kind of silent SUMMARY-vs-code drift goal-backward verification exists to catch.

**Fix is single-line:** change `'main'` → `'DEV'` in `docs/.vitepress/config.ts` line 102, rebuild `docs/`, recommit, and update 01-02-SUMMARY's three drift points (frontmatter, Accomplishments, Coverage Matrix).

The four live-deploy ROADMAP success criteria (#1, #3, #4, parts of #5) are correctly outside this run's reach because docs P01 commits are GSD-only — they have not propagated to DEV / GitLab / GitHub mirror. They are surfaced as `human_verification` items with exact commands rather than being gaps.

---

*Verified: 2026-04-29*
*Verifier: Claude (gsd-verifier)*
