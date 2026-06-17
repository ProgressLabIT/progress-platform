# Decision Records

Project-level Architecture Decision Records for the Progress Platform. One global, monotonically-increasing sequence shared across all features and worktrees — this is the canonical ledger, code-tracked under `km/decisions/` on `DEV`, so every worktree inherits it at fork and it survives squash-to-DEV by default.

> **Provenance:** records 0001–0013 were migrated on 2026-06-03 from the retired `GSD` branch (`.planning/workstreams/sparkplug-demo/decisions/`), which is not an ancestor of `DEV`. The per-workstream numbering they were born under collided the moment a second worktree forked (two `0013`s); the global sequence here replaces it. Forensic history of the originals remains on the `GSD` branch.

Status pipeline:

| Status | Meaning |
|--------|---------|
| `discussion` | Captured but not yet locked. Trade-offs listed; awaiting decision. |
| `decided` | Decision made. Implementation may not yet have started. |
| `implemented` | Code lands and the decision is reflected in the codebase. |
| `superseded by NNNN` | A later decision replaced this one. |

Filename convention: `NNNN-kebab-title.md`. NNNN is zero-padded to 4 digits, assigned from the single global sequence below in order of creation — never reused, never per-workstream.

## Records

| ID | Title | Status | Created |
|----|-------|--------|---------|
| [0001](0001-demo-scope-cut.md) | Demo scope cut for industry 4.0 audience | decided | 2026-04-28 |
| [0002](0002-nats-subject-taxonomy.md) | NATS subject taxonomy for Sparkplug frames | decided | 2026-04-28 |
| [0003](0003-bindings-yaml-schema.md) | bindings.yaml schema for the slim MES wedge | superseded by 0010 | 2026-04-28 |
| [0004](0004-bridge-http-read-api.md) | UNS HTTP read API | superseded | 2026-04-28 |
| [0005](0005-timescale-schema-and-downsampling.md) | Timescale hypertable schema, downsampling, and Postgres consolidation | decided | 2026-04-28 |
| [0006](0006-progress-init-ux.md) | `progress init` Typer CLI UX (Docker Swarm port) | decided | 2026-04-28 |
| [0007](0007-simulator-scenario.md) | Simulator topology and demo scenario | decided | 2026-04-28 |
| [0008](0008-natsmqtt-subject-mapping.md) | NATS-MQTT subject mapping for Sparkplug | decided | 2026-04-28 |
| [0009](0009-stream-processing-framework.md) | Stream processing framework: custom Python for v1, Bytewax for v2 | decided | 2026-04-28 |
| [0010](0010-hardcoded-automation-for-v1-demo.md) | Hardcoded automation for v1 demo (supersedes 0003) | decided | 2026-04-28 |
| [0011](0011-database-substrate.md) | Database substrate: migrate from ArangoDB to PostgreSQL (cross-cutting / defense-readiness) | discussion | 2026-05-21 |
| [0012](0012-graph-query-substrate.md) | Graph queries stay in the database; in-memory rejected as primary substrate | discussion | 2026-05-21 |
| [0013](0013-retire-gsd-branch-worktree-to-dev.md) | Retire perpetual GSD branch; features integrate worktree → DEV (cross-cutting / process) | decided | 2026-05-26 |
| [0015](0015-device-consumer-identity-model.md) | Device & consumer identity model (unified registry, dual credentials) | discussion | 2026-06-17 |
| [0016](0016-reactive-event-automation-contract.md) | Reactive event/automation contract (device channels, subscriber-validated side effects) | discussion | 2026-06-17 |
| [0017](0017-physical-credentials-station-identity.md) | Physical credentials & station device identity (card-as-key, installed station builds) | discussion | 2026-06-17 |

### Reserved / incoming

- **0014** — UNS Data-Plane Contract (`progress.uns.*`). Lives on `feature/mill-twin` as `0014-uns-data-plane-contract.md` (renumbered from a colliding `0013`); its table row + link land here when that feature squashes to `DEV`. Not linked above until the file exists on `DEV` — no dangling links on the mirror.

## Conventions

- One decision per file. Trade-offs and rejected options live in the file, not in the index.
- The first lines of each file declare `Status:`, `Date:`, and (optionally) `Supersedes:` / `Superseded by:`.
- When a decision is locked, update the status here and in the file, in the same commit.
- Do not delete superseded files; mark them and leave them in place for history.
- New numbers come from this global sequence. A worktree that needs the next number takes the lowest free N; at the 2–3-worktree working cap, a same-N race is resolved by hand at squash time.
