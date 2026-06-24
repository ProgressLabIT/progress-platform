# Parallel-worktree / contract-visibility infra — shaping notes

> **Status: WORKING NOTES — options for review, nothing decided.** Not an ADR. Captures four
> candidate designs (A–D) and their skeptical evaluations from the 2026-06-03 workflow-infrastructure
> design discussion, plus a recommended hybrid. Do not treat anything here as locked until promoted
> to an ADR.

## Where this came from

The 2026-06-03 workflow-infrastructure design discussion, working from a verified current-state brief
of the dev workflow. The locked goals: run **2–3 feature worktrees in parallel** without colliding on
shared contract surfaces (NATS subjects, event-type registry, boundary schemas, API shapes, config
shapes); keep **DEV clean + ship-grained** (mirrored GitLab→GitHub); keep **per-worktree local testing**
easy (pytest+testcontainers already isolates — only the long-running compose dev stack collides);
optimise for **context-SWITCH / rehydration cost** because the maintainer is *actively in every worktree*
and architecture **emerges during** the work (contracts are NOT all frozen before forking); the ADR log
**doubles as brainstorming → shaping → decision/rejection record** (already practiced as `km/notes/*.md`
graduating to ADRs); a **soft "claim at the surface"** conflict-detection mechanism is endorsed; and the
solo-maintainer **no-overengineering** rule holds ("if this person stops typing, does the problem exist?").

**The central problem being fixed:** the contract ledger is split across three mutually-invisible homes
— the canonical 14-file ADR set is stranded on the retired `GSD` branch (not an ancestor of DEV), DEV
itself carries **zero** decision files yet `CLAUDE.md` points at them in three places, and `feature/mill-twin`
carries a *second, colliding* `0013` in code-tracked `km/decisions/`. Per-workstream numbering broke the
instant a second workstream forked. Four designs were proposed to fix it.

## Status & next actions (2026-06-10)

> Updated after executing the ledger migration. The **ledger-home decision (D's `km/decisions/`-on-DEV spine) is implemented**; the rest of the hybrid (claims, hooks, DEV-serial cap) is still shaping — see Recommendation + Open questions below.

**Shipped (on DEV):**
- `0feb077b` — ADR ledger consolidated into `km/decisions/` on DEV: 13 ADRs (0001–0013) + global-sequence `index.md` rescued off the retired `GSD` branch, statuses preserved, 0014 reserved/unlinked. Same commit also carries the **CLAUDE.md workflow-section cleanup** (merged "Parallel Worktree Convention" + "Feature → DEV Integration" → one "Branching & Integration"; reframed "Decision Records" to the `km/decisions/` home; fixed `/gsd:` → `/gsd-` skill names) plus the 3 repointed pointers. *(Commit message under-describes — the CLAUDE.md diff is the whole cleanup, not just pointers.)*
- `bdfbf847` — repointed ~34 stale `.planning/workstreams/sparkplug-demo/decisions/` refs across 13 files → `km/decisions/`; un-404'd 6 public GitHub blob URLs; dropped the masking `lychee.toml` exclude.

**Done, not yet on DEV:**
- `feature/mill-twin` `da4602e3` — UNS contract renumbered `0013 → 0014` (+ self-refs/paths). Lives only on the worktree branch.

**Current state:**
- DEV head `a24581da`; both migration commits intact. `km/decisions/` on DEV = 14 files (0001–0013 + index).
- `feature/mill-twin` has diverged: **120 ahead / 6 behind DEV** — it has NOT pulled the migration, so its `0014` refs to `km/decisions/0002`,`0005` dangle *within the worktree* until it integrates DEV. Expected; resolved by the gate below.
- `km/notes/` (this note + `nats-cep-library`, `shared-webapp-composables`) is **untracked** — never committed. Consistent with prior practice; committing is an open decision (▢ below).
- DEV push is yours to drive; the formerly-masked ADR links resolve on the mirror only after a push that includes `km/decisions/`.

**To-do — the gate, in order:**
- ▢ **Integrate mill-twin → DEV.** First merge/rebase DEV *into* mill-twin (brings `km/decisions/0001–0013` so 0014's refs resolve), then squash mill-twin → DEV. On that squash, add the **0014 row + link** to `km/decisions/index.md` (currently reserved/unlinked). Verify zero dangling links before pushing.
- ▢ **Push DEV** → mirror; confirm lychee is green now that the ADR-link exclude is gone.

**To-do — ratify + build the rest of the hybrid (still shaping):**
- ▢ Graduate this note to ADR(s) — likely `0015` (or a small set: ledger-home / claim-mechanism / hook-policy). Ledger-home is retroactive (already implemented).
- ▢ Build the 3 hooks (none exist; no `.claude/hooks/` dir yet), matching the graphify inline-`command`/fail-open style: SessionStart rehydration digest (**must read DEV-live `git show DEV:km/decisions/...` + walk `../<sibling>/`**, never the fork-frozen copy); surface-claim warn (advisory); no-`Co-Authored-By` guard (start warn → block).
- ▢ Lock the `surfaces:` closed vocab; decide pre-stage `would-surface:` = **hook nudge on first contract-surface touch** (preferred refinement) vs mandatory discipline.
- ▢ `km/README.md`: add `km/notes/` + `km/decisions/` genre entries + a notes `_template.md` (km/README already has an unrelated pending edit — fold in).
- ▢ Decide whether to commit `km/notes/` to DEV (visibility) or keep local.
- ▢ Remaining design open questions: claim granularity, global-numbering race, compose `COMPOSE_PROJECT_NAME` + port-offset, `workspace/*`→`feature/*` + skill-name drift (see Open questions to shape next).

## The four options (one line each)

- **A — Extend current:** keep `km/notes/` shaping → promote to ADRs in a code-tracked **on-DEV `km/decisions/` ledger**; the claim *is* a YAML `surfaces:` frontmatter on each contract ADR; collisions detected by a ~30-line query over `surfaces:` across worktrees + DEV; 3 hooks (surface-warn, rehydration digest, no-coauthor block).
- **B — GSD-native:** a permanent `.planning/workstreams/contracts/` workstream is the ledger + `CLAIMS.md` registry, reusing `gsd-thread`/`gsd-plant-seed`/`gsd-sdk`; cross-worktree visibility via a shared-branch mount of `feature/contracts`.
- **C — Dedicated branch:** a long-lived (orphan) `contracts` branch is the single home for ADRs/notes/claims/surfaces; every worktree + DEV `merge --no-ff contracts` (read-mostly) to see it; edit-on-contracts-merge-down only.
- **D — Minimal / attention-bounded:** **DEV-serial by default**, cap at 2–3 short-lived worktrees; move the ADR ledger to code-tracked `km/decisions/` on DEV with **one global monotonic sequence**; add nothing enforced except an optional co-author warn hook + a read-only SessionStart digest; `CLAIMS.md` is a hand-edited table.

## Comparison matrix (score 1–5, one word)

| Criterion | A | B | C | D |
|---|---|---|---|---|
| Parallel, no collision | 3 reactive | 3 unsound-mount | 4 strong-but-stale | 3 numbering-only |
| Clean DEV | 4 decoupled | 2 squash-fragile | 3 merge-markers | **5 untouched** |
| Easy local test | 4 scoped | 4 stamped | 4 over-governed | **5 minimal** |
| Human-in-loop / rehydration | 4 digest | 3 shared-write-race | 2 branch-hop-tax | 4 digest |
| Notes/ADR fit | **5 faithful** | 2 wiki-regression | 4 location-only | **5 faithful** |
| Solo fit / no-overeng | 4 three-hooks | 2 most-machinery | 2 standing-discipline | **5 textbook** |
| Migration cost | 3 careful | 2 blocked-mount | 2 orphan-merge | 3 careful |

## Per-option summary

**A — Extend current.** Lowest-new-surface-area fix: reuses the existing notes→ADR practice, relocates
the broken `.planning/` ADR home to code-tracked `km/decisions/`, and makes the *claim* just a `surfaces:`
frontmatter list (closed vocab keyed to the 5 surfaces) queried across worktrees. *Key tradeoff:* the
contract-ADR commit is decoupled from the feature squash (visible to siblings early) at the cost of one
manual git step per frozen contract, with no enforcement it lands ahead of code. *Adversarial break:* the
`surfaces:` claim is **collision-DETECTION, not edit-time PREVENTION** — two worktrees concurrently
greenfield-shaping the same surface (`backend/api/events/*`) have *no* claim written yet, so both warn hooks
see "all clear" and the overlap is only found at the next sync/merge. Verdict: **ACCEPT WITH ONE FIX** —
make the `would-surface:` note pre-stage a *mandatory* step before first touching a contract surface.

**B — GSD-native.** Correct ledger-consolidation intent (global numbering kills the 0013 collision) and a
good compose-stamp local-test fix, but the load-bearing cross-worktree mount is **mechanically impossible**:
`git worktree add` refuses a second checkout of `feature/contracts` ("already checked out", confirmed), and
the symlink fallback collapses worktree isolation into one shared working tree with write races. Putting the
ledger under `.planning/` *re-creates* the exact squash-strand bug via a never-miss extra `git checkout`
recipe line, and moving shaping off `km/` kills the GitLab-Wiki publish path. *Adversarial break:* the mount
never materialises; the symlink fallback races; a forgotten recipe line silently re-strands an ADR on the
mirror. Verdict: **REJECT as primary; harvest the ideas onto a `km/` home.**

**C — Dedicated branch.** The single global ADR namespace is the strongest structural cure (kills 0013,
resolves mill-twin's dangling `0002`/`0005` refs once they physically exist in every merged tree), and
files-as-truth needs zero bespoke storage. But the **merge-down-only edit-direction invariant fights goal 4
head-on**: the right move at the moment of insight becomes a branch-context hop — the most expensive action
exactly when iteration should be cheapest — and there's *no* hook for that invariant. The orphan root makes
every DEV merge an `--allow-unrelated-histories` graft (ugly on the mirror). *Adversarial break:* under
iteration pressure the maintainer edits the merged-in `contracts/` files *in the worktree* (forbidden,
un-detected), silently re-forking the ledger. Verdict: **CONDITIONAL — adopt the namespace, drop the branch**
(home it in code-tracked `km/`).

**D — Minimal / attention-bounded.** Treats the one-human attention cap as the real bottleneck: DEV-serial by
default, `km/decisions/` on DEV with one global sequence (kills 0013 structurally), and *deliberately omits*
all enforcement except the justified co-author warn — recorded as an intentional non-decision. Best fit for
clean-DEV, notes/ADR fit, solo-fit, local-test. *Key tradeoff:* loosens the contract gate from "frozen before
fork" to "decided lands mid-worktree then squash" and leans on a SessionStart digest + hand-edited `CLAIMS.md`
to backfill safety. *Adversarial break:* a git-worktree staleness bug — the digest as specified reads the
worktree's **own fork-frozen** copy of `CLAIMS.md`, so a sibling's *post-fork* claim is invisible at exactly the
context-switch moment it matters. Verdict: **ACCEPT WITH ONE REQUIRED FIX** — the digest must read DEV-live
(`git show DEV:km/decisions/CLAIMS.md`) and/or walk co-located `../<sibling>/` worktree paths.

## Recommendation — D as the spine, with A's faithful notes/claims layer (hybrid)

Adopt **D's topology** — `km/decisions/` on DEV, one global monotonic ADR sequence, DEV-serial-by-default with
a hard 2–3 worktree cap, minimal enforcement — as the base. It is the only option that scores 5 on clean-DEV,
solo-fit, notes/ADR-fit, and local-test simultaneously, and it is the one design every evaluator agreed is the
right *shape* for this maintainer. **Both B and C, when their flaws are stripped, collapse onto exactly this
home** (code-tracked `km/`, inherited by every worktree at fork, surviving squash by default — mill-twin's
already-correct instinct). That convergence is the strongest signal in the set.

Layer in from **A**: (1) the `surfaces:` / `would-surface:` **closed vocabulary** unifying notes → ADR → hook
into one taxonomy; (2) **A's required fix made mandatory** — write a `km/notes/` note with its `would-surface:`
line committed *before* first touching a contract surface in a new worktree, so the warn hook has something to
query during the greenfield window (this is what upgrades the claim from after-the-fact detection toward
prevention); (3) **D's required fix** — the SessionStart digest reads **DEV-live** `CLAIMS.md` and walks
`../<sibling>/` paths, never the stale fork-frozen copy.

**Three hooks total**, matching the existing graphify inline-`type:command`/`additionalContext`/fail-open style:
- **SessionStart rehydration digest** (warn, fail-open) — branch + regime, last N `index.md` entries, DEV-live sibling claims, nearby WORKING notes. Directly attacks goal 4.
- **surface-claim warn** (warn, fail-open) — on editing a contract-surface path, surface any sibling claim. Advisory only (goal 6).
- **no-coauthor** — the **one** invariant worth deterministic enforcement: the harness Bash guidance *injects* a `Co-Authored-By: Claude` trailer the project + global rules forbid; it passes "if the human stops typing, does the problem exist?" = YES. (Start as warn; promote to block if a trailer ever reaches mirror-facing DEV.)

*Justification against the goals:* clean DEV (km/ survives squash by default, zero recipe edits, no merge
markers — beats B and C); goal 4 (DEV-serial + digest minimise switch cost; no edit-direction tax of C, no
shared-write-race of B); goal 5 (km/notes preserved verbatim, Wiki publish intact — A and D both score 5,
B regresses it); goal 6 (soft claim, human is the sync, fits the 2–3 cap); goal 7 (one global sequence + a
hand-edited table + three fail-open hooks is the minimum that fixes the verified problem — D's omitted-hooks
non-decision is textbook). *Migration cost* is the shared tax of every option (hand-extract + renumber the 14
stranded ADRs, reconcile mill-twin's dangling `0002`/`0005` into the global space) — a careful afternoon, not
a one-command adoption; gate it: land the rescue + global numbering on DEV **before** merging mill-twin, or the
dangling links ship to the public mirror.

## Open questions to shape next

- **Claim granularity:** is the closed surface vocab (`nats-subjects`, `event-registry`, `boundary-schema:<name>`,
  `api:<path>`, `config:<file>`) the right resolution, or does `event-registry` need sub-path globs to avoid
  false collisions across two unrelated event families?
- **Mandatory pre-stage vs friction:** does requiring a committed `would-surface:` note before first contract-surface
  edit actually get followed under iteration pressure, or does it become ceremony the maintainer routes around?
  (This is the load-bearing assumption of the hybrid's collision-*prevention* claim.)
- **Digest read path:** confirm the SessionStart hook can cheaply `git show DEV:km/decisions/CLAIMS.md` from inside a
  worktree AND enumerate `../<sibling>/` — and what it does when DEV is itself mid-rebase.
- **Global numbering race:** two worktrees forked off the same DEV tip can both grab the next free N before either
  squashes. Accept as a soft race the human resolves at squash (fine at 2–3), or allocate from a single DEV-side
  counter at create time?
- **Compose dev-stack collision:** `COMPOSE_PROJECT_NAME=progress-<worktree>` + a derived port offset block per
  worktree `.env` — settle the offset-allocation scheme (so two worktrees don't pick colliding bases) and whether
  it's worth a warn hook backstop.
- **mill-twin migration ordering:** lock the exact sequence (rescue 14 files + global index on DEV → renumber
  mill-twin 0013→next + repoint its cross-refs → only then merge its feature) so no dangling link reaches the mirror.
- **Branch-name + skill-name drift:** rename `workspace/work-order-update-event` → `feature/*`, override
  `gsd-new-workspace`'s `workspace/` + `~/gsd-workspaces/` defaults, and pick the dash-form `/gsd-quick` skill names
  (prune colon-form) — bundle into the same CLAUDE.md pass that repoints the dangling sparkplug-demo pointers.
- **Graduation trigger for THIS note:** when does this note graduate to an ADR (the workflow-infra decision itself),
  and does the hybrid warrant one ADR or a small set (ledger home / claim mechanism / hook policy)?

## Pointers

- Current-state brief: 2026-06-03 workflow-infrastructure design discussion (this session)
- Stranded canonical ADR set: `git show GSD:.planning/workstreams/sparkplug-demo/decisions/0001..0013` + `index.md`
- Code-tracked contract pattern (the right instinct): `.worktrees/mill-twin/km/decisions/0013-uns-data-plane-contract.md`,
  `.worktrees/mill-twin/km/contracts/uns-envelope.schema.json`, test `testing/pytest/tests/unit/mill_twin/test_uns_envelope_contract.py`
- Dangling pointers to fix: `CLAUDE.md` lines ~9, ~59, ~76–78
- Notes-genre gap: `km/README.md` (omits `km/notes/` entirely) — add a `_template.md` + a `### Shaping Notes` entry
- Existing hook style to match: `.claude/settings.json` (lone `PreToolUse:Bash` graphify hook); **no `.claude/hooks/` dir yet**
- Compose collision: memory `feedback_compose_project_name_worktree`
