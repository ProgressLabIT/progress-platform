"""Spike: NDATA alias miss increments gaps_observed in sparkplug_sessions (D-08).

Given the bridge has registered a session with alias=1 for "Temperature",
When we publish NDATA referencing alias=99 (unregistered),
Then sparkplug_sessions[<group>.<edge>].gaps_observed >= 1.
"""
import asyncio
import json

import pytest

from .frames import DT_FLOAT, make_nbirth, make_ndata

pytestmark = pytest.mark.integration

GROUP = "test4"
EDGE = "edge96"


@pytest.mark.asyncio
async def test_alias_miss_increments_gap_counter(
    fresh_kv_buckets,
    mqtt_publisher,
):
    await asyncio.sleep(0.5)

    await mqtt_publisher(
        f"spBv1.0/{GROUP}/NBIRTH/{EDGE}",
        make_nbirth(
            bd_seq=1,
            seq=0,
            metrics=[{"name": "Temperature", "alias": 1, "datatype": DT_FLOAT, "value": 22.0}],
        ),
    )
    await asyncio.sleep(1.0)

    # NDATA with unknown alias 99 — bridge should log + drop + increment counter.
    await mqtt_publisher(
        f"spBv1.0/{GROUP}/NDATA/{EDGE}",
        make_ndata(
            seq=1,
            metrics=[{"alias": 99, "datatype": DT_FLOAT, "value": 99.9}],
        ),
    )
    await asyncio.sleep(2.0)

    kv = fresh_kv_buckets["sparkplug_sessions"]
    entry = await kv.get(f"{GROUP}.{EDGE}")
    doc = json.loads(entry.value)
    assert doc.get("gaps_observed", 0) >= 1, (
        f"expected gaps_observed >= 1 after alias miss; got {doc}"
    )
