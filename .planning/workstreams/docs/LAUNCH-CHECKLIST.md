# Launch Checklist — May 14/15, 2026

> **Internal only.** Not shipped to the public docs site.
> Run through this document during the May 14 dry-run (target: complete by 18:00 May 14).
> Re-run §1 Mirror Sync at 09:30 May 15 (30 min pre-webinar).

---

## §1  Mirror Sync (MIR-08)

> **Self-discipline policy (D-01/D-02/D-03):** No scripted SHA verification. No enforced freeze window. The mirror is one-way; a healthy mirror = SHAs match by definition.

- [ ] **Trigger manual mirror push** — GitLab → Repository → Mirroring → "Update now". Wait ~5 min.
- [ ] **Visual SHA spot-check** — `git ls-remote https://github.com/ProgressLabIT/progress-platform DEV` returns the same SHA as `git ls-remote https://gitlab.com/progresslab/progress-platform DEV`. (No script needed; a solo maintainer who knows when they last pushed can confirm visually.)
- [ ] **Propagation window** — After any content fix on May 14, wait ~10 min (mirror sync ~5 min + Pages deploy ~5 min) before relying on the result.
- [ ] **May 14 18:00 → May 15 11:00 — no-deploy window** — Do not merge to GitLab `DEV` during this window. If a fix is unavoidable, push it to a `post-launch` branch; do not break the freeze.

**Success criterion:** Both `git ls-remote` commands return the same 40-char SHA.

---

## §2  Dead-Link / Anchor Check (SITE-11, D-04)

> **Lychee reuse policy (D-04):** The Phase 1 lychee CI gate already crawls `dist/` on every PR (anchor-aware). The deployed GitHub Pages site IS the dist. If the last PR CI run was green going into May 14, the deployed site is link-clean. No separate live-URL crawl, no cron needed.

- [ ] **Confirm last PR CI was green** — check GitHub Actions for the most recent `deploy-docs.yml` run on `DEV`; the `lychee` step must show green.
- [ ] **Spot-check 3 cross-reference anchor links manually** — pick one API endpoint → "Emits:" → event page; one event page → "Triggered by:" → endpoint page; one `/admins/integrations/` → NATS subject anchor. All three must resolve.

**Success criterion:** Last CI run green; 3 manual spot-checks resolve correctly.

---

## §3  Cloud-VM Rehearsal (MIR-08, D-05/D-06/D-07)

> Validates "works on a stranger's box". Spin up a throwaway VM (Hetzner / Linode / DO — whichever is cheapest/fastest to spin up in your account). Scope = README "5-minute" block ONLY; do NOT exercise the full Sparkplug demo (that is S5's rehearsal).

- [ ] **Provision VM** — Ubuntu 24.04 LTS, 2 vCPU / 4 GB RAM minimum. Note provider + instance type below for teardown reference.
  - Provider/instance: `_______________`
- [ ] **Install prerequisites on VM** — Docker, Docker Compose v2, git. Verify: `docker --version`, `docker compose version`, `git --version`.
- [ ] **Clone public mirror** — `git clone https://github.com/ProgressLabIT/progress-platform.git && cd progress-platform`.
- [ ] **Start asciinema recording** — `asciinema rec docs/public/recordings/install.cast` (commit path per D-07). Record the entire session from this point.
- [ ] **Run README quickstart** — execute the commands exactly as shown in the README "Try it in 5 minutes" block.
- [ ] **Verify stack starts** — all containers report healthy / running.
- [ ] **Hit `/api/hello`** — `curl -s http://progress.localhost/api/hello` returns HTTP 200.
- [ ] **Stop asciinema recording** — Ctrl+D or `exit`.
- [ ] **Copy cast file off VM** — `scp` or `rsync` `docs/public/recordings/install.cast` to local machine.
- [ ] **Tear down VM** — terminate / delete the instance immediately after copying the cast file.

**Success criterion:** `/api/hello` returns 200; `install.cast` is on local machine and non-empty.

---

## §4  README "5-Minute" Block Re-Lock (D-08)

> Replace the Phase 1 placeholder block (currently tagged `# placeholder — coordinated with sparkplug-demo workstream`) with exactly what worked during the §3 rehearsal.

- [ ] **Compare rehearsed commands against README** — identify any differences between the placeholder commands and what actually worked on the VM.
- [ ] **Update README "Try it in 5 minutes" block** — replace the placeholder comment and command block with the validated commands from §3.
- [ ] **Replace demo image placeholder** — swap `https://via.placeholder.com/800x300?text=Demo+GIF+coming+soon` with the committed `install.cast` recording. Embed via standard markdown or VitePress `<asciinema-player>` per CONVENTIONS.md.
- [ ] **Commit and push to GitLab DEV** — commit message: `docs(readme): re-lock 5-min quickstart from May 14 rehearsal`. Wait for mirror + Pages deploy.
- [ ] **Verify README on GitHub mirror** — open `https://github.com/ProgressLabIT/progress-platform` and confirm updated commands and recording are visible.

**Success criterion:** GitHub mirror README shows rehearsed commands and embedded recording (no placeholder text or image).

---

## §5  openapi.json Verification (D-10)

> Phase 2 deferred openapi.json population due to WeasyPrint GTK blocker. Expected to land on the first DEV push via `scripts/export_openapi.py` in CI.

- [ ] **Check CI produced schema** — `jq '.paths | length' docs/public/openapi.json` (run against local clone after pulling latest DEV). Result must be `> 0`.
- [ ] **Vacuum lint passes** — check GitHub Actions `deploy-docs.yml` → "Lint OpenAPI schema (vacuum)" step is green on the most recent DEV run.
- [ ] **Spot-check OAOperation rendering** — open `https://progresslabit.github.io/progress-platform/api/` and confirm at least one endpoint renders with parameters, response schema, and examples (not a blank operation card).

**Success criterion:** `jq '.paths | length'` > 0; vacuum CI step green; one endpoint renders inline with content.

---

## §6  Docs-Site Smoke Checks (SITE-11, D-09)

Run these against `https://progresslabit.github.io/progress-platform/` on a real browser (not `localhost`).

- [ ] **Dark-mode Mermaid** — toggle dark mode; at least one sequence diagram page renders correctly without flashbang or blank diagram. Test against one of the top-10 event pages (e.g., `/events/production/job-started/`).
- [ ] **OAOperation rendering** — open one API endpoint page (e.g., `/api/production/jobs/start/`); confirm the `<OAOperation>` component renders with: description, request fields, response schema, at least one example, and an "Emits:" link.
- [ ] **Top-10 sequence diagrams** — visit all 10 hand-crafted event pages from the events index; confirm each renders a Mermaid diagram without browser console errors (open DevTools → Console, zero red errors).
- [ ] **Local search hits** — use the search box (Cmd+K or Ctrl+K) and verify hits are returned for each of: "create work order", "Sparkplug", "progress init". Each query must return at least one result.
- [ ] **Mobile-Safari rendering** — open the landing page on a real iPhone (or BrowserStack Safari/iOS) and confirm: top-nav is reachable (hamburger menu works), text is readable, no horizontal overflow.

**Success criterion:** All 5 checks pass. Document any failures below as `[FAIL] <description>` for post-launch backlog.

### Failures to log (fill in during run):

```
(none)
```

---

## §7  Final Go / No-Go (May 15, 09:30)

- [ ] §1 Mirror Sync re-run: SHA match confirmed.
- [ ] GitHub Pages returns HTTP 200 on `https://progresslabit.github.io/progress-platform/`.
- [ ] No-deploy window respected: no merges to GitLab `DEV` since May 14 18:00.
- [ ] Webinar demo endpoints (pick 3 "highlight" endpoints from Phase 2) all render with examples.

**Go decision:** All four boxes checked → webinar opens as planned.
**No-go decision:** One or more boxes unchecked → surface to webinar lead immediately; do not attempt a last-minute fix that breaks the freeze.

---

*Document created by plan executor. Owned by: workstream maintainer (Luca Sorgiacomo). Last updated: fill in after May 14 dry-run.*
