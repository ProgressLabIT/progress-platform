# 0013 — Retire the perpetual GSD branch; features integrate worktree → DEV

**Status:** decided
**Date:** 2026-05-26
**Audience:** process / DX (cross-cutting — governs how all future work reaches the trunk)
**Related:**
- `CLAUDE.md` "Feature → DEV Integration" — rewritten this session (commit `d1c0fc3c` on DEV) to encode this decision
- [ADR-0011](0011-database-substrate.md) — precedent for numbering a platform-/process-level decision in continuation of the sparkplug-demo sequence

> **Cross-cutting note.** This ADR is numbered in continuation of the
> sparkplug-demo workstream because that's where active ADRs live, but the
> decision is **process-level** — it governs every future feature, not
> sparkplug. If a dedicated process/meta workstream is later created, this
> ADR should move there.

## Context

The branching model evolved through three regimes:

- **Regime A** (pre-2026-05-08): `branching_strategy: none`, no worktrees. All executor commits landed directly on a single long-lived `GSD` branch, squashed to `DEV`.
- **Regime B** (from 2026-05-08): per-milestone worktrees enabled (`branching_strategy: milestone`, `use_worktrees: true`).
- **Regime C** (current): features develop in their own worktree off `DEV`, each carrying its own GSD `.planning/` project (worktree-as-project).

A tree review on 2026-05-26 surfaced the relevant facts: `master` is a dead 2022 branch; `DEV` is the real trunk and the GitLab → GitHub mirror source; and `GSD` had accumulated 456 atomic commits as a single shared integration track. The question this ADR settles: under the worktree-per-feature model, is the perpetual `GSD` branch still needed?

## Decision

Retire `GSD` as the active integration target.

- `DEV` is the trunk and mirror source. `master` is ignored (dead).
- Each feature is developed in its own git worktree off `DEV`, carrying its own GSD `.planning/` project. Atomic WIP lives on the feature branch; ship-grained units are squashed onto `DEV`.
- Features spanning multiple parallel sessions merge into a short-lived `ms/<name>` parent branch, which is squashed to `DEV` and then retired.
- `GSD` is **kept as an archived ref** for the v1.0 sparkplug milestone's atomic history (review / bisect / undo). It is not deleted and is no longer an integration target.

Integration mechanics (also encoded in `CLAUDE.md`):

- Prefer a 3-way `git merge --squash <feature>` so DEV-side fixes are preserved, then `git reset` and commit by scope. Avoid `git checkout <feature> -- <paths>`, which silently reverts any file where DEV is ahead of the feature branch.
- Exclude `.planning/` from `DEV`. After a squash merge, `git checkout HEAD -- .planning` restores DEV's own planning state and drops the feature's.
- Read the true net delta with the two-dot diff (`git diff DEV <feature>`); the three-dot `DEV...<feature>` over-counts content DEV already shares via history.

## Alternatives Considered

- **Keep the perpetual `GSD` branch.** Rejected: a single shared integration track only made sense before worktree isolation. With per-feature worktrees, each feature branch already plays GSD's staging role (accumulate atomics → squash to DEV).
- **No parent branch ever — feature → DEV directly, always.** Fine for solo single-session features, but leaves no integration point when multiple parallel sessions collaborate on one feature. Hence the short-lived `ms/<name>` parent for that case only.

## Risks and Implications

- In-flight branches still based on an older `GSD`/pre-merge base (e.g. the `demo-seed` worktree) will need to rebase or merge `DEV`'s lead when resumed; the longer they wait, the larger that reconciliation.
- `GSD` must **not** be deleted — it is the only home of the v1.0 atomic history.
- Older sparkplug-demo `.planning` artifacts remain on `GSD`; `DEV` intentionally carries none.
- `GSD`'s own `CLAUDE.md` is now stale (the workflow rewrite landed on `DEV`); this is expected for an archived branch and is not synced back.
