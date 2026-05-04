---
phase: 01-scaffold-public-foundation
plan: 03
slug: gh-actions-deploy-lychee-gate
workstream: docs
subsystem: docs-ci

tags: [github-actions, github-pages, lychee, dependabot, ci-deploy, ci-link-check, oss-launch]

# Dependency graph
requires:
  - phase: 01-scaffold-public-foundation/01-02
    provides: "VitePress 1.6.4 build green at docs/; URL contract locked; cleanUrls=true emits dist/<page>.html"
  - phase: 01-scaffold-public-foundation/01-01
    provides: "protect-main ruleset (id=15731781); GitHub repo + PVR + topics; mirror flow documented in CONTRIBUTING.md"
provides:
  - ".github/workflows/deploy-docs.yml — build+deploy VitePress to GitHub Pages on push to DEV; concurrency cancel-in-progress=false; OIDC publish via id-token: write; npm + VitePress build cache; fetch-depth: 0 for lastUpdated"
  - ".github/workflows/lychee.yml — anchor-aware dead-link CI on every PR + push to DEV; lychee-action@v2 with --include-fragments + --root-dir + --base + --config (CP-10)"
  - ".github/dependabot.yml — weekly PRs for npm (/docs), github-actions (/), gitlab-ci (/)"
  - "lychee.toml — declarative excludes (localhost variants), exclude_all_private, cache 2d, max_retries 2"
  - "Status-check contexts now exist on GitHub side: 'build' (deploy-docs.yml) + 'linkChecker' (lychee.yml) — ready for the orchestrator's post-deploy ruleset re-arm against ruleset id 15731781"
affects:
  - "phase 4 launch readiness — Pages site live + lychee gate ready by May 14 dry run (SITE-11 prereq)"
  - "phase 2/3 content authoring — every PR now gated by lychee against the contract URLs"

tech-stack:
  added:
    - "GitHub Actions workflows (deploy-docs.yml, lychee.yml)"
    - "Dependabot v2 manifest (npm + github-actions + gitlab-ci ecosystems)"
    - "lychee CLI (anchor-aware link checker, lycheeverse/lychee-action@v2)"
  patterns:
    - "Workflow-pinned to floating major tags (@v2/@v4/@v5/@v6) for v1; SHA-pin hardening tracked in STATE.md Post-Launch TODOs (T-01-03-02)"
    - "Pages deploy triggered ONLY by push to DEV + workflow_dispatch — NEVER by PR (T-01-03-03 forked-PR mitigation)"
    - "Concurrency group=pages cancel-in-progress=false (VitePress official guidance, T-01-03-06)"
    - "Cache scoped via cache-dependency-path: docs/package-lock.json (root yarn.lock unrelated)"
    - "Lychee config split: CLI args authoritative for --root-dir/--base/--include-fragments (CP-10); lychee.toml supplements with excludes + retries"

key-files:
  created:
    - .github/workflows/deploy-docs.yml
    - .github/workflows/lychee.yml
    - .github/dependabot.yml
    - lychee.toml
  modified: []

key-decisions:
  - "Used actions/configure-pages@v5 (per plan body) rather than @v4 (per RESEARCH.md §F.1) — plan body is authoritative; v5 is current major; matches plan-locked OIDC publish path."
  - "Lychee workflow uses --config pointing at /lychee.toml for excludes; CLI args remain authoritative for --root-dir / --base / --include-fragments (CP-10) — split is intentional and documented in lychee.toml header."
  - "Live-deploy verification deferred to maintainer checkpoint (Tasks 5–7 of plan): docs commits live on local GSD only; have not propagated to GitLab/GitHub mirror yet. Init context confirms re-arming required_status_checks against ruleset 15731781 is also a post-deploy maintainer step."

metrics:
  start: "2026-05-02T21:09:13Z"
  completed: "2026-05-02T21:11:56Z"
  duration_sec: 163
  duration_human: "2m 43s"
  tasks_completed: 4
  tasks_total: 7
  tasks_deferred_to_maintainer: 3
  commits: 3
  files_created: 4
  files_modified: 0
---

# Phase 01 Plan 03: GitHub Actions Deploy + Lychee Gate Summary

**Workflow + supply-chain scaffolding for the GitHub mirror is committed locally on `GSD`. Pages-deploy and lychee gate go live on the maintainer's next GitLab `Update now` push; ruleset `protect-main` (id=15731781) is then re-armed with `required_status_checks: build + linkChecker`.**

## Tasks Completed (autonomous)

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Author `.github/workflows/deploy-docs.yml` (RESEARCH.md §F.1 + plan body, configure-pages@v5) | `c798dceb` | `.github/workflows/deploy-docs.yml` |
| 2 | Author `.github/workflows/lychee.yml` + `lychee.toml` (RESEARCH.md §F.2 + Pitfall 1.4 + CP-10) | `fe72c160` | `.github/workflows/lychee.yml`, `lychee.toml` |
| 3 | Author `.github/dependabot.yml` (npm /docs + github-actions / + gitlab-ci /) | `c9de1b73` | `.github/dependabot.yml` |
| 4 | Atomic-commit-per-task strategy (per plan `<commit_strategy>`) | n/a | covered by 1–3 |

## Tasks Deferred to Maintainer (live-deploy checkpoints)

Per init-context policy: "live-deploy verification: SURFACE as `[CHECKPOINT:human-action]` since the docs commits haven't been propagated to GitHub yet."

| # | Task | Why deferred | Resume signal |
|---|------|--------------|---------------|
| 5 | First push + Pages deploy verification (CP-7 PAT canary, watch deploy run, curl `/`) | Mirror push (GitLab `Update now`) is a UI step on a system the executor cannot drive | Reply `deployed <run-url>` once first deploy run completes |
| 6 | Live URL contract verification (11 URLs, sitemap hostname, top-nav, MiniSearch, openapi.json placeholder) | Requires the live Pages URL to be reachable | Reply `urls-verified` once 11/11 return HTTP 200 |
| 7 | Branch ruleset status-check verification (build + linkChecker check-runs) + `required_status_checks` re-arm | Ruleset rearm is a post-deploy `gh api PATCH` against id 15731781 (init context); requires at least one workflow run on GH `DEV` | Reply `ruleset-rearmed` once `gh api .../rulesets/15731781` shows `build` + `linkChecker` in `required_status_checks.contexts` |

## Commits

| Hash | Message | Files |
|------|---------|-------|
| `c798dceb` | feat(01-03): add VitePress GH Pages deploy workflow | `.github/workflows/deploy-docs.yml` |
| `fe72c160` | feat(01-03): add lychee dead-link CI gate (anchor-aware) | `.github/workflows/lychee.yml`, `lychee.toml` |
| `c9de1b73` | chore(01-03): configure dependabot for npm + actions + gitlab-ci | `.github/dependabot.yml` |

All commits land on `GSD` branch (per project memory `GSD Commits → GSD Branch`); no Claude co-author trailer.

## Verification Results

### Automated PASS (run during this execution)

All file-system + structural checks from plan `<verification>` block that don't require live workflows:

- **Files exist** — `.github/workflows/deploy-docs.yml`, `.github/workflows/lychee.yml`, `.github/dependabot.yml`, `lychee.toml` all present.
- **YAML well-formed** — all three workflow/manifest files parse cleanly via `pyyaml`; `lychee.toml` parses cleanly via `toml`.
- **Job names match ruleset contexts** — `build` (deploy-docs.yml jobs.build) and `linkChecker` (lychee.yml jobs.linkChecker) match the dormant `required_status_checks.contexts` declared in plan 01-01 Task 7.
- **Deploy permissions scoped** (T-01-03-01) — `contents: read`, `pages: write`, `id-token: write`. NO `contents: write`, NO `actions: write`.
- **Deploy triggers** (T-01-03-03) — only `push: branches: [DEV]` + `workflow_dispatch`. Forked-PR Pages-publish vector closed.
- **Lychee CLI flags** (CP-10) — workflow `args` contain `--include-fragments`, `--root-dir`, `--base`, `--config` (lychee.toml).
- **Lychee triggers** (SITE-09) — `pull_request` + `push: branches: [DEV]`. Both gates exist.
- **Concurrency** (T-01-03-06) — `group: pages`, `cancel-in-progress: false`.
- **fetch-depth: 0** (CP-9) — present in deploy-docs.yml on `actions/checkout@v5` for VitePress `lastUpdated`.
- **Node version 20.19.0** — both workflows pin to `20.19.0` (matches `docs/package.json` engines).
- **npm cache scope** — `cache-dependency-path: docs/package-lock.json` on both workflows (yarn.lock at repo root excluded).
- **Dependabot ecosystems** — npm /docs, github-actions /, gitlab-ci /; weekly schedules; PR limits 5/5/3; labels per plan.
- **Local `docs/.vitepress/dist/` exists from 01-02 build** — lychee `--root-dir` will resolve correctly when CI rebuilds the dist (sanity check on directory contract).
- **Working tree clean of unintended deletions** — `git diff --diff-filter=D HEAD~3 HEAD` returned nothing.

### Deferred to Maintainer (live-CI required)

These checks from plan `<verification>` cannot run until the docs commits propagate to GitHub mirror via GitLab `Update now`:

```bash
# Anchor 4 — push triggers Actions deploy in <10 min:
gh run list --repo ProgressLabIT/progress-platform --workflow=deploy-docs.yml --limit 1 \
  --json status,conclusion,startedAt,updatedAt \
  | jq -e '.[0].conclusion == "success"
           and ((.[0].updatedAt | fromdateiso8601) - (.[0].startedAt | fromdateiso8601)) < 600'

# Anchor 4 — 11 contract URLs return HTTP 200:
BASE=https://progresslabit.github.io/progress-platform
for path in / /api/ /api/production/jobs/start/ /events/ /events/production/job-started/ \
            /cli/ /cli/init/ /users/ /users/production/ /admins/ /admins/deployment/; do
  curl -fsS -o /dev/null -w "${path} → %{http_code}\n" "${BASE}${path}"
done

# Anchor 4 — sitemap hostname + MiniSearch enabled:
curl -fsS "${BASE}/sitemap.xml" | grep -F "https://progresslabit.github.io/progress-platform/"
curl -fsS "${BASE}/" | grep -E "VPLocalSearch|provider.+local"

# Anchor 4 — openapi.json placeholder served at site root:
curl -fsS -o /dev/null -w "%{http_code}\n" "${BASE}/openapi.json"  # expect 200

# Anchor 5 — lychee runs on DEV push, completes successfully:
gh run list --repo ProgressLabIT/progress-platform --workflow=lychee.yml --branch=DEV --limit 1 \
  --json conclusion | jq -e '.[0].conclusion == "success"'

# Branch ruleset status checks now active:
gh api /repos/ProgressLabIT/progress-platform/commits/DEV/check-runs \
  --jq '.check_runs[] | select(.name == "build" or .name == "linkChecker") | "\(.name):\(.conclusion)"' | sort -u

# Mirror SHA match after the workflow files land:
GL_SHA=$(git ls-remote https://gitlab.com/progresslab/progress-platform DEV | awk '{print $1}')
GH_SHA=$(git ls-remote https://github.com/ProgressLabIT/progress-platform DEV | awk '{print $1}')
test -n "$GL_SHA" && test "$GL_SHA" = "$GH_SHA"
```

**Maintainer propagation steps (verbatim from init context):**
1. Cherry-pick / merge docs P01 commits onto DEV branch (latest tip on GSD: `c9de1b73`; precedessors include 01-02 + 01-01 commits and `8cb144a1` rewrite).
2. Push DEV to GitLab.
3. Trigger GitLab → GitHub mirror `Update now` (Repository → Mirroring repositories).
4. Wait for first GitHub Actions deploy to finish.
5. Re-arm `required_status_checks` on ruleset id 15731781 via `gh api -X PATCH /repos/ProgressLabIT/progress-platform/rulesets/15731781` adding `{ "type": "required_status_checks", "parameters": { "required_status_checks": [{"context":"build"},{"context":"linkChecker"}], "strict_required_status_checks_policy": false } }` to the rules array.

**01-02 deviation #4 carryforward (cleanUrls):** the Anchor-3 nav-extraction sub-script in plan `<verification>` already correctly anchors against `<div class="VPNavBar">` — no adjustment needed for cleanUrls. The HTML-shape paths (`<page>/index.html` vs `<page>.html`) only matter for local-dist inspection, which is not performed in this plan's verification.

## Deviations from Plan

### Auto-fixed / clarified

**1. [Information — `actions/configure-pages` version mismatch between plan body and RESEARCH.md]**

- **Where:** Plan body §Task 1 yaml: `actions/configure-pages@v5`. RESEARCH.md §F.1 yaml: `actions/configure-pages@v4`.
- **Resolution:** Used `@v5` per the plan body (which is authoritative per the executor protocol — RESEARCH.md is supporting evidence, plan body is the implementation contract). `@v5` is the current major; same OIDC publish path as `@v4`; no behavioral difference at the contract surface.
- **Files affected:** `.github/workflows/deploy-docs.yml` only.
- **Threat impact:** none. Pinning to `@v5` is consistent with T-01-03-02's "pin to floating major" v1 stance.

**2. [Information — lychee `--exclude` moved from CLI args to `lychee.toml`]**

- **Where:** RESEARCH.md §F.2 puts `--exclude` directly in workflow `args:`. Plan body §Task 2 puts excludes in `lychee.toml` and references `--config` from the workflow.
- **Resolution:** Followed plan body — split is more code-review-friendly (excludes change more often than CLI flags) and the plan's text explicitly says "declarative supplement; CLI flags above already work standalone but this captures excludes in code-review-able form".
- **Files affected:** `.github/workflows/lychee.yml` (uses `--config`), `lychee.toml` (carries excludes).
- **Threat impact:** none.

**3. [Information — three live-deploy tasks deferred to maintainer per init context]**

- **Where:** Init context `<additional_context>`: "Live-deploy verification (curl Pages URL, gh run list, etc): SURFACE as [CHECKPOINT:human-action] since the docs commits haven't been propagated to GitHub yet."
- **Resolution:** Tasks 5, 6, 7 of the plan are surfaced as deferred to maintainer in the "Tasks Deferred to Maintainer" table above. Resume signals defined.
- **Threat impact:** none — this is process scheduling, not implementation.

### No auto-fixes triggered (Rules 1/2/3)

No bugs found in the plan's workflow/config templates. No missing critical functionality identified beyond what the plan and threat model already enumerate. No blocking issues prevented execution.

## Threat Surface Compliance

All threat-model dispositions held:

| Threat ID | Disposition | Evidence in this plan |
|-----------|-------------|------------------------|
| T-01-03-01 (privilege escalation via permissions block) | mitigate | `.github/workflows/deploy-docs.yml` permissions = `{contents: read, pages: write, id-token: write}`; lychee.yml permissions = `{contents: read}`. NO `contents: write` anywhere. |
| T-01-03-02 (action SHA pinning) | mitigate (post-launch hardening) | All `uses:` pinned to floating major (`@v2/@v4/@v5/@v6`). Tracked in STATE.md `Post-Launch TODOs` (already present from prior runs). |
| T-01-03-03 (forked-PR Pages publish) | mitigate | `deploy-docs.yml on:` block contains `push: branches: [DEV]` + `workflow_dispatch` only — no `pull_request:`. Lychee runs on PR but has `contents: read` only and no Pages access. |
| T-01-03-04 (npm lifecycle script tampering) | accept (post-launch) | Dependabot configured to surface advisories. `--ignore-scripts` post-launch hardening tracked. |
| T-01-03-05 (lychee leaking internal URLs) | accept | Phase 1 site is fully public scaffold. `lychee.toml` excludes localhost / 127.0.0.1 / progress.localhost. |
| T-01-03-06 (concurrent deploy partial-deploy) | mitigate | `concurrency: { group: pages, cancel-in-progress: false }` in deploy-docs.yml. |
| T-01-03-07 (build artifact leaks .env) | accept | Plan 01-02 confirmed no env consumption in `docs/`; this plan adds no new env-touching paths. |
| T-01-03-08 (branch protection misconfig blocks mirror) | mitigate | Init context confirms orchestrator dropped `required_status_checks` pre-execution; will re-arm post-deploy against ruleset id 15731781 once at least one of `build`/`linkChecker` has run. |

No new threat surface introduced. No threat flags.

## Coverage Matrix

| Requirement | Status | Verification |
|-------------|--------|--------------|
| **SITE-07** (GH Actions deploys VitePress to Pages on push to DEV) | **complete (workflow files)**; live-deploy pending maintainer push | `.github/workflows/deploy-docs.yml` exists; triggers on `push: [DEV]`; `actions/deploy-pages@v4`; OIDC publish via `id-token: write`. Live verification deferred (Task 5). |
| **SITE-09** (lychee dead-link CI on every PR; --include-fragments enabled) | **complete (workflow files)**; live-run pending maintainer push | `.github/workflows/lychee.yml` exists; triggers on PR + DEV push; args contain `--include-fragments`, `--root-dir`, `--base`, `--config`; `fail: true`. Live verification deferred (Task 7). |

## Known Stubs

None introduced by this plan. Plan 01-02's stubs (10 contract pages with "Coming soon" placeholders, `paths: {}` in `openapi.json`, AI-prompt-scaffold STUB in CONVENTIONS.md) carry forward unchanged.

## Self-Check: PASSED

Files created exist:
- FOUND: `.github/workflows/deploy-docs.yml`
- FOUND: `.github/workflows/lychee.yml`
- FOUND: `.github/dependabot.yml`
- FOUND: `lychee.toml`

Commits exist on GSD branch:
- FOUND: `c798dceb` (feat(01-03): add VitePress GH Pages deploy workflow)
- FOUND: `fe72c160` (feat(01-03): add lychee dead-link CI gate (anchor-aware))
- FOUND: `c9de1b73` (chore(01-03): configure dependabot for npm + actions + gitlab-ci)

Job names match plan 01-01 ruleset contexts:
- FOUND: `build` job in deploy-docs.yml
- FOUND: `linkChecker` job in lychee.yml

Threat-model dispositions all upheld (8/8); no new threat surface introduced.

---

*Generated 2026-05-02 by docs/01-03-PLAN.md execution. Live-deploy + ruleset re-arm tasks routed to maintainer per init-context CHECKPOINT policy.*
