"""Spike: historian_ingester writes a metric_samples row when a metric.data
arrives on progress.sparkplug.*.

Given the historian_ingester is up and subscribed to progress.sparkplug.>,
When we publish a synthetic progress.sparkplug.test3.edge99.pump1.metric.vibration.data
     envelope matching ADR-0002's JSON shape,
Then a row appears in metric_samples with metric_name='Vibration' and
     value_double~=22.5 within 5 s.

Requires: live docker-stack with historian_ingester running (plan 03-03).
Harness: existing nats_fixture (function-scoped) from conftest.py. No new fixtures.
"""
from __future__ import annotations

import asyncio
import json
import time

import asyncpg
import pytest

pytestmark = pytest.mark.integration

GROUP = "test3"
EDGE = "edge99"
DEVICE = "pump1"
METRIC = "Vibration"
SUBJECT = f"progress.sparkplug.{GROUP}.{EDGE}.{DEVICE}.metric.{METRIC.lower()}.data"
HIST_DB_URL = "postgresql://postgres:postgres@localhost:5432/progress_historian"
POLL_DEADLINE_SEC = 5.0
POLL_INTERVAL_SEC = 0.1


@pytest.mark.asyncio
async def test_historian_ingest_writes_row(nats_fixture):
    # Allow ingester subscription to be active before publishing.
    # The ingester subscribes on startup; 2 s covers any cold-start lag.
    await asyncio.sleep(2.0)

    payload = {
        "schema_version": 1,
        "ts_utc_ms": int(time.time() * 1000),
        "source_ts_utc_ms": None,
        "group": GROUP,
        "edge": EDGE,
        "device": DEVICE,
        "bd_seq": 1,
        "seq": 0,
        "kind": "metric.data",
        "name": METRIC,
        "alias": None,
        "type": "Float",
        "value": 22.5,
        "quality": "good",
    }
    await nats_fixture.publish(SUBJECT, json.dumps(payload).encode())

    # Poll metric_samples for up to POLL_DEADLINE_SEC.
    deadline = asyncio.get_event_loop().time() + POLL_DEADLINE_SEC
    conn = await asyncpg.connect(HIST_DB_URL)
    try:
        row = None
        while asyncio.get_event_loop().time() < deadline and row is None:
            await asyncio.sleep(POLL_INTERVAL_SEC)
            row = await conn.fetchrow(
                "SELECT metric_name, value_double FROM metric_samples "
                "WHERE metric_name = $1 AND group_id = $2 AND edge_id = $3 "
                "ORDER BY ts_utc DESC LIMIT 1",
                METRIC, GROUP, EDGE,
            )
        assert row is not None, (
            f"expected metric_samples row for metric_name='{METRIC}' within "
            f"{POLL_DEADLINE_SEC}s — ingester may not be running or subscribed"
        )
        assert row["metric_name"] == METRIC
        assert row["value_double"] == pytest.approx(22.5)
    finally:
        await conn.close()
