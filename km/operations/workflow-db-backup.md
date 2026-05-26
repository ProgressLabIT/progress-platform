# Workflow DB Backup Strategy

Backup strategy for `progress_workflow-db` (Prefect metadata Postgres). Companion to [`workflow-db-recovery.md`](./workflow-db-recovery.md).

## Why backups matter here

Prefect's metadata DB carries:

- **Flow runs** — execution history, state transitions, logs (pointers), retries
- **Deployments** — registered flows + parameters + schedules
- **Work queues / pools** — runtime state
- **Variables, blocks, concurrency limits**

Without it, the platform's automation surface is blind: schedules don't fire, history disappears, UI shows nothing. The DB is also exposed to the failure mode documented in `workflow-db-recovery.md` (segfault mid-checkpoint → WAL chain break → `pg_resetwal` with seconds of data loss). A nightly logical dump turns that incident from "lossy emergency" into "30-second restore".

## Why `pg_dump`, not `pg_basebackup` or FS snapshots

| Approach | Fit for this DB | Notes |
|---|---|---|
| `pg_dump` (logical) | ✅ Best fit | Small output (Prefect DB is mostly indexes + history rows), portable across pg minor versions, restore is `psql < dump.sql`. Trivial to schedule. |
| `pg_basebackup` (physical) | ❌ Overkill | Requires WAL archive setup, identical pg version on restore, larger output. Designed for replicas / PITR, neither needed here. |
| FS snapshot (`tar` while running) | ❌ Unsafe | Catches files mid-write → exact failure mode this whole runbook exists to recover from. Only safe with `pg_start_backup()` / `pg_stop_backup()` ceremony, at which point `pg_basebackup` is the proper tool. |
| Volume snapshot (EBS / `cp -a` while stopped) | 🟡 Fallback | Fine as a forensic copy before a destructive operation (see recovery runbook), but not a backup strategy — requires DB downtime. |

**Decision: nightly `pg_dump` + 7-day local retention + offsite copy of latest.** Simple, sufficient.

## Proposed design

### Storage layout

A new bind-mounted volume `workflow_db_backup` at `/opt/progress/workflow_db_backup`, mirroring the pattern used by ArangoDB's `db_backup` (`deploy/compose/base.yaml`). Backups land here, retention is local; optional offsite sync from this dir.

```
/opt/progress/workflow_db_backup/
├── prefect-20260512-030000.sql.gz
├── prefect-20260513-030000.sql.gz
└── ... (7 most recent kept)
```

### Service definition (proposed addition to `deploy/compose/workflow.yaml`)

```yaml
volumes:
  workflow_db_backup:
    external: true   # created by single_node_setup.yaml

services:
  workflow-db-backup:
    image: postgres:15.2-alpine
    restart: always
    depends_on:
      - workflow-db
    networks:
      - progress
    environment:
      - PGHOST=workflow-db
      - PGUSER=postgres
      - PGPASSWORD=postgres
      - PGDATABASE=prefect
      - BACKUP_RETENTION_DAYS=7
    volumes:
      - workflow_db_backup:/backup
    entrypoint:
      - /bin/sh
      - -c
      - |
        echo "0 3 * * * /backup.sh >> /var/log/backup.log 2>&1" | crontab -
        cat > /backup.sh <<'EOF'
        #!/bin/sh
        set -eu
        TS=$(date +%Y%m%d-%H%M%S)
        OUT="/backup/prefect-${TS}.sql.gz"
        pg_dump --format=plain --no-owner --no-acl "$PGDATABASE" | gzip -6 > "$OUT.tmp"
        mv "$OUT.tmp" "$OUT"
        find /backup -name 'prefect-*.sql.gz' -mtime "+${BACKUP_RETENTION_DAYS}" -delete
        echo "[$(date -Iseconds)] backup ok: $OUT ($(du -h "$OUT" | cut -f1))"
        EOF
        chmod +x /backup.sh
        # Run once on container start so the first backup isn't 24h away
        /backup.sh || true
        crond -f -l 8
    deploy:
      replicas: 1
```

Notes:

- Same image as `workflow-db` → `pg_dump` is guaranteed wire-compatible, no separate dependency to track.
- Output is plain SQL gzipped — readable, diffable, restorable with `psql`. Custom format (`-Fc`) would be slightly smaller but adds `pg_restore` dependency on restore.
- Cron at 03:00 local. First backup runs at container start so a fresh deployment has a backup within seconds, not 24h later.
- Retention 7 days local. Adjust `BACKUP_RETENTION_DAYS` per customer.

### Volume creation

Add `workflow_db_backup` to the `volumes` list in `deploy/single_node_setup.yaml`:

```yaml
volumes:
  - db_data
  - db_backup
  - workflow_db
  - workflow_db_backup   # <-- new
  - workflow_config
  - flows
  ...
```

The existing loop creates `/opt/progress/workflow_db_backup/` and the matching Docker volume on first run.

### Offsite copy (optional, customer-dependent)

When the customer has S3 / network share / external backup target:

- **S3**: a sidecar `aws-cli` task or a cron on the host runs `aws s3 sync /opt/progress/workflow_db_backup/ s3://<bucket>/<host>/workflow_db/`.
- **SMB / NFS share**: bind a second host path into `workflow-db-backup` and copy.
- **rclone**: same idea, broader provider support.

Offsite cadence: same as the local cron, or every N hours. The local dump is the source of truth — offsite is just transport.

## Restore procedure

Restore from a logical dump is database-level, not data-dir level.

```bash
# 1. Confirm target DB is healthy enough to accept a connection
docker exec $(docker ps -qf name=progress_workflow-db) \
  psql -U postgres -d postgres -c "SELECT 1;"

# 2. Drop and recreate the prefect database
docker exec $(docker ps -qf name=progress_workflow-db) \
  psql -U postgres -d postgres -c "DROP DATABASE IF EXISTS prefect WITH (FORCE);"
docker exec $(docker ps -qf name=progress_workflow-db) \
  psql -U postgres -d postgres -c "CREATE DATABASE prefect;"

# 3. Pipe the dump back in
gunzip -c /opt/progress/workflow_db_backup/prefect-<ts>.sql.gz | \
  docker exec -i $(docker ps -qf name=progress_workflow-db) \
    psql -U postgres -d prefect

# 4. Restart wf-server so the connection pool resets cleanly
docker service update --force progress_wf-server
```

If `workflow-db` itself is broken (the runbook scenario):

1. Recover the DB cluster via `pg_resetwal -f` (see `workflow-db-recovery.md`) so it accepts connections.
2. Then restore the `prefect` database from the dump as above — replaces whatever state the reset left behind with the last consistent snapshot.

This is why local backups matter even with `pg_resetwal` available: the reset gets you a *running* DB, the dump gets you back the *data*.

## What's NOT backed up here

- **Flow code / deployments** — these live in the `flows` volume + `wf-system-worker` image and are re-registered on worker start. The DB has *references* to them, not the code.
- **Prefect server config** — `workflow_config` volume, separate.
- **Worker logs / artifacts** — stdout only, not in this DB.

So a complete "workflow tier" recovery is: restore `workflow_db` dump → re-deploy stack → workers re-register flows. The DB dump is the only stateful piece that can't be regenerated from code.

## Operational checks

After deployment, verify the cron is firing:

```bash
# Should show backups for each day, sorted oldest → newest
ls -la /opt/progress/workflow_db_backup/

# Should show "backup ok" lines every 24h
docker service logs progress_workflow-db-backup --tail 20
```

If the latest backup is older than 24h, investigate immediately — silent backup failure is the worst case.

## Open items

- [ ] Implement `workflow-db-backup` service in `deploy/compose/workflow.yaml`
- [ ] Add `workflow_db_backup` volume to `deploy/single_node_setup.yaml`
- [ ] Decide per-customer offsite target (S3 / SMB / none)
- [ ] Add backup-age alert (e.g. simple Prometheus textfile collector reporting age of newest file)
- [ ] Apply same pattern to ArangoDB main DB if not already in place (`db_backup` volume exists but cron status unclear)

## Related

- `deploy/compose/workflow.yaml` — service definitions
- `deploy/single_node_setup.yaml` — host setup / volume creation
- `km/operations/workflow-db-recovery.md` — recovery runbook this strategy mitigates
