# 0005 — Timescale Hypertable Schema, Downsampling, and Postgres Consolidation

**Status:** decided
**Date:** 2026-04-28
**Revised:** 2026-04-28 (consolidated onto Prefect's existing Postgres instead of a separate `historian_db` service)
**Audience:** S1 (bridge / Timescale ingester), S2 (UI history chart)
**Supersedes:** none

## Context

The v1 demo includes a Timescale-backed historian for Sparkplug metrics, per
ADR-0001. The historian gives the demo persistence credibility for an
audience that expects "data we collect, query, and trust" rather than
in-memory sparklines that vanish on refresh. This ADR specifies the
hypertable shape, the ingest path from NATS to Timescale, the
continuous-aggregate buckets that the `/api/uns/history` endpoint
queries, the retention policy for the demo footprint, and the
**consolidation onto Prefect's existing Postgres instance** rather than
running a second Postgres process.

The original draft of this ADR specified a separate `historian_db` service.
On 2026-04-28 review the consolidation decision was made: TimescaleDB is a
Postgres extension and Postgres handles multiple databases natively. Two
Postgres processes on the same host duplicate resources and operational
overhead for no architectural gain. v1 demo runs a single Postgres instance
serving both Prefect's `prefect` database (vanilla) and the historian's
`progress_historian` database (with the `timescaledb` extension enabled).

## Decision

### Postgres consolidation

The existing `workflow-db` service (currently `postgres:15.2-alpine`) is
re-imaged onto `timescale/timescaledb:latest-pg15`. Same major Postgres
version, no Prefect data migration needed. The TimescaleDB extension is
installed at the cluster level but **enabled per-database**:

- Prefect's `prefect` database: vanilla Postgres usage, no
  `CREATE EXTENSION timescaledb` call. Behaviour identical to the old
  `postgres:15.2-alpine`.
- New `progress_historian` database: `CREATE EXTENSION timescaledb;` at
  bootstrap; holds the hypertable + continuous aggregates described
  below.

The service stays in `deploy/compose/workflow.yaml` (its current home).
The new `progress_historian` database is created by an init-time SQL
script run alongside the existing Prefect DB init.

There is **no** separate `historian_db` service. The `historian_data`
volume listed in earlier drafts is dropped; data lives in the existing
`workflow_db` external volume.

### Ingester topology

A new ingester process named `historian_ingester` lives in
`deploy/compose/sparkplug.yaml`:

- Image: same Python base as `sparkplug_bridge` (built from a shared
  `backend/sparkplug/` Dockerfile if practical).
- Subscribes to `progress.sparkplug.>` filtered to `metric.*.data` and
  `metric.*.birth` (per ADR-0002).
- Writes to `metric_samples` hypertable in batches of up to 500 rows with a
  100 ms flush window.
- Owns no other state. Crash-safe by virtue of being a NATS consumer with no
  ack-tracking — at-most-once delivery is acceptable for demo history.
- Connects to `workflow-db` on the existing internal network with the
  `progress_historian` database name and a dedicated `historian` role.

### Hypertable shape

```sql
CREATE TABLE metric_samples (
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
  source          TEXT             NOT NULL DEFAULT 'data'  -- 'data' | 'birth'
);

SELECT create_hypertable(
  'metric_samples',
  'ts_utc',
  chunk_time_interval => INTERVAL '6 hours'
);

CREATE INDEX ON metric_samples (metric_id, ts_utc DESC);
CREATE INDEX ON metric_samples (group_id, edge_id, device_id, metric_name, ts_utc DESC);
```

Notes:

- `ts_utc` is the Sparkplug payload timestamp when present
  (`source_ts_utc_ms` from ADR-0002 envelope), else the bridge clock
  (`ts_utc_ms`). Choice is made by the ingester, recorded in `source`
  field for diagnostics.
- `metric_id` is the dotted slug ID from ADR-0004
  (`<group>.<edge>[.<device>].<name>`). Denormalized columns
  (`group_id`/`edge_id`/`device_id`/`metric_name`) live alongside for
  ad-hoc SQL queries during the demo and post-demo analysis.
- `value_*` columns are typed; only one is populated per row depending on
  `metric_type`. Numeric Sparkplug types all collapse to
  `value_double` (acceptable precision loss for the demo). Boolean →
  `value_bool`. String → `value_text`. Other types are dropped from the
  ingest path in v1 (DataSet, Template, File per ADR-0002).
- `source = 'birth'` rows record per-metric birth events so the UI can
  recover initial state from history if needed. Not yet consumed by v1 UI.
- 6-hour chunk interval is conservative for a demo expected to run a few
  hours at most; tuning is a post-demo exercise.

### Continuous aggregates

Three rollups are pre-created so `/api/uns/history` (per ADR-0004) can
pick a bucket that satisfies the requested `max_points` without scanning
raw samples:

```sql
CREATE MATERIALIZED VIEW metric_samples_1s
WITH (timescaledb.continuous) AS
SELECT
  metric_id,
  time_bucket(INTERVAL '1 second', ts_utc) AS bucket,
  AVG(value_double) AS avg,
  MIN(value_double) AS min,
  MAX(value_double) AS max,
  COUNT(*)          AS count
FROM metric_samples
WHERE value_double IS NOT NULL
GROUP BY metric_id, bucket
WITH NO DATA;

-- Same shape for 30-second and 5-minute buckets.
CREATE MATERIALIZED VIEW metric_samples_30s ...
CREATE MATERIALIZED VIEW metric_samples_5m  ...

-- Refresh policies: each view refreshes every 30 s with a 5 s lag.
SELECT add_continuous_aggregate_policy('metric_samples_1s',
  start_offset => INTERVAL '5 minutes',
  end_offset   => INTERVAL '5 seconds',
  schedule_interval => INTERVAL '30 seconds');
-- Likewise for 30s and 5m views (different start_offsets).
```

Bucket selection rule (implemented in the API):

| Range requested | Bucket used |
|---|---|
| ≤ 5 min | raw `metric_samples` |
| ≤ 30 min | `metric_samples_1s` |
| ≤ 4 hours | `metric_samples_30s` |
| ≤ 24 hours | `metric_samples_5m` |

The 24-hour cap from ADR-0004 means the 5-minute bucket is the worst-case;
≤ 288 points per response, well under the 500-point UI default.

For Boolean and String metrics, the API short-circuits the bucket choice:
Boolean returns last-value-per-bucket; String returns last-value-per-bucket
or "n samples in bucket" depending on UI need (not exercised in v1 demo).

### Retention

Demo footprint is small; v1 sets retention to 7 days on raw `metric_samples`
and indefinite on continuous aggregates (which are tiny by construction):

```sql
SELECT add_retention_policy('metric_samples', INTERVAL '7 days');
```

`make demo-reset` truncates `metric_samples` and refreshes all continuous
aggregates from empty. This is the rehearsal recovery path.

### Roles

Two Postgres roles inside the consolidated cluster:

- `prefect` (existing, untouched): owns the `prefect` database. Used by Prefect.
- `historian` (new): owns the `progress_historian` database. Used by both
  the ingester and the API's history endpoint. v1 demo reuses one role for
  both reads and writes; a read-only role for API queries is a post-demo
  hardening.

Passwords for both roles live in Docker secrets (the existing `progress_*`
secret pattern from `single_node_setup.yaml`):

- `progress_workflow_db_pwd` (existing).
- `progress_historian_db_pwd` (new).

### Ingest performance budget

For v1 demo expected load (≤ 50 metrics × 1 Hz nominal, with bursts to
~200 msg/s during scenario alarm phase), the ingester's 500-row batch +
100 ms flush is comfortably over-provisioned. No load test required for v1.

### Connection wiring

- Ingester reads `historian` role's password from
  `/run/secrets/progress_historian_db_pwd` (Docker secret).
- API reads the same secret to query Timescale for `/history`. API uses a
  dedicated SQLAlchemy engine (read-only role would be better post-demo;
  v1 reuses the same role).
- Bridge does NOT talk to Timescale directly. The historian is a parallel
  consumer of NATS, not a downstream of the bridge.

## Trade-offs and rejected options

**Reuse Prefect's Postgres vs separate Timescale instance.** The original
draft chose separate. On review, separate was rejected: TimescaleDB is a
clean Postgres extension; Postgres is multi-database; running two Postgres
processes on the same host wastes RAM and adds an unnecessary backup target.
Single instance with two databases is the standard pattern.

**ArangoDB as historian.** Rejected. Arango isn't a time-series store; the
write throughput and downsampling story would be weak. The audience knows
the difference.

**InfluxDB as the historian.** Considered as an alternative if we ever need
to physically separate the historian from Prefect's Postgres (e.g. moving
it to a CPU/RAM-flexible host). Rejected for v1 demo and likely for v2
because:
- Progress is a SQL shop; introducing Flux query language adds an admin and
  query-learning surface for no functional benefit at this scale.
- TimescaleDB on a separate Postgres instance solves the physical-isolation
  case without protocol change.
- InfluxDB's commercial-license shape on the storage engine has historically
  caused friction in industrial customers.

If physical separation is ever needed, the right move is a second Postgres
instance running the same TimescaleDB image, not a different TSDB.

**Single wide table vs metric-per-table.** Single hypertable with
`metric_id` filter and a covering index is the Timescale idiom and
performs fine at demo scale.

**Compression policy.** Skipped for v1 demo. Timescale compression adds a
configuration vector for no demo benefit at this footprint.

**Per-metric pre-aggregated columns.** Considered keeping last_value /
first_value on a row; dropped for v1 simplicity. Continuous aggregates
serve the same purpose.

**Storing protobuf raw payloads alongside the decoded value.** Rejected.
Protobuf stays inside the bridge per ADR-0002. The historian consumes the
JSON envelope only.

## Consequences

- S1 (bridge) extends to include the `historian_ingester` service in the
  same Python codebase under `backend/sparkplug/historian.py`. The bridge
  process and the ingester process are separate containers but share Docker
  image and codebase.
- S1 also adds the `metric_samples` migration and the three continuous
  aggregate views as a SQL bootstrap script. Bootstrap runs against the
  `progress_historian` database on first deploy.
- The `workflow-db` service in `deploy/compose/workflow.yaml` switches
  image from `postgres:15.2-alpine` to `timescale/timescaledb:latest-pg15`.
  S1 owns that one-line change and confirms Prefect's data is unaffected.
- S2 (UI) wires the ECharts time-series chart to
  `/api/uns/history?subject=...` (ADR-0004 contract) and renders avg +
  min/max band per bucket.
- S5 (demo data) ensures the historian schema is empty in the restored DB
  (history is built up live during the demo run; we don't ship pre-baked
  history).
- `make demo-reset` truncates `metric_samples` between rehearsals so each
  run starts clean.

## Related

- ADR-0002 — NATS subject taxonomy (envelope shape consumed by the
  ingester).
- ADR-0004 — UNS HTTP read API; `/api/uns/history` consumes the
  continuous aggregates here.
- ADR-0007 — simulator scenario (drives the data shape that needs
  meaningful downsampling).
- `deploy/compose/workflow.yaml` — service the consolidation touches.
