---
phase: 01-scaffold-public-foundation
plan: 01
slug: oss-table-stakes-repo-settings
workstream: docs
status: checkpoint-pending
type: execute
wave: 1
subsystem: docs
tags:
  - oss-launch
  - github-mirror
  - apache-2.0
  - branch-protection
requirements:
  - MIR-01
  - MIR-02
  - MIR-03
  - MIR-04
  - MIR-05
  - MIR-06
  - MIR-07
requirements_complete:
  - MIR-03
  - MIR-04
  - MIR-05
  - MIR-06
  - MIR-07
requirements_pending_checkpoint:
  - MIR-01
  - MIR-02
dependency_graph:
  requires: []
  provides:
    - "Apache 2.0 LICENSE at repo root"
    - "OSS table-stakes (CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, PR template)"
    - "ARCHITECTURE.md extracted from old README"
    - "README.md rewritten per Pitfall 4.4 8-section structure"
    - "GitHub repo settings (Issues/Discussions on, Wiki off, PVR on, topics, homepage)"
    - "Branch protection ruleset 'protect-main' on default branch"
  affects:
    - "Plan 01-02 (VitePress scaffold) consumes the Apache 2.0 license declaration in docs/package.json"
    - "Plan 01-03 (GitHub Actions) populates the dormant 'build' + 'linkChecker' status checks declared in protect-main"
    - "Phase 4 launch-day SHA-match script depends on the mirror flow documented in CONTRIBUTING.md"
tech-stack:
  added:
    - "Apache 2.0 license (project-level)"
    - "GitHub PVR (Private Vulnerability Reporting)"
    - "GitHub Repository Ruleset 'protect-main'"
  patterns:
    - "Mirror-honest CONTRIBUTING.md (Pitfall 4.2 verbatim)"
    - "Pitfall 4.4 8-section README structure"
key-files:
  created:
    - CONTRIBUTING.md
    - SECURITY.md
    - CODE_OF_CONDUCT.md
    - ARCHITECTURE.md
    - .github/PULL_REQUEST_TEMPLATE.md
  modified:
    - LICENSE
    - README.md
    - webapps/main/package.json
    - webapps/warehouse/package.json
decisions:
  - "Followed plan as locked — 8-section README, ≤150 lines (final 55), NATS-not-Kafka."
  - "GitHub PVR enabled via PUT (REST endpoint requires PUT, not the plan's PATCH)."
  - "Renamed tracked filename `readme.md` → `README.md` for OSS-conventional capitalization (case-insensitive macOS edit required two-step git mv)."
  - "PVR API call deviates from plan command (PUT not PATCH); same behavioral outcome."
metrics:
  start: "2026-04-29T15:50:10Z"
  completed: "2026-04-29T15:58:31Z"
  duration_sec: 501
  duration_human: "8m 21s"
  tasks_completed: 7
  tasks_total: 8
  commits: 8
  files_created: 5
  files_modified: 4
---

# Phase 01 Plan 01: OSS Table-Stakes & Repo Settings Summary

Established the public-facing OSS foundation for `github.com/ProgressLabIT/progress-platform`: replaced MIT with Apache 2.0, authored mirror-honest CONTRIBUTING / SECURITY / CODE_OF_CONDUCT / PR-template, extracted ARCHITECTURE.md from the legacy README, rewrote README per Pitfall 4.4 (≤150 lines, mirror banner, docs-site link, NATS not Kafka), and applied GitHub repo settings + PVR + branch ruleset via `gh`. Task 8 (GitLab→GitHub mirror verification) is the human-action checkpoint pending user execution in the GitLab UI.

## Tasks Completed

| Task | Description | Commit | Notes |
|------|-------------|--------|-------|
| 0 | Stale-ref correction (`progresslab` → `ProgressLabIT` GitHub-org refs) | n/a | Verified clean — all forms already correct in workstream artifacts; no changes required |
| 1 | Author CONTRIBUTING.md (Pitfall 4.2 verbatim + D-15 mirror flow) | `febf6375` | SDK auto-bundled pre-existing staged deletions of `docs/superpowers/**` (D-05 deletions, owned by plan 01-02 scope) |
| 2 | SECURITY.md, CODE_OF_CONDUCT.md (Contributor Covenant 2.1), `.github/PULL_REQUEST_TEMPLATE.md` | `bbe48c96` | SECURITY.md is 7 body lines (well under D-02 cap of 15) |
| 3 | LICENSE swap (MIT → Apache 2.0, 202 lines) | `4e5b660e` | Plain `curl` from apache.org/licenses/LICENSE-2.0.txt |
| 4a | Extract ARCHITECTURE.md from legacy README content | `ba3a72c4` | 100 lines covering system diagram, key decisions, layered backend, data flow, frontends, repo layout, tech stack |
| 4b | Rewrite README.md per Pitfall 4.4 / D-09 8-section structure | `8425b512` | Final 55 lines (well under 150-line cap); 5 OSS file links present; NATS not Kafka |
| 4c | Rename tracked file `readme.md` → `README.md` for OSS convention | `74f6ccca` | Two-step git mv on macOS case-insensitive FS |
| 7 (commit) | webapp `package.json` license fields → Apache-2.0 | `fa679217` | Single-key insertion preserving formatting (per threat T-01-01-05) |
| 5 | Verify ProgressLabIT/progress-platform repo state | n/a (gh CLI) | Repo exists, public; pre-edit state captured at `/tmp/repo-state-pre.json` |
| 6 | `gh repo edit` (description/homepage/issues/discussions/wiki/topics) + PVR enable | n/a (GitHub state) | All 7 required topics added (alongside 6 pre-existing); PVR enabled |
| 7 | `gh api` create `protect-main` branch ruleset | n/a (GitHub state) | id=15731781; deletion + non_fast_forward + dormant required_status_checks=[build, linkChecker] |
| 8 | CHECKPOINT — GitLab UI mirror verification | **PENDING** | See "Awaiting" below |

## Commits

| Hash | Message |
|------|---------|
| `febf6375` | feat(01-01): add CONTRIBUTING.md with mirror flow |
| `bbe48c96` | feat(01-01): add SECURITY.md, CODE_OF_CONDUCT.md, PR template |
| `4e5b660e` | chore(01-01): swap LICENSE to Apache 2.0 |
| `ba3a72c4` | docs(01-01): extract architecture overview into ARCHITECTURE.md |
| `8425b512` | docs(01-01): rewrite README per Pitfall 4.4 with mirror banner |
| `74f6ccca` | chore(01-01): canonicalize README.md filename casing |
| `fa679217` | chore(01-01): set Apache-2.0 license field in webapp package.json |

(Pre-existing commit `bbe48c96` already covered Task 2; this list reflects new commits made in this plan run.)

## Verification Results (local)

All locally-runnable verification commands from the plan's `<verification>` block PASS:

- ✓ `head -5 LICENSE | grep -F "Apache License"` — Apache 2.0 confirmed
- ✓ `grep -F "read-only mirror" README.md` — mirror banner present
- ✓ `grep -F "https://progresslabit.github.io/progress-platform/" README.md` — docs URL present
- ✓ `grep -qi "NATS"` and `! grep -qi "Kafka"` — README correctly says NATS, not Kafka
- ✓ `wc -l README.md` ≤ 150 — 55 lines actual
- ✓ `grep -F "git ls-remote" CONTRIBUTING.md` — mirror SHA-match command documented
- ✓ SECURITY.md body-line count ≤ 15 — 7 body lines
- ✓ `grep -F "Contributor Covenant" CODE_OF_CONDUCT.md` — Covenant 2.1 confirmed
- ✓ `grep -F "read-only mirror" .github/PULL_REQUEST_TEMPLATE.md` — mirror notice present
- ✓ No stale MIT references in repo-root visitor-facing files (`README.md`, `LICENSE`, all OSS table-stakes, both webapp `package.json`s)
- ✓ Repo settings: `hasIssuesEnabled=true`, `hasDiscussionsEnabled=true`, `hasWikiEnabled=false`
- ✓ `homepageUrl == "https://progresslabit.github.io/progress-platform/"`
- ✓ All 7 required topics present (manufacturing, mes, iiot, sparkplug-b, industry40, fastapi, vue3)
- ✓ PVR enabled (`gh api .../private-vulnerability-reporting | jq .enabled` → `true`)
- ✓ `protect-main` ruleset listed at `/repos/.../rulesets`

Mirror-side verifications (Anchor 1 / MIR-01 / MIR-02) **deferred to checkpoint**.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] PVR API call uses PUT instead of PATCH**

- **Found during:** Task 6
- **Issue:** Plan command `gh api -X PATCH /repos/.../private-vulnerability-reporting -F enabled=true` returned `404 Not Found` (the GitHub PVR endpoint accepts PUT to enable, DELETE to disable; PATCH is not supported).
- **Fix:** Used `gh api -X PUT /repos/ProgressLabIT/progress-platform/private-vulnerability-reporting`.
- **Verification:** `gh api .../private-vulnerability-reporting | jq .enabled` → `true`.
- **Commit:** n/a (no file change).

**2. [Rule 1 - Bug] README tracked at `readme.md` (lowercase) rather than conventional `README.md`**

- **Found during:** Task 4 (README rewrite commit)
- **Issue:** macOS case-insensitive filesystem masked the fact that the tracked file is `readme.md`. My initial Write to `README.md` actually wrote to the existing `readme.md` in place. The `gsd-sdk query commit README.md` returned `nothing staged` because the SDK passed the exact filename to git's case-sensitive index. Subsequently passed `readme.md` and committed.
- **Follow-up fix:** Performed a two-step `git mv readme.md README.tmp && git mv README.tmp README.md` to canonicalize to OSS-convention uppercase-R. Tracked filename is now `README.md`.
- **Files modified:** `readme.md` → `README.md` (rename only).
- **Commits:** `8425b512` (content), `74f6ccca` (case rename).

**3. [Rule 1 - Bug] Verification regex over-strict on file-link count**

- **Found during:** Task 4 README final-length check.
- **Issue:** Plan's local verification used `grep -cE '\[(CONTRIBUTING|CODE_OF_CONDUCT|SECURITY|ARCHITECTURE|LICENSE)\.md\]'` and required the count `≥5`. The plan's own README template, however, links `LICENSE` without a `.md` extension (`[LICENSE](LICENSE)`), so the regex can never match more than 4. The substantive intent (link to all 5 files) is satisfied — all 5 are linked.
- **Fix:** Used corrected pattern `\[(CONTRIBUTING|CODE_OF_CONDUCT|SECURITY|ARCHITECTURE)\.md\]|\[LICENSE\]\(LICENSE\)` for verification, returning count=5.
- **Files modified:** none (verification-script issue, not a content issue).
- **Recommendation:** Update plan's verification regex to match the template; fix lives at the planner layer, not in this plan execution.

### SDK Commit Bundling Note

The first SDK commit (`febf6375`, Task 1) automatically bundled pre-existing staged deletions of `docs/superpowers/plans/2026-04-15-custom-data.md` and `docs/superpowers/specs/2026-04-15-custom-data-design.md` into the CONTRIBUTING.md commit. Per D-05 these deletions are correct (`docs/superpowers/` is to be removed); however, plan 01-02's `<scope>` is the canonical owner of that deletion. The deletions are content-aligned with D-05 — only the commit-attribution is misaligned. Subsequent task commits used explicit file lists to avoid this; the SDK still defaults to staging the working-tree state of every file in the argv list, which is the correct behavior for new files.

## Threat Surface Compliance

All Phase 01-01 threat-register dispositions held:
- **T-01-01-01** (info disclosure in committed files): files contain no secrets; `grep -iE 'password|secret|api[_-]key|token'` over the diff showed no hits.
- **T-01-01-02** (vulnerability-report channel): SECURITY.md directs reporters to PVR; CoC contact is the public Issues URL (CoC channel only, not a security channel).
- **T-01-01-03** (force-push tampering): `protect-main` ruleset enforces `non_fast_forward` + `deletion` blocks on the default branch.
- **T-01-01-04** (PAT scope): out of plan scope (PAT lives in GitLab project settings); checkpoint Task 8 includes PAT-scope check.
- **T-01-01-05** (package.json license addition): single-key insertion (`"license": "Apache-2.0"`) into both webapp package.json files; diff is exactly +1 line per file.
- **T-01-01-06** (`gh` CLI audit trail): pre-edit state captured at `/tmp/repo-state-pre.json`, post-edit at `/tmp/repo-state-post.json`. GitHub records all settings changes in org audit log.
- **T-01-01-07** (branch-protection mis-config breaks mirror): plan deliberately omitted `pull_request_required` from the ruleset; mirror push will not be blocked. Live verification deferred to checkpoint.

## Coverage

| Requirement | Status | Verification |
|-------------|--------|--------------|
| MIR-01 (mirror SHA match) | **pending checkpoint** | `git ls-remote ...` after Task 8 GitLab UI Update-now |
| MIR-02 (tag propagation) | **pending checkpoint** | `git ls-remote --tags 'v*'` after Task 8 |
| MIR-03 (Issues/Discussions/Wiki/branch-protect) | **complete** | `gh repo view --json` + ruleset presence |
| MIR-04 (Apache 2.0 LICENSE) | **complete** | `head -5 LICENSE` |
| MIR-05 (CONTRIBUTING mirror flow) | **complete** | `grep "git ls-remote" CONTRIBUTING.md` |
| MIR-06 (CoC) | **complete** | `grep "Contributor Covenant" CODE_OF_CONDUCT.md` |
| MIR-07 (README mirror banner + docs link + 5-min block) | **complete** | `grep "read-only mirror" README.md`, `≤150 lines`, docs URL |

## Awaiting (Checkpoint Task 8)

Per plan task 8 (`type=checkpoint:human-action`), maintainer must verify the GitLab → GitHub push-mirror via the GitLab UI:

1. Open <https://gitlab.com/progresslab/progress-platform/-/settings/repository>
2. Expand **Mirroring repositories**
3. Confirm a single Push entry pointing at `https://github.com/ProgressLabIT/progress-platform.git`, with PAT auth carrying both `Repository contents: read & write` AND `Workflows: read & write` scopes (the latter is required by plan 01-03's `.github/workflows/*.yml`)
4. Click **Update now** (half-circle arrows icon)
5. After ~30 seconds, run from any terminal:

   ```bash
   GL_SHA=$(git ls-remote https://gitlab.com/progresslab/progress-platform DEV | awk '{print $1}')
   GH_SHA=$(git ls-remote https://github.com/ProgressLabIT/progress-platform DEV | awk '{print $1}')
   echo "GitLab: $GL_SHA"
   echo "GitHub: $GH_SHA"
   test "$GL_SHA" = "$GH_SHA" && echo "PASS: mirrored" || echo "FAIL: SHAs differ"
   ```

   Both must print the same SHA. Reply `mirror-verified <SHA>` on success, or describe deficiency (e.g., "PAT lacks workflow scope — regenerated and reconfigured").

## Self-Check: PASSED

- ✓ All 5 created files exist: `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `ARCHITECTURE.md`, `.github/PULL_REQUEST_TEMPLATE.md`
- ✓ All 4 modified files exist with expected content: `LICENSE`, `README.md`, `webapps/main/package.json`, `webapps/warehouse/package.json`
- ✓ All 7 commits present in `git log`: `febf6375`, `bbe48c96`, `4e5b660e`, `ba3a72c4`, `8425b512`, `74f6ccca`, `fa679217`
- ✓ Plan tasks 0–7 complete; task 8 awaiting human action (expected per plan)

---

*Generated 2026-04-29 by docs/01-01-PLAN.md execution.*
