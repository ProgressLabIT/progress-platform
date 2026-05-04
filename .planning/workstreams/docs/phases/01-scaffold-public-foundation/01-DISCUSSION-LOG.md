# Phase 1: Scaffold & Public Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-29
**Phase:** 01-scaffold-public-foundation
**Areas discussed:** License + OSS files scope, docs/ layout vs superpowers/, Skeleton page strategy, README + S5 coordination, GitHub org/URL canonical

---

## License + OSS files scope

### Sub-question 1: License choice

| Option | Description | Selected |
|--------|-------------|----------|
| Apache 2.0 (Recommended) | Pitfall 4.1 — explicit patent grant, B2B/enterprise-friendly, AGPL-bans-friendly. Replace existing MIT LICENSE. | ✓ |
| Keep MIT | Already in repo. Maximum permissiveness, no patent clause. Simpler but no enterprise patent grant. | |
| MPL 2.0 | File-level copyleft. Useful for reciprocity but heavier than MIT/Apache for B2B. | |

**User's choice:** Apache 2.0
**Notes:** Locked. Existing MIT `LICENSE` replaced; `license: Apache-2.0` added to docs `package.json`.

### Sub-question 2: OSS scaffold scope (initial)

| Option | Description | Selected |
|--------|-------------|----------|
| Full scaffold (initial recommendation) | SECURITY.md w/ 72h ack + supported-version table, PVR toggle, .github/ISSUE_TEMPLATE/, .github/PULL_REQUEST_TEMPLATE.md. | |
| Minimum: SECURITY.md only | Only SECURITY.md + PVR. Templates deferred. | |
| Punt entirely to Phase 4 | All security/template scaffolding in launch-prep. | |
| (User pushback) | "Isn't this a footgun for a one-man project?" — challenged the 72h ack SLA as undeliverable for solo maintainer. | ✓ |

**User's choice:** Pushback — refined below.

### Sub-question 2 refined: OSS scaffold for solo-maintainer reality

| Option | Description | Selected |
|--------|-------------|----------|
| PVR + minimal SECURITY.md (Recommended) | PVR toggle on. 10-line SECURITY.md, no SLA, no version table. PR template w/ closes-direct-PR notice. Skip issue templates. | ✓ |
| Just PVR toggle | Only PVR toggle. No SECURITY.md, no templates. | |
| Original full scaffold | Original recommendation as-is. | |

**User's choice:** PVR + minimal SECURITY.md
**Notes:** 72h ack reframed — agent agreed solo-maintainer SLA is a credibility footgun. Final scope: PVR toggle + ≤15-line SECURITY.md (no SLA, no version table) + `.github/PULL_REQUEST_TEMPLATE.md` (closes-direct-PR notice, automation not commitment) + no issue templates.

---

## docs/ layout vs superpowers/

| Option | Description | Selected |
|--------|-------------|----------|
| Move to .planning/archive/superpowers/ (Recommended) | Single git mv early in Phase 1; VitePress owns docs/ root. | |
| Move to km/superpowers/ | km/ is internal-knowledge area — but km/ is itself out-of-v1; mixing muddies its purpose. | |
| VitePress at docs/site/ | Lower-blast-radius file move but URL becomes /site/api/...; awkward path forever. | |
| VitePress srcExclude superpowers/ | Internal alongside public at directory level — mixed signal to GitHub repo browsers. | |
| (User override) | "just remove the directory. it's planning files for a shipped feature" | ✓ |

**User's choice:** Delete `docs/superpowers/` entirely.
**Notes:** Cleaner than relocation. Phase 1 starts with `git rm -r docs/superpowers/`.

---

## Skeleton page strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Section landings + 1 example each (Recommended) | 5 top-nav landings + 5 representative stubs. Proves URL contract, exercises lychee CI gate on real cross-link patterns. Phase 2/3 generators fill the rest. | ✓ |
| Full URL enumeration now | Complete URL list — every endpoint, every event, every CLI/user/admin page — even though L0 sweep + event auto-extract are Phase 2. Bleeds Phase 2 work into Phase 1. | |
| Top-nav landings only | Just 5 pages; sidebar shows 'Coming soon'. lychee can't validate any deep URLs in Phase 1. | |

**User's choice:** Section landings + 1 example each
**Notes:** Concrete stubs (`/api/production/jobs/start/`, `/events/production/job-started/`, `/cli/init/`, `/users/production/`, `/admins/deployment/`) chosen by Claude as representative anchors that match Phase 2/3 work.

---

## README + S5 coordination

### Sub-question 1: 5-min `progress init` block

| Option | Description | Selected |
|--------|-------------|----------|
| Placeholder + nightly S5 sync (Recommended) | Phase 1 ships full README structure; 5-min block as placeholder pinned to S5's current locked CLI surface; daily re-sync. Phase 4 final-locks. | ✓ |
| Wait for S5 lockdown | Phase 1 ships README without 5-min block (or with TODO). Re-open after S5 locks. | |
| Embed S5 README block via include | Sparkplug owns README-fragment file; main README @-includes it. Zero drift but extra build step + cross-workstream coupling. | |

**User's choice:** Placeholder + nightly S5 sync

### Sub-question 2: Demo GIF / asciinema

| Option | Description | Selected |
|--------|-------------|----------|
| Phase 4 launch-prep (Recommended) | Captured during S5's May 14 fresh-VM rehearsal. One pass, no churn. Phase 1 has placeholder image slot. | ✓ |
| Phase 1, re-record if S5 changes | Capture v0 now; re-record if S5 surface changes pre-launch. | |
| Skip entirely | No recording, just a UNS topology screenshot. Pitfall 4.5 most-regretted decision. | |

**User's choice:** Phase 4 launch-prep
**Notes:** Avoids re-record churn; rehearsal naturally captures the final version.

---

## GitHub org / Pages URL canonical

| Option | Description | Selected |
|--------|-------------|----------|
| ProgressLabIT (use existing) | Existing remote. Pages URL = progresslabit.github.io/progress-platform/. Update PROJECT.md / ROADMAP.md / REQUIREMENTS.md / STATE.md references. | ✓ |
| Create progresslab org, mirror to it | Match PROJECT.md as written. Requires GitHub org rename or new org + transfer. | |
| Custom subdomain | Pitfall 4.8 — explicitly out of v1. | |

**User's choice:** ProgressLabIT
**Notes:** Phase 1 includes a ref-correction sub-task: update `progresslab` → `ProgressLabIT` and `progresslab.github.io` → `progresslabit.github.io` in PROJECT.md, ROADMAP.md, REQUIREMENTS.md, STATE.md.

---

## Claude's Discretion

The following were not asked because they are research-level / pinning decisions; researcher resolves:

- GitHub Actions concurrency / cache strategy / package manager pin (npm vs pnpm vs yarn)
- VitePress version pin (latest 1.x with `vitepress-openapi` + `vitepress-plugin-mermaid` compatibility)
- `vitepress-plugin-mermaid` version pin (default + ELK renderer support, dark-mode flashbang fix)
- GitHub repo topics list (Pitfall 4.6 default; user can refine)
- Branch protection rule details (no force-push, no delete, status checks required — exact UI rule names per researcher)

Folded STATE.md todos into Phase 1 deliverables:

- `CONVENTIONS.md` authoring (todo #3) — folded as D-14
- `security@progresslab.it` alias (todo #5) — folded as D-02 (PVR replaces email channel; alias optional)
- License confirmation (todo #4) — resolved by D-01
- Mirror-update trigger documentation (PROJECT.md Phase 0 risk) — folded as D-15

---

## Deferred Ideas

(See `01-CONTEXT.md` `<deferred>` section for the full list — preserves: custom domain, Algolia DocSearch, versioned docs, `/v1/` prefix, PR preview deploys, issue templates, SECURITY SLA, sponsorship link, auto-sidebar plugin, Layout.vue override, embedded L2 docs.)
