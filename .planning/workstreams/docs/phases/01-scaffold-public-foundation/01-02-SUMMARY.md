---
phase: 01-scaffold-public-foundation
plan: 02
slug: vitepress-scaffold-url-contract
workstream: docs
subsystem: docs-site

tags: [vitepress, mermaid, openapi, sitemap, minisearch, github-pages, oss-scaffold]

# Dependency graph
requires:
  - phase: 01-scaffold-public-foundation/01-01
    provides: "OSS table-stakes (LICENSE Apache 2.0, README rewrite, CONTRIBUTING/SECURITY/COC); already deleted docs/superpowers/ in commit febf6375 (D-05 swept early)"
provides:
  - "VitePress 1.6.4 site scaffold at docs/ with type:module, building cleanly to docs/.vitepress/dist/"
  - "URL contract locked: 11 routable pages (homepage + 5 landings + 5 representative stubs) at exactly the D-07/D-08 paths"
  - "Hand-written themeConfig.sidebar (Pitfall 1.2 honored — no auto-sidebar plugin in deps)"
  - "Top-nav in fixed D-07 order: API · Events · CLI · Users · Admins"
  - "MiniSearch local search wired (themeConfig.search.provider='local')"
  - "Sitemap with hostname https://progresslabit.github.io/progress-platform/ (CP-3 — base-path-included)"
  - "vitepress-openapi 0.1.20 wired against placeholder docs/public/openapi.json (paths:{}, OpenAPI 3.0.4)"
  - "Mermaid plugin (vitepress-plugin-mermaid 2.0.17) with ELK loader registered behind typeof-window SSR guard (CP-5)"
  - "editLink.pattern → github.com/ProgressLabIT/progress-platform/edit/DEV/docs/:path (D-13/SITE-08; never gitlab)"
  - ".planning/workstreams/docs/CONVENTIONS.md authored with D-14 initial scope (endpoint docstring shape, AI prompt scaffold STUB, Mermaid transaction-boundary, curation gate, GitHub permalink template, kebab-case URLs)"
affects: [01-03 (CI/deploy workflow + lychee), phase-02 (API/events content), phase-03 (CLI/users/admins content), phase-04 (launch prep)]

tech-stack:
  added:
    - "vitepress 1.6.4 (exact pin)"
    - "vitepress-plugin-mermaid 2.0.17 (exact pin)"
    - "vitepress-openapi 0.1.20 (exact pin)"
    - "mermaid ^11.14.0"
    - "@mermaid-js/layout-elk ^0.2.1"
  patterns:
    - "Hand-written sidebar (Pitfall 1.2) — single source of truth for nav"
    - "Default theme + CSS-variable brand color override only (Pitfall 1.5)"
    - "ESM module type at docs/ (type:module) — required for VitePress 1.x ESM-only deps"
    - "cleanUrls:true with sidebar links having no .html suffix (CP-4 internal consistency)"
    - "Section landing + 1 representative stub per top-nav (D-07 contract-shape strategy)"

key-files:
  created:
    - "docs/package.json (5 dev deps, type:module, engines.node 20.19.0, Apache-2.0)"
    - "docs/package-lock.json (286 packages, lockfileVersion 3)"
    - "docs/.gitignore"
    - "docs/.vitepress/config.ts (site config, nav, sidebar, sitemap, search, editLink, mermaid)"
    - "docs/.vitepress/theme/index.ts (default theme + vitepress-openapi + ELK loader)"
    - "docs/.vitepress/theme/custom.css (brand-color variables)"
    - "docs/public/openapi.json (placeholder OpenAPI 3.0.4 with paths:{})"
    - "docs/public/robots.txt (allow-all + sitemap pointer)"
    - "docs/index.md (homepage)"
    - "docs/api/index.md, docs/api/production/jobs/start.md (2 pages)"
    - "docs/events/index.md, docs/events/production/job-started.md (2 pages)"
    - "docs/cli/index.md, docs/cli/init.md (2 pages)"
    - "docs/users/index.md, docs/users/production.md (2 pages)"
    - "docs/admins/index.md, docs/admins/deployment.md (2 pages)"
    - ".planning/workstreams/docs/CONVENTIONS.md (D-14 initial scope)"
  modified: []

key-decisions:
  - "Added type:module to docs/package.json — required for VitePress 1.6.4 ESM bundling; plan template missed this (Rule 3 deviation)"
  - "Theme spec import path corrected to ../../public/openapi.json (two levels up from docs/.vitepress/theme/) — plan text said ../public/openapi.json which is correct only if theme is at docs/.vitepress/index.ts not docs/.vitepress/theme/index.ts"
  - "Verification anchor file paths read as cleanUrls:true output (page.html, not page/index.html); sitemap and 11 contract pages all rendered correctly"

patterns-established:
  - "Hand-written sidebar pattern: every contract URL has an explicit entry in themeConfig.sidebar (no auto-discovery)"
  - "Pitfall 5.1 grounding rule documented in CONVENTIONS.md §2 — every example value originates in openapi.json or source"
  - "Mermaid sequenceDiagram transaction-boundary convention (CONVENTIONS.md §3) — rect rgb(232,245,233) wraps pre_processing+apply+store_event, Note marks commit_transaction"

requirements-completed:
  - SITE-01
  - SITE-02
  - SITE-03
  - SITE-04
  - SITE-05
  - SITE-06
  - SITE-08
  - SITE-10
  - SITE-12

# Metrics
duration: 5m 26s
completed: 2026-04-29
---

# Phase 01 Plan 02: VitePress Scaffold + URL Contract Summary

**VitePress 1.6.4 site scaffolds at `docs/`, builds 11 contract pages cleanly, hand-written sidebar locks the URL shape, and CONVENTIONS.md captures the D-14 patterns Phase 2/3 will fill.**

## Performance

- **Duration:** 5 min 26 sec
- **Started:** 2026-04-29T15:51:04Z
- **Completed:** 2026-04-29T15:56:30Z
- **Tasks:** 9 / 9 (Task 1 absorbed into 01-01's prior commit — see Deviations §1)
- **Files modified:** 18 created (1 prior plan deletion already executed by 01-01)

## Accomplishments

- VitePress 1.6.4 builds the entire URL contract (homepage + 10 contract pages) in 19.52s with no errors.
- All 9 SITE requirements owned by this plan are met: SITE-01, 02, 03, 04, 05, 06, 08, 10, 12.
- Sitemap emits all 11 pages under `https://progresslabit.github.io/progress-platform/...` (CP-3 satisfied: sitemap hostname includes the GH-Pages base path).
- Mermaid plugin loads with ELK layout engine registered behind `typeof window !== 'undefined'` SSR guard (CP-5) — no `window is not defined` SSR crash.
- vitepress-openapi wired against the placeholder `public/openapi.json` (paths:{}, OpenAPI 3.0.4) — Phase 2 swaps in the real export without re-wiring.
- Brand CSS variables only (Pitfall 1.5 honored — no Layout.vue override).
- `editLink.pattern` and CONVENTIONS.md §5 both template to `github.com/ProgressLabIT/...`, never `gitlab.com` (D-13/SITE-08 enforced).
- CONVENTIONS.md authored with D-14 initial scope: endpoint docstring shape, AI prompt scaffold STUB (Phase 2/3 fills), Mermaid transaction-boundary convention, curation gate, GitHub permalink template, kebab-case URL convention.

## Task Commits

| Task | Name | Commit | Type |
|------|------|--------|------|
| 1 | Delete `docs/superpowers/` (D-05) | (absorbed into 01-01 commit `febf6375`) | chore — pre-executed |
| 2 + 3 | Scaffold `docs/package.json` + `package-lock.json` + `.gitignore` (npm install) | `f17156b7` | feat |
| 4 | Wire `docs/.vitepress/config.ts` (nav, sidebar, sitemap, search, editLink) | `477f8a92` | feat |
| 5 | Wire `docs/.vitepress/theme/{index.ts, custom.css}` (vitepress-openapi + ELK + SSR guard) | `4c1540e3` | feat |
| 6 | `docs/public/openapi.json` + `robots.txt` | `88268171` | feat |
| 7a | `package.json` ESM fix (`type: module` — Rule 3 auto-fix) | `c4c09f3e` | fix |
| 7b | 11 contract pages (homepage + 5 landings + 5 stubs) | `46853447` | feat |
| 8 | Smoke test `npm run docs:build` (no commit — captured in commit msg footer of c4c09f3e/46853447) | n/a | smoke |
| 9 | `.planning/workstreams/docs/CONVENTIONS.md` (D-14 initial scope) | `0e3e8261` | docs |

## Files Created/Modified

Created (18):

- `docs/package.json` — 5 dev deps exact-pinned, `type:module`, `engines.node 20.19.0`, `license Apache-2.0`
- `docs/package-lock.json` — 286 packages locked
- `docs/.gitignore` — node_modules, .vitepress/cache, .vitepress/dist
- `docs/.vitepress/config.ts` — base, sitemap, nav (D-07 5 sections), hand-written sidebar, MiniSearch, editLink (github), withMermaid wrapper
- `docs/.vitepress/theme/index.ts` — extends DefaultTheme, useOpenapi, ELK loader behind SSR guard, custom.css import
- `docs/.vitepress/theme/custom.css` — `--vp-c-brand-1/2/3` CSS variables only
- `docs/public/openapi.json` — OpenAPI 3.0.4 placeholder, `paths: {}`
- `docs/public/robots.txt` — allow-all + sitemap pointer to `progresslabit.github.io/progress-platform/sitemap.xml`
- `docs/index.md` — homepage, 5-link section overview
- `docs/api/index.md`, `docs/api/production/jobs/start.md`
- `docs/events/index.md`, `docs/events/production/job-started.md`
- `docs/cli/index.md`, `docs/cli/init.md`
- `docs/users/index.md`, `docs/users/production.md`
- `docs/admins/index.md`, `docs/admins/deployment.md`
- `.planning/workstreams/docs/CONVENTIONS.md` — D-14 initial scope (6 sections)

Pre-deleted by 01-01 (D-05):

- `docs/superpowers/plans/2026-04-15-custom-data.md` (deleted in `febf6375`)
- `docs/superpowers/specs/2026-04-15-custom-data-design.md` (deleted in `febf6375`)

## Decisions Made

- **package.json `type: module`** — added because VitePress 1.6.4 + vitepress-plugin-mermaid are ESM-only and esbuild's CJS resolution path failed during config load. The plan's package.json template (lifted verbatim from RESEARCH.md §Standard Stack) omitted this. Single-line fix; standard for any modern Vite-based config. Documented as Rule 3 deviation below.
- **`theme/index.ts` openapi.json import path: `../../public/openapi.json`** — the plan's snippet uses `../public/...`, which would only be correct if `index.ts` lived at `docs/.vitepress/index.ts`. Since it lives at `docs/.vitepress/theme/index.ts` (per the plan's own files-modified list), the path needs two `..` segments. Corrected silently in implementation; build verified correct resolution.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking issue] `package.json` missing `"type": "module"`**

- **Found during:** Task 8 (smoke test).
- **Issue:** First `npm run docs:build` failed with esbuild error: `"vitepress" resolved to an ESM file. ESM file cannot be loaded by require.` VitePress 1.6.4 and vitepress-plugin-mermaid 2.0.17 are ESM-only; without `"type": "module"` in `package.json`, esbuild defaults to CJS resolution for the config bundle.
- **Fix:** Added `"type": "module"` to `docs/package.json` between `"private": true` and `"license"`.
- **Files modified:** `docs/package.json` (1-line addition).
- **Verification:** Re-ran `npm run docs:build` → exit 0; 11 pages emitted in 19.52s; sitemap generated.
- **Committed in:** `c4c09f3e` (`fix(01-02): mark docs package as ESM (type: module)`).

**2. [Rule 1 — Bug] Plan snippet had wrong relative import path for `openapi.json`**

- **Found during:** Task 5 (writing `theme/index.ts`).
- **Issue:** Plan §"Task 5" code snippet has `import spec from '../public/openapi.json'`. The file lives at `docs/.vitepress/theme/index.ts`, so `../public/` resolves to `docs/.vitepress/public/`, which doesn't exist. The actual `public/` is at `docs/public/`, requiring `../../public/`.
- **Fix:** Used `../../public/openapi.json` in the import statement.
- **Files modified:** `docs/.vitepress/theme/index.ts`.
- **Verification:** Build succeeded; spec loaded without error.
- **Committed in:** `4c1540e3` (silent correction baked into task 5's initial write).

**3. [Rule 3 — Pre-execution by another plan] D-05 deletion already committed by 01-01**

- **Found during:** Task 1 (intended `git rm -r docs/superpowers/`).
- **Issue:** When this plan's executor checked, `docs/superpowers/` was already gone from `HEAD` — deleted by parallel plan 01-01 in commit `febf6375` ("feat(01-01): add CONTRIBUTING.md with mirror flow"). 01-01's plan owned OSS scaffolding but absorbed the D-05 cleanup as part of its commit. Per the executor prompt this plan owned `docs/**`, but the deletion preceded it in the timeline.
- **Fix:** Skipped Task 1's `git rm` and intended commit; verified `docs/` is clean before proceeding to Task 2.
- **Files modified:** None (no-op task).
- **Verification:** `test ! -d docs/superpowers` passed before any other Task 1-9 file was written.
- **Committed in:** N/A — already in `febf6375`.

**Verification anchor file-path note (informational, not a deviation):** The plan's `<verification>` block expects `dist/api/production/jobs/start/index.html` style paths. With `cleanUrls: true`, VitePress emits `dist/api/production/jobs/start.html` (single file at the top level, with the URL `/api/production/jobs/start` resolved by GH Pages serving `<page>.html` as `<page>` or `<page>/`). All 11 contract pages emit correctly under both interpretations; the URL contract is intact (sitemap-verified). The verification block in 01-03 should match against `<page>.html` rather than `<page>/index.html`.

## Verification Output

All `<verification>` block checks passed (run from `/Users/luca/dev/progress/progress-platform/`):

- `docs/package.json` exact pins (vitepress=1.6.4, plugin-mermaid=2.0.17, openapi=0.1.20, engines.node=20.19.0, license=Apache-2.0): **OK**
- `docs/package-lock.json` present (lockfileVersion 3, 286 packages): **OK**
- `docs/.gitignore` excludes node_modules, dist, cache: **OK**
- `npm run docs:build` exit 0; build complete in 19.52s; 1 informational chunk-size warning (vitepress-openapi bundle ~500kB, expected): **OK**
- All 11 contract HTML pages emitted (under cleanUrls naming `<page>.html`): **OK**
- `docs/.vitepress/dist/sitemap.xml` exists with 11 entries under `https://progresslabit.github.io/progress-platform/`: **OK**
- `docs/.vitepress/dist/robots.txt` includes `Sitemap: https://progresslabit.github.io/progress-platform/sitemap.xml`: **OK**
- `themeConfig.search.provider = 'local'`: **OK**
- `sitemap.hostname = 'https://progresslabit.github.io/progress-platform/'`: **OK**
- 5 nav entries (API, Events, CLI, Users, Admins): **OK**
- 10 markdown contract files (docs/api/**, docs/events/**, docs/cli/**, docs/users/**, docs/admins/**): **OK**
- No auto-sidebar plugin in dependencies: **OK**
- `editLink.pattern` → github.com (no gitlab.com in editLink): **OK** (gitlab.com still appears once under `socialLinks`, intentional per plan §Task 4)
- `vitepress-openapi/client` imported in `theme/index.ts`: **OK**
- `typeof window !== 'undefined'` SSR guard around `mermaid.registerLayoutLoaders(elkLayouts)`: **OK**
- `withMermaid` wrapping in `config.ts`: **OK**
- No `.html` suffix in sidebar `link:` values: **OK**
- `docs/superpowers/` deleted: **OK**
- `.planning/workstreams/docs/CONVENTIONS.md` exists with `transaction-boundary`, `github.com/ProgressLabIT/progress-platform`, `kebab-case` strings: **OK**

## Threat Surface Scan

No new security-relevant surface introduced beyond what `<threat_model>` enumerated. Supply-chain (T-01-02-01) mitigated by exact pins on the three risky packages and a committed `package-lock.json`. SSR-pass crash (T-01-02-02) mitigated and tested via the build smoke. `editLink` spoofing (T-01-02-04) mitigated by hardcoded github.com and verified by grep.

No new threat flags.

## Coverage Matrix

| Req | Status | Verification |
|-----|--------|--------------|
| SITE-01 | ✓ | docs/package.json exists with vitepress 1.6.4; npm run docs:build exit 0 |
| SITE-02 | ✓ | vitepress-plugin-mermaid 2.0.17 in deps; @mermaid-js/layout-elk registered with SSR guard |
| SITE-03 | ✓ | themeConfig.sidebar hand-written; no auto-sidebar plugin in deps |
| SITE-04 | ✓ | nav array has 5 entries in D-07 order |
| SITE-05 | ✓ | themeConfig.search.provider = 'local' |
| SITE-06 | ✓ | sitemap.hostname = 'https://progresslabit.github.io/progress-platform/' |
| SITE-08 | ✓ | editLink.pattern + CONVENTIONS.md §5 both target github.com/ProgressLabIT/progress-platform |
| SITE-10 | ✓ | 10 markdown contract files exist; sidebar entries match; sitemap has 11 entries (homepage + 10) |
| SITE-12 | ✓ | vitepress-openapi/client imported; docs/public/openapi.json valid OpenAPI 3.0.4 with paths:{} |

Plan does NOT cover SITE-07 (deploy workflow — owned by 01-03) or SITE-09 (lychee CI — owned by 01-03). 01-02 is a strict prerequisite for 01-03: the build now succeeds locally, so the deploy workflow has something to ship.

## Known Stubs

| Stub | File | Reason | Resolves in |
|------|------|--------|-------------|
| `Coming soon` placeholder content | All 10 contract pages (api/index.md, api/production/jobs/start.md, events/*, cli/*, users/*, admins/*) | D-07 strategy: Phase 1 locks URL contract shape; deeper enumeration is Phase 2/3 generator output | Phase 2 (api/events) and Phase 3 (cli/users/admins) |
| `paths: {}` in `docs/public/openapi.json` | `docs/public/openapi.json` | Phase 2 will populate from `scripts/export_openapi.py` against the real backend | Phase 2 |
| AI drafting prompt scaffold (`§2 STUB` in CONVENTIONS.md) | `.planning/workstreams/docs/CONVENTIONS.md` §2 | D-14 explicitly stubs this; pattern crystallizes during Phase 2/3 drafting sessions | Phase 2/3 |

## Self-Check: PASSED

Verified files exist:

- FOUND: `docs/package.json`
- FOUND: `docs/package-lock.json`
- FOUND: `docs/.gitignore`
- FOUND: `docs/.vitepress/config.ts`
- FOUND: `docs/.vitepress/theme/index.ts`
- FOUND: `docs/.vitepress/theme/custom.css`
- FOUND: `docs/public/openapi.json`
- FOUND: `docs/public/robots.txt`
- FOUND: `docs/index.md`
- FOUND: `docs/api/index.md`, `docs/api/production/jobs/start.md`
- FOUND: `docs/events/index.md`, `docs/events/production/job-started.md`
- FOUND: `docs/cli/index.md`, `docs/cli/init.md`
- FOUND: `docs/users/index.md`, `docs/users/production.md`
- FOUND: `docs/admins/index.md`, `docs/admins/deployment.md`
- FOUND: `.planning/workstreams/docs/CONVENTIONS.md`

Verified commits exist:

- FOUND: `f17156b7` (package scaffold)
- FOUND: `477f8a92` (config.ts)
- FOUND: `4c1540e3` (theme)
- FOUND: `88268171` (public assets)
- FOUND: `c4c09f3e` (type:module fix)
- FOUND: `46853447` (11 markdown pages)
- FOUND: `0e3e8261` (CONVENTIONS.md)

D-05 absorbed by 01-01 commit `febf6375` (verified).
