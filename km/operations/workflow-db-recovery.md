# Workflow DB Recovery Runbook

Recovery procedure for `progress_workflow-db` (the Prefect metadata Postgres) when it enters a crash-loop on startup.

> **Scope**: This DB stores Prefect's flow runs, schedules, deployments, work queues. It is **not** the main application DB (that's ArangoDB, with its own backup volume `db_backup`).

## Symptoms

The service crash-loops with logs of the form:

```
LOG:  database system was interrupted while in recovery at <time>
HINT: This probably means that some data is corrupted ...
LOG:  database system was not properly shut down; automatic recovery in progress
LOG:  redo is not required
PANIC: invalid magic number 0000 in log segment 000000010000000000000000, offset 0
LOG:  startup process (PID ..) was terminated by signal 6: Aborted
LOG:  database system is shut down
```

Each task ID in `docker service logs` is fresh (swarm re-spawning), so logs accumulate identical loop iterations.

## Architectural context

- The volume `workflow_db` is a **bind-mount** to `/opt/progress/workflow_db` (created by `deploy/single_node_setup.yaml`). The `/var/lib/docker/volumes/workflow_db/_data` path **only contains data while a container is mounting it** — when no container holds it, you see an empty stub directory. Always inspect the bind source `/opt/progress/workflow_db`, not the volume metadata path.
- The image is `postgres:15.2-alpine`, pinned in `deploy/compose/workflow.yaml`.
- Postgres data layout: `base/` (heap files), `pg_wal/` (write-ahead log segments), `global/pg_control` (cluster control file with checkpoint position).

## Failure mode

The PANIC happens because **the WAL chain is broken** — `global/pg_control` references a REDO segment that no longer exists in `pg_wal/`, OR `pg_control` itself was torn-written (zeroed REDO fields) and pg looks for a nonexistent segment `0/0`.

Most common triggers observed at customer sites:

1. **One-off backend segfault mid-checkpoint** (musl ld crash, single bit-flip, kernel/libc edge case). Confirmed by `dmesg` or `journalctl -k` showing `postgres[...]: segfault at ... in ld-musl-x86_64.so.1` at the checkpoint timestamp.
2. **Power-loss / hard kill** of the host during a checkpoint write before fsync. Look for unexpected reboots in `last reboot`.
3. **Disk full** during WAL allocation — pg pre-creates 16 MB segments with `fallocate`; if FS runs out of space, file exists but contents never flushed.
4. **Filesystem corruption** on the EBS volume (rare). Look for `ext4` / `xfs` / `i/o error` in `dmesg`.

If `dmesg` is clean and the host has stable uptime, cause is almost certainly (1) — a one-time fault, not a systemic issue. Recovery will hold.

## Diagnostic procedure

Run as `root` on the swarm host.

```bash
# 1. Confirm crash-loop pattern
docker service logs --tail 100 progress_workflow-db | grep -E '(PANIC|magic number|recovery)'

# 2. Inspect bind-mount source (NOT the _data stub)
ls -la /opt/progress/workflow_db/
ls -la /opt/progress/workflow_db/pg_wal/
sudo cat /opt/progress/workflow_db/PG_VERSION    # confirm pg version on disk

# 3. Read pg_control — REDO location tells you which WAL segment is needed
docker run --rm -v workflow_db:/var/lib/postgresql/data \
  --entrypoint pg_controldata postgres:15.2-alpine \
  /var/lib/postgresql/data

# 4. Check for host-side cause
dmesg -T | grep -iE '(ext4|xfs|nvme|i/o error|corrupt|oom|segfault.*postgres)' | tail -30
sudo journalctl -k --since "<crash timestamp> -1h" | grep -iE '(error|corrupt|oom|kill|segfault)' | tail -30
last reboot | head -5
uptime
df -h /opt/progress
```

Match the `Latest checkpoint's REDO WAL file` from step 3 against `pg_wal/` from step 2. If that segment is missing, pg cannot replay → recovery via `pg_resetwal` is required.

## Recovery — `pg_resetwal -f`

`pg_resetwal` rewrites `pg_control` and creates a fresh WAL segment past the last on-disk LSN. It does **not** modify data files. Use it when data files are consistent but the WAL chain is broken.

**Data-loss expectation**: any transaction committed in the seconds between the last on-disk checkpoint and the crash is lost. For Prefect, this is flow-run state updates from the final ~30s — acceptable.

```bash
# 1. Stop the service
docker service scale progress_workflow-db=0

# 2. SNAPSHOT THE DATA DIR — non-negotiable, even though resetwal is non-destructive
#    Use uncompressed copy (faster, polite to other services on the host)
sudo nice -n 19 ionice -c 3 cp -a /opt/progress/workflow_db \
  /opt/progress/workflow_db.backup.$(date +%Y%m%d-%H%M%S)
ls -la /opt/progress/workflow_db.backup.*/PG_VERSION   # verify backup

# 3. Remove any bogus zero-LSN WAL segment left by the failed startup
sudo rm -f /opt/progress/workflow_db/pg_wal/000000010000000000000000

# 4. DRY-RUN pg_resetwal — shows what it would change, no side effects
docker run --rm -v workflow_db:/var/lib/postgresql/data \
  --entrypoint /bin/sh postgres:15.2-alpine \
  -c "su-exec postgres pg_resetwal -n /var/lib/postgresql/data"

# Verify in the output:
#   - TimeLineID stays 1
#   - NextXID is preserved (>= the value from pg_controldata)
#   - NextOID is preserved
#   - "First log segment after reset" advances PAST the highest existing segment
# If anything looks off (e.g. NextXID drops, timeline changes), STOP and escalate.

# 5. Real run
docker run --rm -v workflow_db:/var/lib/postgresql/data \
  --entrypoint /bin/sh postgres:15.2-alpine \
  -c "su-exec postgres pg_resetwal -f /var/lib/postgresql/data"

# 6. Verify pg_control flipped to "shut down" state
docker run --rm -v workflow_db:/var/lib/postgresql/data \
  --entrypoint pg_controldata postgres:15.2-alpine \
  /var/lib/postgresql/data | grep -E '(cluster state|REDO location)'

# 7. Restart service
docker service scale progress_workflow-db=1
docker service logs -f progress_workflow-db
```

Healthy startup looks like:

```
LOG:  starting PostgreSQL 15.2 ...
LOG:  database system was shut down at <time>
LOG:  database system is ready to accept connections
```

No `PANIC`, no `recovery in progress`.

## Post-recovery sanity checks

```bash
CID=$(docker ps -qf name=progress_workflow-db)
docker exec $CID psql -U postgres -d prefect -c "SELECT count(*) FROM flow_run;"
docker exec $CID psql -U postgres -d prefect -c "SELECT count(*) FROM deployment;"
docker exec $CID psql -U postgres -d prefect -c "VACUUM ANALYZE;"
```

Then force-restart dependents so they reconnect cleanly:

```bash
docker service update --force progress_wf-server
docker service update --force progress_wf-system-worker
```

## Rollback (if recovery fails)

The backup at `/opt/progress/workflow_db.backup.<ts>/` is a perfect-fidelity copy. To revert:

```bash
docker service scale progress_workflow-db=0
sudo rm -rf /opt/progress/workflow_db
sudo mv /opt/progress/workflow_db.backup.<ts> /opt/progress/workflow_db
# Re-run diagnostic, escalate
```

## When NOT to use `pg_resetwal`

- If `pg_controldata` reports a sane checkpoint AND the referenced WAL segment **exists**, the failure is something else (data file corruption, FS issue). `pg_resetwal` won't help and may mask the real problem.
- If `dmesg` shows ongoing FS errors, **do not** start the DB on the same volume. Replace the underlying volume first.

## Prevention

See [`workflow-db-backup.md`](./workflow-db-backup.md). The fundamental mitigation is **logical backups** (`pg_dump`) on a schedule — they're tiny (the Prefect DB is mostly hot history) and turn this scenario from a recovery-with-data-loss event into a trivial restore.

## Related

- `deploy/compose/workflow.yaml` — service definition
- `deploy/single_node_setup.yaml` — host setup and volume creation
- Postgres docs: [pg_resetwal](https://www.postgresql.org/docs/15/app-pgresetwal.html)
