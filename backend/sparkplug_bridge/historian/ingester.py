"""Historian ingester — NATS subscriber + asyncpg writer.

Phase 3 D-04: same image as bridge, different CMD. Module path
'sparkplug_bridge.historian' invoked via `python -m`.

Per RESEARCH §Pattern 3 + D-06: in-memory buffer with dual flush trigger
(>=BATCH_SIZE rows OR >=FLUSH_MS since first row), executemany INSERT to
metric_samples. Per RESEARCH §Pitfall 5: four separate subscribe() calls
(NATS does not support multi-subject syntax in one subscription).

Crash semantics (D-07): no ack-tracking. On restart, ingester reconnects
and resumes; gaps during downtime are accepted demo-side (per ADR-0005).
"""
import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timezone

import asyncpg
import nats

from utils import nats_client  # backend/api/utils/nats_client.py via PYTHONPATH

from ..heartbeat import heartbeat_loop
from .bootstrap import bootstrap
from .config import HistorianSettings, get_historian_config
from .schema import INSERT_SQL, SUBJECTS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("sparkplug_bridge.historian")


# Sparkplug B numeric type names that collapse to value_double per ADR-0005.
_NUMERIC_TYPES = frozenset({
    "Int8", "Int16", "Int32", "Int64",
    "UInt8", "UInt16", "UInt32", "UInt64",
    "Float", "Double",
})


class Buffer:
    """In-memory row buffer with dual flush trigger (size or time).

    RESEARCH §Pattern 3 — no codebase analog (the bridge's asyncio.Queue in
    main.py:543-576 is single-message, not batched). Single-task ingester
    means no locking is required.
    """

    def __init__(self, batch_size: int, flush_ms: int) -> None:
        self.batch_size = batch_size
        self.flush_ms = flush_ms
        self.rows: list[tuple] = []
        self.first_ts_mono: float | None = None

    def add(self, row: tuple) -> None:
        if not self.rows:
            self.first_ts_mono = time.monotonic()
        self.rows.append(row)

    def should_flush_size(self) -> bool:
        return len(self.rows) >= self.batch_size

    def should_flush_time(self) -> bool:
        return (
            self.first_ts_mono is not None
            and (time.monotonic() - self.first_ts_mono) * 1000 >= self.flush_ms
        )

    def drain(self) -> list[tuple]:
        rows, self.rows, self.first_ts_mono = self.rows, [], None
        return rows


def message_to_row(subject: str, data: bytes) -> tuple | None:
    """Parse ADR-0002 envelope -> tuple matching metric_samples columns.

    Returns None for unsupported types or malformed payloads. Never raises
    (per-message error tolerance modeled on main.py:563-576 _queue_worker).

    Tuple column order MUST match schema.INSERT_SQL:
      (ts_utc, metric_id, group_id, edge_id, device_id,
       metric_name, metric_type, value_double, value_bool, value_text,
       quality, bd_seq, seq, source)
    """
    try:
        doc = json.loads(data)
    except json.JSONDecodeError:
        logger.warning("non-JSON payload on %s - dropping", subject)
        return None

    try:
        kind = doc["kind"]               # "metric.data" | "metric.birth"
        group = doc["group"]
        edge = doc["edge"]
        device = doc.get("device")        # None on edge-level subjects
        metric_name = doc["name"]
        metric_type = doc["type"]
        value = doc["value"]
        quality = doc.get("quality", "good")
        bd_seq = int(doc["bd_seq"])
        seq = int(doc["seq"]) if doc.get("seq") is not None else 0
        ts_utc_ms = int(doc["ts_utc_ms"])
        source_ts_utc_ms = doc.get("source_ts_utc_ms")
    except (KeyError, TypeError, ValueError) as exc:
        logger.warning("malformed envelope on %s: %s - dropping", subject, exc)
        return None

    # Type collapse per ADR-0005 §"Hypertable shape" notes.
    if metric_type in _NUMERIC_TYPES:
        try:
            value_double, value_bool, value_text = float(value), None, None
        except (TypeError, ValueError):
            logger.warning("non-numeric value for %s on %s - dropping", metric_type, subject)
            return None
    elif metric_type == "Boolean":
        value_double, value_bool, value_text = None, bool(value), None
    elif metric_type == "String":
        value_double, value_bool, value_text = None, None, str(value)
    else:
        # DataSet, Template, File, DateTime - dropped from v1 ingest path per ADR-0005.
        return None

    # ts_utc: prefer Sparkplug payload timestamp when present; else bridge clock.
    ts_ms = source_ts_utc_ms if source_ts_utc_ms is not None else ts_utc_ms
    ts_utc = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)

    # metric_id: <group>.<edge>[.<device>].<name> per ADR-0005.
    if device:
        metric_id = f"{group}.{edge}.{device}.{metric_name}"
    else:
        metric_id = f"{group}.{edge}.{metric_name}"

    # source: 'data' | 'birth' from envelope kind.
    source = "birth" if kind == "metric.birth" else "data"

    return (
        ts_utc, metric_id, group, edge, device,
        metric_name, metric_type, value_double, value_bool, value_text,
        quality, bd_seq, seq, source,
    )


async def flush_loop(buf: Buffer, conn: asyncpg.Connection) -> None:
    """Periodically flush the buffer to Postgres via executemany.

    Polls at half the flush window (RESEARCH §Pattern 3). Errors per-flush
    are caught and logged - never let one failed insert kill the loop
    (per-message tolerance shape mirrors main.py:563-576 _queue_worker).
    """
    poll_interval = max(buf.flush_ms / 1000 / 2, 0.005)
    while True:
        await asyncio.sleep(poll_interval)
        if buf.should_flush_size() or buf.should_flush_time():
            rows = buf.drain()
            if not rows:
                continue
            try:
                await conn.executemany(INSERT_SQL, rows)
                logger.debug("flushed %d rows", len(rows))
            except Exception:
                logger.exception(
                    "flush failed (rows=%d) - dropping batch", len(rows),
                )


async def main() -> None:
    cfg: HistorianSettings = get_historian_config()
    logger.info(
        "historian_ingester starting - NATS=%s db=%s batch=%d flush_ms=%d",
        cfg.nats_url, cfg.historian_db_name,
        cfg.historian_batch_size, cfg.historian_flush_ms,
    )

    # 1. Bootstrap DDL - idempotent. Safe on every restart.
    await bootstrap(
        admin_url=cfg.historian_admin_url,
        target_url=cfg.historian_db_url,
        target_db=cfg.historian_db_name,
    )

    # 2. asyncpg single connection (RESEARCH §Discretionary Decisions #3 -
    #    no pool; single writer task).
    conn = await asyncpg.connect(cfg.historian_db_url)

    # 3. NATS - raw nats.connect for subscribe path; nats_client singleton
    #    used by heartbeat module (own publisher).
    nc = await nats.connect(cfg.nats_url)
    await nats_client.connect(cfg.nats_url)

    buf = Buffer(
        batch_size=cfg.historian_batch_size,
        flush_ms=cfg.historian_flush_ms,
    )

    async def on_msg(msg) -> None:
        row = message_to_row(msg.subject, msg.data)
        if row is not None:
            buf.add(row)

    # 4. Four subscribe() calls per RESEARCH §Pitfall 5.
    for subj in SUBJECTS:
        await nc.subscribe(subj, cb=on_msg)
        logger.info("subscribed: %s", subj)

    # 5. Background tasks.
    flush_task = asyncio.create_task(flush_loop(buf, conn))
    hb_task = asyncio.create_task(
        heartbeat_loop(
            "historian",
            state=None,
            interval_sec=cfg.historian_heartbeat_interval_sec,
        )
    )

    try:
        await asyncio.gather(flush_task, hb_task)
    except asyncio.CancelledError:
        pass
    finally:
        for t in (flush_task, hb_task):
            t.cancel()
            try:
                await t
            except asyncio.CancelledError:
                pass
        await nc.drain()
        await nats_client.drain()
        await conn.close()
        logger.info("historian_ingester stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
