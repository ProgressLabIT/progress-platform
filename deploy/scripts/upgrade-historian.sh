#!/usr/bin/env bash
# Upgrade demo server's workflow-db to TimescaleDB and bootstrap the
# progress_historian database. Idempotent — safe to re-run.
#
# Run on the demo server (root or docker-group user). Assumes Docker Swarm
# stack named "progress" per deploy/scripts/service-update.
#
# Steps:
#   1. Detect current workflow-db image + PG major version.
#   2. pg_dumpall backup (always — insurance).
#   3. If image != timescale/timescaledb:latest-pg15:
#        - Same PG major as target → image swap (in-place upgrade, fast).
#        - Different PG major     → dump/restore path (slow, asks confirm).
#   4. CREATE DATABASE progress_historian + CREATE EXTENSION timescaledb.
#   5. Apply hypertable + indexes + continuous aggregates + retention policy.
#   6. Print next step (start historian_ingester).
#
# Rollback: `pg_restore` the dump captured in step 2 into a freshly recreated
# volume after reverting the image tag on the service.

set -euo pipefail

# ----- Config ----------------------------------------------------------------
TARGET_IMAGE="timescale/timescaledb:latest-pg15"
TARGET_PG_MAJOR=15
STACK_NAME="${STACK_NAME:-progress}"
SERVICE_NAME="${STACK_NAME}_workflow-db"
NETWORK_NAME="${NETWORK_NAME:-progress}"
BACKUP_DIR="${BACKUP_DIR:-/opt/progress/backups}"
HISTORIAN_DB="${HISTORIAN_DB:-progress_historian}"
PG_USER="${PG_USER:-postgres}"
PG_PASS="${PG_PASS:-postgres}"

TS=$(date -u +%Y%m%dT%H%M%SZ)
BACKUP_FILE="${BACKUP_DIR}/workflow-db-${TS}.sql.gz"

log()  { printf '\033[1;34m[%s]\033[0m %s\n' "$(date -u +%H:%M:%SZ)" "$*"; }
warn() { printf '\033[1;33m[WARN]\033[0m %s\n' "$*" >&2; }
fail() { printf '\033[1;31m[FAIL]\033[0m %s\n' "$*" >&2; exit 1; }
ask()  { read -rp "$1 [y/N]: " a; [[ "${a:-N}" =~ ^[Yy]$ ]]; }

# ----- 0. Sanity -------------------------------------------------------------
command -v docker >/dev/null || fail "docker not on PATH"
docker info >/dev/null 2>&1 || fail "docker daemon unreachable"
docker service inspect "${SERVICE_NAME}" >/dev/null 2>&1 \
  || fail "service ${SERVICE_NAME} not found — adjust STACK_NAME env"

mkdir -p "${BACKUP_DIR}"

CURRENT_IMAGE=$(docker service inspect --format '{{.Spec.TaskTemplate.ContainerSpec.Image}}' "${SERVICE_NAME}")
log "current image: ${CURRENT_IMAGE}"
log "target image:  ${TARGET_IMAGE}"

# Find the running container so we can pg_dumpall / psql against it.
CONTAINER_ID=$(docker ps --filter "label=com.docker.swarm.service.name=${SERVICE_NAME}" \
  --format '{{.ID}}' | head -1)
[[ -n "${CONTAINER_ID}" ]] || fail "no running task for ${SERVICE_NAME}"

CURRENT_PG_MAJOR=$(docker exec "${CONTAINER_ID}" psql -U "${PG_USER}" -d postgres -tAc \
  "SELECT current_setting('server_version_num')::int / 10000")
log "current PG major: ${CURRENT_PG_MAJOR}"

# ----- 1. Backup ------------------------------------------------------------
log "pg_dumpall → ${BACKUP_FILE}"
docker exec -e PGPASSWORD="${PG_PASS}" "${CONTAINER_ID}" \
  pg_dumpall -U "${PG_USER}" --clean --if-exists \
  | gzip > "${BACKUP_FILE}"
SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
log "backup ok (${SIZE})"

# ----- 2. Decide migration path ----------------------------------------------
NEEDS_IMAGE_SWAP=true
[[ "${CURRENT_IMAGE}" == "${TARGET_IMAGE}" ]] && NEEDS_IMAGE_SWAP=false

if ${NEEDS_IMAGE_SWAP}; then
  if [[ "${CURRENT_PG_MAJOR}" == "${TARGET_PG_MAJOR}" ]]; then
    log "in-place image swap (same PG major) — safe"
    PATH_CHOICE=in_place
  else
    warn "PG major mismatch: ${CURRENT_PG_MAJOR} → ${TARGET_PG_MAJOR}"
    warn "in-place start will FAIL — Postgres refuses cross-major data dirs"
    warn "the dump/restore path will recreate the volume from ${BACKUP_FILE}"
    ask "proceed with dump/restore migration?" || fail "aborted by user"
    PATH_CHOICE=dump_restore
  fi
else
  log "image already on target — skipping swap"
  PATH_CHOICE=none
fi

# ----- 3. Image swap ---------------------------------------------------------
swap_image_in_place() {
  log "docker service update --image ${TARGET_IMAGE} ${SERVICE_NAME}"
  docker service update --force --image "${TARGET_IMAGE}" "${SERVICE_NAME}"
}

swap_image_with_volume_wipe() {
  log "scaling ${SERVICE_NAME} to 0 (releases volume)"
  docker service scale "${SERVICE_NAME}=0"
  sleep 5

  VOLUME_NAME=$(docker service inspect --format \
    '{{range .Spec.TaskTemplate.ContainerSpec.Mounts}}{{if eq .Target "/var/lib/postgresql/data"}}{{.Source}}{{end}}{{end}}' \
    "${SERVICE_NAME}")
  [[ -n "${VOLUME_NAME}" ]] || fail "could not resolve PGDATA volume name"
  log "wiping volume ${VOLUME_NAME}"
  docker run --rm -v "${VOLUME_NAME}:/data" alpine sh -c 'rm -rf /data/* /data/.[!.]* 2>/dev/null || true'

  log "service update → ${TARGET_IMAGE} + scale back to 1"
  docker service update --force --image "${TARGET_IMAGE}" "${SERVICE_NAME}"
  docker service scale "${SERVICE_NAME}=1"
}

case "${PATH_CHOICE}" in
  in_place)     swap_image_in_place ;;
  dump_restore) swap_image_with_volume_wipe ;;
  none)         : ;;
esac

# ----- 4. Wait for workflow-db healthy --------------------------------------
log "waiting for workflow-db to be ready"
for i in $(seq 1 60); do
  CONTAINER_ID=$(docker ps --filter "label=com.docker.swarm.service.name=${SERVICE_NAME}" \
    --format '{{.ID}}' | head -1)
  if [[ -n "${CONTAINER_ID}" ]] \
     && docker exec "${CONTAINER_ID}" pg_isready -U "${PG_USER}" -d postgres -q 2>/dev/null; then
    log "ready after ${i}s"
    break
  fi
  sleep 1
  [[ $i -eq 60 ]] && fail "workflow-db not ready after 60s"
done

# ----- 5. dump/restore restore step (only on that path) ---------------------
if [[ "${PATH_CHOICE}" == "dump_restore" ]]; then
  log "restoring backup into fresh cluster"
  gunzip -c "${BACKUP_FILE}" \
    | docker exec -i -e PGPASSWORD="${PG_PASS}" "${CONTAINER_ID}" \
        psql -U "${PG_USER}" -d postgres
  log "restore complete — Prefect data is back"
fi

# ----- 6. Bootstrap progress_historian --------------------------------------
log "bootstrapping ${HISTORIAN_DB}"

# Inline schema — mirrors backend/sparkplug_bridge/historian/schema.py.
# Idempotent: CREATE DATABASE checks pg_database; everything else uses
# IF NOT EXISTS or jobs-table guards.
DB_EXISTS=$(docker exec -e PGPASSWORD="${PG_PASS}" "${CONTAINER_ID}" \
  psql -U "${PG_USER}" -d postgres -tAc \
  "SELECT 1 FROM pg_database WHERE datname='${HISTORIAN_DB}'")
if [[ -z "${DB_EXISTS}" ]]; then
  docker exec -e PGPASSWORD="${PG_PASS}" "${CONTAINER_ID}" \
    psql -U "${PG_USER}" -d postgres -c "CREATE DATABASE \"${HISTORIAN_DB}\""
  log "database created"
else
  log "database already exists"
fi

docker exec -i -e PGPASSWORD="${PG_PASS}" "${CONTAINER_ID}" \
  psql -U "${PG_USER}" -d "${HISTORIAN_DB}" -v ON_ERROR_STOP=1 <<'SQL'
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS metric_samples (
  ts_utc          TIMESTAMPTZ      NOT NULL,
  metric_id       TEXT             NOT NULL,
  group_id        TEXT             NOT NULL,
  edge_id         TEXT             NOT NULL,
  device_id       TEXT             NULL,
  metric_name     TEXT             NOT NULL,
  metric_type     TEXT             NOT NULL,
  value_double    DOUBLE PRECISION NULL,
  value_bool      BOOLEAN          NULL,
  value_text      TEXT             NULL,
  quality         TEXT             NOT NULL DEFAULT 'good',
  bd_seq          INTEGER          NOT NULL,
  seq             INTEGER          NOT NULL,
  source          TEXT             NOT NULL DEFAULT 'data'
);

SELECT create_hypertable(
  'metric_samples', 'ts_utc',
  chunk_time_interval => INTERVAL '6 hours',
  if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_metric_samples_metric_ts
  ON metric_samples (metric_id, ts_utc DESC);
CREATE INDEX IF NOT EXISTS idx_metric_samples_lookup
  ON metric_samples (group_id, edge_id, device_id, metric_name, ts_utc DESC);

CREATE MATERIALIZED VIEW IF NOT EXISTS metric_samples_1s
WITH (timescaledb.continuous) AS
SELECT metric_id,
       time_bucket(INTERVAL '1 second', ts_utc) AS bucket,
       AVG(value_double) AS avg,
       MIN(value_double) AS min,
       MAX(value_double) AS max,
       COUNT(*)          AS count
FROM metric_samples
WHERE value_double IS NOT NULL
GROUP BY metric_id, bucket
WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS metric_samples_30s
WITH (timescaledb.continuous) AS
SELECT metric_id,
       time_bucket(INTERVAL '30 seconds', ts_utc) AS bucket,
       AVG(value_double) AS avg,
       MIN(value_double) AS min,
       MAX(value_double) AS max,
       COUNT(*)          AS count
FROM metric_samples
WHERE value_double IS NOT NULL
GROUP BY metric_id, bucket
WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS metric_samples_5m
WITH (timescaledb.continuous) AS
SELECT metric_id,
       time_bucket(INTERVAL '5 minutes', ts_utc) AS bucket,
       AVG(value_double) AS avg,
       MIN(value_double) AS min,
       MAX(value_double) AS max,
       COUNT(*)          AS count
FROM metric_samples
WHERE value_double IS NOT NULL
GROUP BY metric_id, bucket
WITH NO DATA;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM timescaledb_information.jobs
    WHERE proc_name='policy_refresh_continuous_aggregate'
      AND hypertable_name='metric_samples_1s'
  ) THEN
    PERFORM add_continuous_aggregate_policy(
      'metric_samples_1s',
      start_offset      => INTERVAL '5 minutes',
      end_offset        => INTERVAL '5 seconds',
      schedule_interval => INTERVAL '30 seconds'
    );
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM timescaledb_information.jobs
    WHERE proc_name='policy_refresh_continuous_aggregate'
      AND hypertable_name='metric_samples_30s'
  ) THEN
    PERFORM add_continuous_aggregate_policy(
      'metric_samples_30s',
      start_offset      => INTERVAL '30 minutes',
      end_offset        => INTERVAL '1 minute',
      schedule_interval => INTERVAL '1 minute'
    );
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM timescaledb_information.jobs
    WHERE proc_name='policy_refresh_continuous_aggregate'
      AND hypertable_name='metric_samples_5m'
  ) THEN
    PERFORM add_continuous_aggregate_policy(
      'metric_samples_5m',
      start_offset      => INTERVAL '4 hours',
      end_offset        => INTERVAL '5 minutes',
      schedule_interval => INTERVAL '5 minutes'
    );
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM timescaledb_information.jobs
    WHERE proc_name='policy_retention'
      AND hypertable_name='metric_samples'
  ) THEN
    PERFORM add_retention_policy('metric_samples', INTERVAL '7 days');
  END IF;
END$$;
SQL

# ----- 7. Verify -------------------------------------------------------------
log "verifying schema"
docker exec -e PGPASSWORD="${PG_PASS}" "${CONTAINER_ID}" \
  psql -U "${PG_USER}" -d "${HISTORIAN_DB}" -tAc "
    SELECT 'ext=' || extname || ' v=' || extversion
      FROM pg_extension WHERE extname='timescaledb';
    SELECT 'hypertable=' || hypertable_name
      FROM timescaledb_information.hypertables
      WHERE hypertable_name='metric_samples';
    SELECT 'cagg=' || view_name
      FROM timescaledb_information.continuous_aggregates;
    SELECT 'job=' || proc_name || ' on ' || hypertable_name
      FROM timescaledb_information.jobs
      WHERE proc_name IN ('policy_refresh_continuous_aggregate','policy_retention');"

log "DONE"
echo
echo "Backup:  ${BACKUP_FILE}"
echo "Next:    deploy the historian_ingester service so rows actually flow."
echo "         It runs the bridge image with command:"
echo "           python -m sparkplug_bridge.historian"
echo "         Env it needs (defaults work inside the progress network):"
echo "           PROGRESS_NATS_URL=nats://broker:4222"
echo "           PROGRESS_HISTORIAN_DB_URL=postgresql://postgres:postgres@workflow-db:5432/${HISTORIAN_DB}"
echo "           PROGRESS_HISTORIAN_ADMIN_URL=postgresql://postgres:postgres@workflow-db:5432/postgres"
echo
echo "Rollback (in-place path): revert image with"
echo "  docker service update --image ${CURRENT_IMAGE} ${SERVICE_NAME}"
echo "Rollback (dump/restore): same image revert, then"
echo "  gunzip -c ${BACKUP_FILE} | docker exec -i <new-task-id> psql -U postgres -d postgres"
