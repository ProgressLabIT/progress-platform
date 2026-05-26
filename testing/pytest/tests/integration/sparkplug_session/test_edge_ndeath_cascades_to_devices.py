"""Spike: edge NDEATH cascades to device-level session.offline + stale fan-out per D-11/D-12.

Given an edge NBIRTH + one DBIRTH + one DDATA frame,
When the matching NDEATH (same bd_seq) arrives,
Then within 1.5s the bridge publishes:
  - progress.sparkplug.<group>.<edge>.session.offline (kind=session.offline)
  - progress.sparkplug.<group>.<edge>.<device>.session.offline (kind=session.offline) — D-12 cascade
  - per-metric metric.data with quality="stale" for each metric in last_values
AND sparkplug_last_values KV docs for affected metrics now have quality="stale" (D-10).
"""
import asyncio
import json

import pytest

from .frames import DT_FLOAT, make_dbirth, make_ddata, make_nbirth, make_ndeath

pytestmark = pytest.mark.integration

GROUP = "test6"
EDGE = "edge95"
DEVICE = "pump1"


@pytest.mark.asyncio
async def test_edge_ndeath_cascades_to_devices(
    fresh_kv_buckets,
    mqtt_publisher,
    nats_subscriber,
):
    await asyncio.sleep(0.5)

    # NBIRTH for the edge — registers the session at bd_seq=7.
    await mqtt_publisher(
        f"spBv1.0/{GROUP}/NBIRTH/{EDGE}",
        make_nbirth(
            bd_seq=7,
            seq=0,
            metrics=[
                {"name": "EdgeUptime", "alias": 1, "datatype": DT_FLOAT, "value": 100.0},
            ],
        ),
    )
    # DBIRTH for the device — registers device-scope metrics.
    await mqtt_publisher(
        f"spBv1.0/{GROUP}/DBIRTH/{EDGE}/{DEVICE}",
        make_dbirth(
            bd_seq=7,
            seq=1,
            metrics=[
                {"name": "Vibration", "alias": 10, "datatype": DT_FLOAT, "value": 22.0},
                {"name": "Pressure", "alias": 11, "datatype": DT_FLOAT, "value": 4.1},
            ],
        ),
    )
    # One DDATA so last_values is populated.
    await mqtt_publisher(
        f"spBv1.0/{GROUP}/DDATA/{EDGE}/{DEVICE}",
        make_ddata(
            seq=2,
            metrics=[{"alias": 10, "datatype": DT_FLOAT, "value": 22.5}],
        ),
    )
    await asyncio.sleep(1.5)

    baseline = len(nats_subscriber)

    # Matching NDEATH — bd_seq=7 matches the session.
    await mqtt_publisher(
        f"spBv1.0/{GROUP}/NDEATH/{EDGE}",
        make_ndeath(bd_seq=7),
    )

    deadline = asyncio.get_event_loop().time() + 2.5  # CONTEXT.md 1s budget + slack
    edge_offline = device_offline = stale_metrics = None
    while asyncio.get_event_loop().time() < deadline:
        await asyncio.sleep(0.1)
        after = nats_subscriber[baseline:]
        edge_offline = next(
            (e for e in after
             if e.get("kind") == "session.offline"
             and e["subject"] == f"progress.sparkplug.{GROUP}.{EDGE}.session.offline"),
            None,
        )
        device_offline = next(
            (e for e in after
             if e.get("kind") == "session.offline"
             and e["subject"] == f"progress.sparkplug.{GROUP}.{EDGE}.{DEVICE}.session.offline"),
            None,
        )
        stale_metrics = [
            e for e in after
            if e.get("kind") == "metric.data"
            and e["payload"].get("quality") == "stale"
            and f"{GROUP}.{EDGE}" in e["subject"]
        ]
        if edge_offline and device_offline and stale_metrics:
            break

    assert edge_offline is not None, "edge session.offline not published"
    assert device_offline is not None, "device session.offline (D-12 cascade) not published"
    assert stale_metrics, "stale metric.data fan-out not published"

    # KV+NATS coherence (D-10): last_values for the affected metric flipped to stale.
    last_values = fresh_kv_buckets["sparkplug_last_values"]
    entry = await last_values.get(f"{GROUP}.{EDGE}.{DEVICE}.Vibration")
    doc = json.loads(entry.value)
    assert doc["quality"] == "stale", f"expected quality=stale in KV, got {doc}"
