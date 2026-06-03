---
title: progress restore
description: progress restore reference — Progress Platform.
cli_validated: false
---

# `progress restore`

> Restores ArangoDB content from a `db/backup/` archive against a running stack and seeds the media volume plus the `/opt/progress/config/.sparkplug-token` JWT used by the bridge service user. Wraps `arangorestore` inside the `progress_db` container — the same call the legacy `progress db restore` shell recipe makes — and adds the demo-bundle plumbing the Sparkplug demo needs.

> 🚧 Coming soon — `progress restore` is in active development; this page will be promoted to validated content when the underlying source lands.

## When to use it

- After `progress init` completes on a fresh VM, when the demo presenter wants to load the shipped demo bundle (work orders, phases, products, the `USR-SPARKPLUG-BRIDGE` user).
- When the Sparkplug demo S5 rehearsal needs a known-good DB state before the walkthrough segment.
- After a botched migration on a dev VM, to rewind to the last `latest` snapshot under `/opt/progress/db_backup/`.
- When CI primes a single-node Progress instance for an integration test run.

## Usage

```bash
progress restore <archive> [OPTIONS]
```

`<archive>` is a path to a directory under `/opt/progress/db_backup/` (or an absolute path on the host). The default `latest` symlink — created by the legacy `progress db backup` recipe — is the typical argument.

## Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--database` / `-d` | `TEXT` | `PROGRESS_PROD` | ArangoDB database name to restore into. Mirrors `arangorestore --server.database`. |
| `--snapshot` / `-s` | `TEXT` | `latest` | Snapshot directory name under `/opt/progress/db_backup/`. The `latest` alias points at the most recent dump. |
| `--include-media` / `--no-media` | `FLAG` | `--include-media` | Restore the `media/` payload bundled with the archive into the `media` Docker volume. `--no-media` skips for DB-only rewinds. |
| `--sparkplug-token` | `FLAG` | _(off)_ | Write the demo-bundled JWT to `/opt/progress/config/.sparkplug-token` for the `USR-SPARKPLUG-BRIDGE` user. Required for the Sparkplug demo segment. |
| `--yes` / `-y` | `FLAG` | _(off)_ | Skip the destructive-restore confirmation prompt. |
| `--help` | `FLAG` | _(off)_ | Show the help text and exit. |

Source: `cli/readme.md` §"Restore backup" (legacy recipe — locks `--database` / `--snapshot` defaults) + ADR-0001 §"What ships in v1 demo" (locks the `<archive>` positional and `--sparkplug-token` side effect). Once `cli/restore.py` ships, this table is regenerated from the Typer-decorated function signature and `cli_validated` flips to `true`.

## Example

Restore the demo bundle on a freshly initialized VM and seed the bridge JWT:

```bash
$ sudo progress restore /opt/progress/db_backup/demo-bundle --sparkplug-token --yes

  ▸ Locating archive                ✓ (/opt/progress/db_backup/demo-bundle)
  ▸ Verifying running stack         ✓ (progress_db container reachable)        # progress init must have run first
  ▸ Running arangorestore           ✓ (PROGRESS_PROD, 142 collections)         # docker exec into progress_db
  ▸ Restoring media payload         ✓ (87 files, 12 MB)                         # writes into the media Docker volume
  ▸ Writing .sparkplug-token        ✓ (/opt/progress/config/.sparkplug-token)   # bridge service-user JWT seed

  Restored from:    demo-bundle
  Database:         PROGRESS_PROD
  Bridge token:     /opt/progress/config/.sparkplug-token
```

Transcript shape grounded in `cli/readme.md` and ADR-0001; once `cli/restore.py` ships, this example is replaced with a captured live run.

## Related

- [Deployment basics](/admins/deployment) — the stack `progress restore` writes against
- [Operations](/admins/operations) — backup snapshots and recovery flow
- [progress init](/cli/init) — the prerequisite bootstrap step before restore
- [ADR-0001](https://github.com/ProgressLabIT/progress-platform/blob/DEV/km/decisions/0001-demo-scope-cut.md) — Source of truth for `progress restore` scope
