"""Historian schema constants — DDL strings, INSERT SQL, default tuning knobs.

Source of truth for the metric_samples hypertable shape per ADR-0005 (decisions/
0005-timescale-schema-and-downsampling.md). Bumping any DDL here is a schema
change — co-edit with bootstrap.py callers and document in ADR-0005.

Subscribe topology per ADR-0002 §"Wildcards and consumer patterns".
"""

# ----- Identifiers -----------------------------------------------------------

TABLE_NAME = "metric_samples"
VIEW_1S = "metric_samples_1s"
VIEW_30S = "metric_samples_30s"
VIEW_5M = "metric_samples_5m"

# ----- Subscribe topology (ADR-0002, RESEARCH §Pitfall 5) --------------------
# 4 separate subscriptions — NATS does not support multi-subject syntax in one
# subscribe(), and the 6-vs-7-token edge/device split cannot be covered by a
# single `*` wildcard pattern.
SUBJECTS = (
    "progress.sparkplug.*.*.*.metric.*.data",   # device-level data (7 tokens)
    "progress.sparkplug.*.*.*.metric.*.birth",  # device-level birth
    "progress.sparkplug.*.*.metric.*.data",     # edge-level data   (6 tokens)
    "progress.sparkplug.*.*.metric.*.birth",    # edge-level birth
)

# ----- Batch + flush defaults (D-06; mirrored in HistorianSettings) ---------

BATCH_SIZE_DEFAULT = 500
FLUSH_MS_DEFAULT = 100

# ----- INSERT (parameterized — see executemany in ingester.flush_loop) ------

INSERT_SQL = """
INSERT INTO metric_samples
  (ts_utc, metric_id, group_id, edge_id, device_id,
   metric_name, metric_type, value_double, value_bool, value_text,
   quality, bd_seq, seq, source)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
"""

# ----- DDL bodies (ADR-0005 schema; RESEARCH §Pattern 2) --------------------

TABLE_DDL = """
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
)
"""

HYPERTABLE_DDL = """
SELECT create_hypertable(
  'metric_samples',
  'ts_utc',
  chunk_time_interval => INTERVAL '6 hours',
  if_not_exists => TRUE
)
"""

INDEXES_DDL = """
CREATE INDEX IF NOT EXISTS idx_metric_samples_metric_ts
  ON metric_samples (metric_id, ts_utc DESC);
CREATE INDEX IF NOT EXISTS idx_metric_samples_lookup
  ON metric_samples (group_id, edge_id, device_id, metric_name, ts_utc DESC);
"""

# Continuous aggregates — Postgres 12+ supports CREATE MATERIALIZED VIEW IF NOT EXISTS,
# and TimescaleDB inherits this behavior on the WITH (timescaledb.continuous) form.
CAGG_1S_DDL = """
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
WITH NO DATA
"""

CAGG_30S_DDL = """
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
WITH NO DATA
"""

CAGG_5M_DDL = """
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
WITH NO DATA
"""

# Refresh policies — no IF NOT EXISTS form on add_continuous_aggregate_policy;
# check timescaledb_information.jobs first (RESEARCH §Pattern 2 + Pitfall 3).
# Window picks per RESEARCH §Discretionary Decisions #2:
#   1s  view: start_offset 5m,  end_offset 5s,  schedule_interval 30s  (10x ratio — safe)
#   30s view: start_offset 30m, end_offset 1m,  schedule_interval 1m   (avoids start==schedule edge case)
#   5m  view: start_offset 4h,  end_offset 5m,  schedule_interval 5m
POLICY_1S = """
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM timescaledb_information.jobs
    WHERE proc_name = 'policy_refresh_continuous_aggregate'
      AND hypertable_name = 'metric_samples_1s'
  ) THEN
    PERFORM add_continuous_aggregate_policy(
      'metric_samples_1s',
      start_offset      => INTERVAL '5 minutes',
      end_offset        => INTERVAL '5 seconds',
      schedule_interval => INTERVAL '30 seconds'
    );
  END IF;
END$$;
"""

POLICY_30S = """
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM timescaledb_information.jobs
    WHERE proc_name = 'policy_refresh_continuous_aggregate'
      AND hypertable_name = 'metric_samples_30s'
  ) THEN
    PERFORM add_continuous_aggregate_policy(
      'metric_samples_30s',
      start_offset      => INTERVAL '30 minutes',
      end_offset        => INTERVAL '1 minute',
      schedule_interval => INTERVAL '1 minute'
    );
  END IF;
END$$;
"""

POLICY_5M = """
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM timescaledb_information.jobs
    WHERE proc_name = 'policy_refresh_continuous_aggregate'
      AND hypertable_name = 'metric_samples_5m'
  ) THEN
    PERFORM add_continuous_aggregate_policy(
      'metric_samples_5m',
      start_offset      => INTERVAL '4 hours',
      end_offset        => INTERVAL '5 minutes',
      schedule_interval => INTERVAL '5 minutes'
    );
  END IF;
END$$;
"""

# Retention — TimescaleDB drops chunks (not rows). Idempotent: TimescaleDB
# raises an error if a retention policy already exists; wrap in DO/IF NOT EXISTS
# using the same jobs-table guard for symmetry with refresh policies.
RETENTION_POLICY = """
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM timescaledb_information.jobs
    WHERE proc_name = 'policy_retention'
      AND hypertable_name = 'metric_samples'
  ) THEN
    PERFORM add_retention_policy('metric_samples', INTERVAL '7 days');
  END IF;
END$$;
"""
