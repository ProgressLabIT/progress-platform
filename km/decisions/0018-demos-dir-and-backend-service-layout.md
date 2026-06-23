# 0018 — `demos/` for demo code; `backend/` for real services

**Status:** implemented
**Date:** 2026-06-23
**Audience:** structure / DX (cross-cutting — governs where demo code vs. shippable services live)
**Related:**
- `CLAUDE.md` Architecture / Conventions
- DEV commits `3d06db96` (layout + service split), `b262f0a7` (mill-twin harvest), `0b69eeb6` (ref fixes)
- [ADR-0007](0007-simulator-scenario.md) — the sparkplug simulator this moves to `demos/sparkplug_sim/`
- [ADR-0010](0010-hardcoded-automation-for-v1-demo.md) — the `THRESHOLD` contract the sim now inlines
- [ADR-0013](0013-retire-gsd-branch-worktree-to-dev.md) — worktree → DEV process under which this reorg landed

> **Cross-cutting note.** Numbered in continuation of the active ledger, but the
> decision is **structure-level** — it governs where every future demo artifact
> and every new service directory lives, not any one feature.

## Context

Demo code had accreted in three places: inside `backend/` (the Sparkplug simulator nested in `backend/sparkplug_bridge/simulator/`; demo seeders in `backend/scripts/`), under `deploy/scripts/` (the Streamlit reports app), and entirely unmerged on `feature/mill-twin` (the mill HMI `demo_twin/` + `mill_automation/`). `backend/` therefore mixed shippable services (`api`, `print-service`) with demo-only code and two dead 2021/2024 dirs (`mock/`, `lte/`).

Progress mirrors `DEV` to a public GitHub repo. A reader (or a new contributor) could not tell product from demo, and "where does this new report/simulator go?" had no consistent answer. The trigger was a worktree cleanup that had to land the mill-twin demo somewhere; rather than drop it back into `backend/`, we settled the layout.

## Decision

**`demos/` (repo root) holds demo-only CODE:**

| Path | Was |
|---|---|
| `demos/reports/` (Streamlit app + `pages/`) | `deploy/scripts/reports/` |
| `demos/sparkplug_sim/` | `backend/sparkplug_bridge/simulator/` |
| `demos/mill_twin/demo_twin/` (HMI) + `mill_automation/` | `feature/mill-twin` worktree (unmerged) |
| `demos/seed/` | `backend/scripts/seed_demo_positions.py` |

**`backend/` holds only real services**, each its own directory alongside `api`: `print_service` (renamed from `print-service` — underscore makes it an importable package and matches the `api` / `sparkplug_bridge` convention; the **published image / registry / DB-account name stays `print-service`** to avoid release-artifact churn), `sparkplug_bridge` (the real ingress service; the vendored `backend/sparkplug/` Tahu protobuf lib stays with it), `workflow`.

**Demo simulators are decoupled from the services they exercise.** `demos/sparkplug_sim/` carries its own copy of `heartbeat.py` and inlines `THRESHOLD = 100.0` (ADR-0010) rather than importing `sparkplug_bridge.*`. The bridge and the sim now share **zero imports in either direction** — a demo must never be a build/runtime dependency of a service, nor vice-versa.

**Orchestration stays in `deploy/`.** All compose and config — including demo stacks (`sparkplug.yaml`, `mill-twin.yaml`, `nats-ws.yaml`) and demo configs (`deploy/config/twinConfig.js`, `mill_automation.json`) — remain under `deploy/compose/` and `deploy/config/`. `demos/` is *what the demo is*; `deploy/` is *how it runs*. Build contexts/Dockerfiles point back into `demos/`.

Dead `backend/{mock,lte,reports-stub}` removed.

## Alternatives Considered

- **`backend/demos/` (nest under backend).** Rejected: demo code spans backend (sim, automation), frontend (static HMI), and a Streamlit app — repo-root `demos/` is the honest home for something that crosses all three layers.
- **Move the demo compose stacks into `demos/` too.** Rejected: that splits orchestration across two trees. `deploy/` stays the single home for *all* compose, product or demo; only build-context paths were repointed.
- **Leave the sparkplug simulator inside the bridge** (it shared a 74-line `heartbeat.py` + one constant). Rejected this session: the sim is demo, the bridge is a service; the duplication of one small module is cheaper than a cross-tree import and honors the service/demo boundary. The shared payload schema is locked by `server_event_manager`'s `subtopic` key, so contract drift is low-risk (and flagged in a `ponytail:` comment in both copies).
- **Keep `print-service` hyphenated.** Rejected for the directory (underscore = importable, consistent); kept for the published artifact name.

## Risks and Implications

- **In-flight worktrees based on the old layout need a rebase** onto reorganized DEV. `workspace/work-order-update-event` touched `sparkplug_bridge/simulator/` — expect conflicts there; `worktree-demo-seed` is lighter. Its unfinished seeding CLI is destined for `demos/seed/`.
- **`feature/mill-twin` is kept as an archived branch** (worktree removed, demo harvested). It still carries the reserved **[0014](index.md#reserved--incoming) UNS Data-Plane Contract** ADR and a handful of dropped shared-file tweaks (incl. a `nats-server.conf` delta). Do not delete the branch until 0014 lands on DEV and those tweaks are reconciled.
- **The sim's `heartbeat.py` is now a contract-synced copy, not a shared import.** If the heartbeat payload schema changes, both copies must change. Mitigated by the locked `subtopic` contract and a marker comment.
- **`demos/` is not on `backend`'s import path.** Each demo ships its own Dockerfile/entrypoint. `demos/sparkplug_sim/` still needs `backend/api/utils/` (platform `nats_client`) on `PYTHONPATH` — handled in its Dockerfile, which now builds from the repo root.
- `.planning/codebase/{STACK,STRUCTURE,INTEGRATIONS}.md` still reference old paths — regenerable via `/gsd-map-codebase`, not hand-patched.
