# 0001 — Demo Scope Cut for Industry 4.0 Audience

**Status:** decided
**Date:** 2026-04-28
**Revised:** 2026-04-28 (after the 0002–0007 contract pass: hardcoded automation per ADR-0010, UNS framing per ADR-0004, Postgres consolidation per ADR-0005, generic `tap` CLI, Bytewax post-demo per ADR-0009)
**Owner:** @luca
**Audience for the demo:** Industry 4.0 consultants and practitioners versed in UNS, ISA-95, and the ProveIT! community / demo style.

> **Addendum (2026-04-28, end of day):** the "Execution model — parallel sessions in git worktrees" subsection below is **superseded**. The team tried per-session git worktrees on `feature/*` branches, then dropped that approach within the same day in favor of GSD workstream sessions on the shared `GSD` branch (session-scoped workstream activation). The five-session scope partition (S1–S5) and the file-ownership map remain valid; only the "separate branch / separate worktree per session" mechanism changed. Authoritative execution model at the time: `git show GSD:.planning/workstreams/sparkplug-demo/PROJECT.md` § "Parallel Session Execution" (on the retired `GSD` branch). Current model: repo `CLAUDE.md` § "Branching & Integration".

## Context

A live demo of the Progress Platform is scheduled on **Friday May 15, 2026**, today is April 28. The audience is technically expert in industrial messaging patterns: Unified Namespace (UNS), ISA-95 hierarchy, Sparkplug B, and report-by-exception architectures. They will spot specification shortcuts and shallow integrations.

The demo is delivered as a **webinar / Zoom call to 5–10 viewers**, with the presenter creating a clean Linode Ubuntu LTS VM live during the call.

The existing Sparkplug demo workstream (`.planning/workstreams/sparkplug-demo/`) is sized as a production-skeleton: 7 phases, 47 requirements, including a binding engine with hot reload and a circuit breaker, ISA-18.2 alarms with deadband and dwell timers, a full topology UI with sparklines and bdSeq history, and demo polish on top. That scope is realistic for several weeks of focused work, not for a 17-calendar-day window that also has to cover bootstrap CLI, backup/restore, and a feature walkthrough.

The user wants four things from the demo:

1. A `progress init` command that brings up an empty Progress environment on a fresh Ubuntu LTS server.
2. A backup/restore command that populates that environment from a shipped demo dataset.
3. A walkthrough of the main MOM features (work orders, traceability, issues, notifications).
4. A Sparkplug B segment that goes beyond a generic viewer, showing a metric driving a Progress action.

## Decision

Cut the v1 demo scope to four sparkplug phases plus a hardcoded automation phase, drop the differentiation features (full binding engine, ISA-18.2 alarms, sparkline polish) to a post-demo roadmap, and add a Timescale-backed historian as the persistence story the audience expects. Execute via parallel AI sessions against contracts frozen by ADRs 0002, 0004, 0005, 0006, 0007, 0008, 0009, 0010. (Initial plan called for separate git worktrees per session — see Addendum above; superseded same-day by GSD workstream sessions on a single shared branch.)

### What ships in v1 demo

**Bootstrap and walkthrough (parallel, low risk).**

- `progress init` Typer CLI command (per ADR-0006), a Python+Typer port of `deploy/single_node_setup.yaml`. Both interactive prompts and declarative flags. Demo uses interactive on stage; default `--no-tls` for reliability with `--enable-tls` available if rehearsal proves it.
- `progress restore <archive>` CLI command, wraps `arangorestore` against the existing `db/backup/` archives and seeds media volume + the `/opt/progress/config/.sparkplug-token` JWT for the bridge service user.
- `progress tap <pattern>` CLI command — a generic `nats sub` wrapper with pretty-printing. Use against any subject; for Sparkplug raw frames the documented pattern is `'spBv1//0.>'` (per ADR-0008).
- Demo script for the main feature walkthrough — work orders, traceability, issues, notifications.

**Sparkplug pipeline (cut to four phases from the original seven).**

1. *Transport.* Enable the NATS MQTT 3.1.1 endpoint in `deploy/compose/`, JetStream with mounted volume, healthchecks. Spike the LWT, retained, and STATE primitives against a Sparkplug simulator. If any primitive fails, fall back to HiveMQ CE 2025.5 (compose change only).
2. *Bridge — decode and session state.* `backend/sparkplug_bridge/` using `aiomqtt` + vendored Eclipse Tahu protobuf. bdSeq state machine, alias map per `(edge_node, bdSeq)`, sequence number monotonicity, primary-host STATE handshake. JetStream KV for session state + last-values (per ADR-0002). Subjects, payload shape, and KV bucket names locked in ADR-0002.
3. *NATS publication and historian.* Bridge publishes decoded frames as JSON onto `progress.sparkplug.<group>.<edge>.<device?>.metric.<name>.{data,birth}` and notifications onto `progress.notification.sparkplug`. Timescale ingester (running against the consolidated Postgres-with-TimescaleDB instance, per ADR-0005) writes to a hypertable. Read endpoint `GET /api/uns/history?subject=...` exposes downsampled history per ADR-0004.
4. *UI lite.* `/app/uns` route (UNS-aligned, not Sparkplug-specific naming, per ADR-0004). Quasar `QTree` topology browser with online/offline indicator and live last-value. Single ECharts chart pulling from the Timescale endpoint over the last hour. No in-memory uPlot sparklines, no bdSeq history panel, no rebirth button, no threshold overlays.

**Hardcoded automation (Phase 5 wedge).** A single Python module `backend/sparkplug_bridge/automations/pump_anomaly.py` (~50–80 lines, per ADR-0010) detects `pump3.Vibration > 100 mm/s` for 5 continuous seconds and POSTs an `IssueCreatedEvent` to `/api/event` linked to `WO-DEMO-001` and `PH-DEMO-001`. No `bindings.yaml`, no engine, no UI panel, no GUI builder. Configurable knobs are in-code constants. The post-demo Bytewax-based engine (per ADR-0009) replaces this module with a YAML-driven configurable system.

The wedge demonstrates that Sparkplug data can drive Progress events end-to-end. The presenter has the option to open the (~75-line) Python file on stage during the wedge segment to reinforce "no magic, just code".

### What does NOT ship in v1 demo (deferred to post-demo roadmap)

- `bindings.yaml` schema and loader
- Generic binding engine, separate `backend/bindings/` service, hot reload, debounce, circuit breaker, source-cycle protection
- `BindingConfig.vue` read-only panel
- `SparkplugSignalEvent` wrapper class
- ISA-18.2 alarm state machine with deadband and dwell
- `SparkplugAlarmRaisedEvent`, threshold overlays, last-fired indicators
- Rebirth-request button
- bdSeq history UI panel
- 1000 msg/s load test gate
- `/debug/status` observability endpoint
- Machine-as-user resolution, auto-link-running-job chain
- Bytewax framework adoption (locked as the v2 path in ADR-0009)

These remain in `REQUIREMENTS.md` `## Post-Demo` and will move forward post-demo.

### What is added that was NOT in the original plan

- **Timescale historian.** ProveIT!-aligned audiences expect persisted, queryable history. In-memory sparklines that vanish on refresh would undercut the credibility of the rest of the demo. Schema and downsampling locked in ADR-0005. The historian runs on Prefect's existing Postgres instance (TimescaleDB extension on a new `progress_historian` database); no separate `historian_db` service.
- **ECharts** as the chart library (one chart in v1; the platform will use it elsewhere).
- **`progress tap`** generic CLI subcommand for live-tailing any NATS subject with pretty-printed JSON output.
- **`km/architecture/sparkplug.md`** intro doc covering the standard, our approach, and the system-integrator view (subject schema, REST endpoints, security model). Future-facing user-doc-shape, lives in KM for now.

### Stretch goal

Batch completion as a second wedge target if the rest of the work lands ahead of schedule. With ADR-0010's hardcoded shape, "batch_completed" is a separate Python module with its own constants — additive, no engine refactor. The cost is the simulator scenario producing a clean batch-completion trigger and ensuring `BatchCompletedEvent`'s preconditions are met by the restored DB.

### Execution model — parallel sessions in git worktrees ⚠️ superseded — see Addendum at top

> The text below is preserved as historical record. Current execution model: GSD workstream sessions on the shared `GSD` branch. The five-session scope partition still applies; only the per-session worktree/branch mechanism was dropped.

The work runs across five sessions in `.worktrees/` (per CLAUDE.md's Workstream Workflow section), each owning a non-overlapping file scope:

| Session | Branch | File ownership | Scope |
|---------|--------|----------------|-------|
| **S1** | `feature/sparkplug-bridge` | `backend/sparkplug_bridge/**`, `backend/sparkplug/**`, `deploy/compose/sparkplug.yaml`, `backend/api/endpoints/uns.py`, NATS-MQTT enable in `deploy/compose/base.yaml`, workflow-db image swap in `deploy/compose/workflow.yaml` | Sparkplug P1+P2+P3, Timescale ingester, FastAPI proxy/history endpoints, Postgres consolidation, hardcoded automation module |
| **S2** | `feature/sparkplug-ui` | `webapps/main/src/pages/uns/**`, `webapps/main/src/stores/uns.js`, `webapps/main/src/router/routes_uns.js`, `webapps/main/src/i18n/**` (UNS strings) | UNS topology browser + ECharts chart |
| **S3** | `feature/sparkplug-wedge` | Simulator scenario tuning, integration test for the automation fire path | Hardcoded automation tuning + sim integration |
| **S4** | `feature/cli-init-restore` | `cli/init.py`, `cli/restore.py`, `cli/tap.py`, `cli/main.py` (registration only) | `progress init`, `progress restore`, `progress tap` |
| **S5** | You | `db/backup/demo-bundle/**`, `docs/sparkplug-demo/**`, `km/architecture/sparkplug.md` (alongside Claude), walkthrough script and slides | Restored DB content, KM intro doc, demo script, Linode rehearsals |

**Shared files** (touched by exactly one session per day, daily integration):
- `cli/main.py` — registration only, S4-owned but coordinated when S5 ships extras.
- `deploy/compose/base.yaml` — NATS MQTT enable lives here; S1-owned single-touch.
- `deploy/compose/workflow.yaml` — Postgres image swap; S1-owned single-touch.
- `backend/api/utils/nats_client.py` — `SUBTOPIC_TO_SUBJECT` extension; S1-owned single-touch.

**Deviation protocol:** a session that hits a wall against the locked contracts stops and surfaces the deviation back to the orchestrator. The relevant ADR is updated (or superseded) before work resumes. No session unilaterally re-shapes a frozen contract.

## Trade-offs

**The cut version is a competent UNS/Sparkplug viewer with a working historian and a single hardcoded automation.** It is not a full MES integration suite. The hardcoded automation keeps the differentiation moment without absorbing the cost of a real binding engine; the audience sees a metric drive an Issue creation in the running Progress UI, and (optionally) sees the ~75 lines of Python that did it. This is more honest than shipping a half-baked YAML engine, which would invite unfavourable comparison to mature engines (Ignition, OAS) the audience already knows.

**Risk: live automation firing during the demo.** The 5-second dwell + 60-second latch in the automation suppress flapping; the simulator scenario (ADR-0007) is engineered to produce exactly one clean cross at t≈3:50. An emergency `make demo-stop-automations` sets `SPARKPLUG_AUTOMATIONS_ENABLED=false` on the bridge container and restarts it.

**Risk: NATS-MQTT spec coverage.** NATS 2.4+ MQTT 3.1.1 has been stable; Sparkplug-critical primitives (LWT for NDEATH, retained QoS 1 for STATE) are documented as supported but not validated by the Sparkplug community at the same depth as HiveMQ. Mitigation: the Phase 1 spike from the original plan is preserved as a hard gate; HiveMQ CE 2025.5 is a compose-only fallback. The dot-escaping behaviour on the NATS side is documented in ADR-0008.

**Risk: live Linode bootstrap on stage.** Image pulls during a webinar = potential dead air. Mitigation: structure the segment so `progress init` runs in background while the presenter narrates Progress architecture. Use `--no-tls` to skip Let's Encrypt provisioning. Three full rehearsals on fresh Linode hosts: May 5, May 10, May 13. A pre-staged Linode snapshot exists for emergency recovery during the live segment.

**Risk: timeline busts.** The Phase 5 simplification (hardcoded automation per ADR-0010) saves ~1 day vs the original slim-wedge plan. Plus the Postgres consolidation (ADR-0005) saves another half-day vs the original separate `historian_db` service. Updated estimate is ~12 working days serial; parallel sessions reduce wall-clock to ~9–10 days against the 11–12 working days available. Cut levers in priority order if needed:
1. Drop the ECharts chart (saves 1–1.5 days). Audience falls back to "see the topology, see history via terminal `progress tap` and `psql`."
2. Drop the hardcoded automation (saves 1 day). Demo loses the differentiation moment.
3. Drop the Timescale historian (saves 1 day). Use in-memory ring buffer instead.

Preferred order is 1 → 2 → 3, because losing the chart hurts presentation polish, losing the wedge hurts pitch differentiation, and losing the historian hurts technical credibility. The wedge is more valuable than the chart for this audience.

**Decision on OAM.** Out of scope for the demo. The Sparkplug bridge is an ingress adapter, not a mesh peer; OAM's contracts and discovery add no ergonomic value here. For terminal-side debugging, native `nats sub` (and the `progress tap` wrapper) are more credible to the audience than a custom OAM CLI. OAM may appear as a one-slide "what's next" tease in the deck.

## Verified during recon (2026-04-28)

- Progress already has a generic event API: `POST /api/event` with `Authorization: Bearer <jwt>` and a body containing `event_type` plus the event's `info` payload. The pattern is used routinely by Prefect flows (`backend/workflow/flows/flowcode/pause_offline_jobs.py`, `apply_inventory_counts.py`).
- Token model: JWT, `TokenContext.API`, scope-checked. Issued via `issue_token()` in `backend/api/utils/auth.py`. A "sparkplug-bridge" service user (`USR-SPARKPLUG-BRIDGE`) and an API token are seeded in the restored demo database (S5); the token is written to `/opt/progress/config/.sparkplug-token` (file mode 0600) per ADR-0010. No new auth code is needed.
- `IssueCreatedEvent.InfoModel` accepts `issue_data` with a `linked_to` list. The demo automation links to one work order (`WO-DEMO-001`) and one phase (`PH-DEMO-001`), both shipped in the restored DB.
- Progress's deployment uses Docker Swarm + `docker stack deploy` (`deploy/single_node_setup.yaml`), not `docker compose up`. ADR-0006 ports the playbook faithfully.

These findings remove the need for a new endpoint and the need for a new auth path.

## Locked answers (formerly open questions)

| Question | Answer |
|---|---|
| Demo deadline | Friday May 15, 2026 |
| Demo machine | Linode Ubuntu LTS VM, presenter-controlled, created live during the webinar |
| Audience size and format | Webinar / Zoom, 5–10 attendees |
| `progress init` UX | Both interactive prompts and flags via Typer; interactive used on stage (full spec: ADR-0006) |
| Demo Issue link target | Linked to one demo work order (`WO-DEMO-001`) and one phase (`PH-DEMO-001`); machine-as-user + auto-resolve chain deferred to v2 |
| Batch completion stretch goal | Yes, time permitting |
| TLS handling | Both `--enable-tls` and `--no-tls` supported; rehearsal-time decision on which the May 15 demo uses |
| Bindings/wedge shape | Hardcoded Python automation per ADR-0010; YAML engine deferred to v2 per ADR-0009 |
| Stream processing framework | Custom Python for v1; Bytewax for v2 (ADR-0009) |
| Postgres for historian | Consolidated with Prefect's existing instance per ADR-0005 (single TimescaleDB-flavoured Postgres serving two databases) |
| UI URL framing | UNS-aligned (`/app/uns`, `/api/uns/*`) per ADR-0004 |

## Updated timeline

Working days from April 28 (Tue) through May 13 (Wed), excluding May 1 (Italian Labor Day) and weekends: **11 working days for development**, plus May 14 dress rehearsal, demo May 15.

| Block | Days (serial) | Days (parallel wall-clock) |
|---|---|---|
| `progress init` CLI (ADR-0006) | 1.5 | overlapped with S1 |
| `progress restore` CLI | 0.5 | overlapped with S1 |
| `progress tap` CLI | 0.25 | overlapped |
| Sparkplug P1 (transport + sim stub) | 1 | 1 |
| Sparkplug P2 (decode + state) | 3 | 3 |
| Sparkplug P3 (NATS + Timescale on consolidated Postgres) | 1.5 | 1.5 |
| Sparkplug P4 (UI lite + chart) | 2.5 | overlapped with S1 P3 |
| Hardcoded automation (per ADR-0010) | 1 | overlapped with P4 |
| Demo data (service user, WO/phase, simulator scenario) | 1 | overlapped |
| KM Sparkplug intro doc | 0.5 | overlapped |
| Demo script + slides | 1 | overlapped |
| Linode rehearsals (×3) + dress run | 1.5 | sequential, end of timeline |
| Buffer | 1.25 | 1.25 |
| **Total serial** | **16.5** | — |
| **Total parallel wall-clock** | — | **~9–10** |

Parallel execution fits the available 11 working days with comfortable buffer.

## Status transitions

- `discussion` → `decided` (2026-04-28).
- `decided` → `implemented` once the workstream's `STATE.md` reflects scope alignment and Phase 1 has begun.

## Related

- `.planning/workstreams/sparkplug-demo/PROJECT.md` — original v1 scope (47 reqs, 7 phases). This decision narrows that scope for the demo only; the broader workstream remains the post-demo target.
- `.planning/workstreams/sparkplug-demo/ROADMAP.md` — to be rewritten to the four-phase + automation shape.
- `.planning/workstreams/sparkplug-demo/research/SUMMARY.md` — research basis for the technology choices preserved here. Note: its judgment on Bytewax-as-abandoned is superseded by ADR-0009.
- ADR-0002 — NATS subject taxonomy.
- ADR-0003 — superseded YAML schema; preserved as v2 starting point.
- ADR-0004 — UNS HTTP read API.
- ADR-0005 — Timescale schema and Postgres consolidation.
- ADR-0006 — `progress init` Typer CLI UX.
- ADR-0007 — simulator topology and scenario.
- ADR-0008 — NATS-MQTT subject mapping.
- ADR-0009 — stream processing framework (Bytewax for v2).
- ADR-0010 — hardcoded automation for v1 demo (supersedes 0003).
