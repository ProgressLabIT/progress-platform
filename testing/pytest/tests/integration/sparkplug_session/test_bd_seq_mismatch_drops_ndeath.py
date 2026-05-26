"""Spike: stale NDEATH (mismatched bdSeq) is dropped silently per D-05.

Given the bridge has registered an NBIRTH with bd_seq=5,
When we publish an NDEATH carrying bd_seq=3,
Then no `progress.sparkplug.<group>.<edge>.session.offline` subject is emitted
AND `sparkplug_sessions[<group>.<edge>]` retains alive=True bd_seq=5.
"""
import asyncio
import json

import pytest

from .frames import (
    DT_FLOAT,
    make_nbirth,
    make_ndeath,
)

pytestmark = pytest.mark.integration

GROUP = "test1"
EDGE = "edge99"


@pytest.mark.asyncio
async def test_bd_seq_mismatch_drops_ndeath(
    fresh_kv_buckets,
    mqtt_publisher,
    nats_subscriber,
):
    # Allow the subscriber to register before publishing.
    await asyncio.sleep(0.5)

    # Establish a session at bd_seq=5 with one metric.
    await mqtt_publisher(
        f"spBv1.0/{GROUP}/NBIRTH/{EDGE}",
        make_nbirth(
            bd_seq=5,
            seq=0,
            metrics=[{"name": "Temperature", "alias": 1, "datatype": DT_FLOAT, "value": 22.0}],
        ),
        qos=1,
        retain=False,
    )
    # Wait for the bridge to process and persist.
    await asyncio.sleep(1.5)

    # Snapshot subscriber state before injecting the stale NDEATH.
    before = list(nats_subscriber)

    # Stale NDEATH — bd_seq=3 does NOT match the session's bd_seq=5.
    await mqtt_publisher(
        f"spBv1.0/{GROUP}/NDEATH/{EDGE}",
        make_ndeath(bd_seq=3),
        qos=1,
        retain=False,
    )
    # Wait for the bridge to (correctly) drop and log without publishing.
    await asyncio.sleep(2.0)

    # Assertion 1: no NEW session.offline subject after the stale NDEATH.
    after_new = nats_subscriber[len(before):]
    offline_subjects = [
        e["subject"] for e in after_new
        if e.get("kind") == "session.offline" and EDGE in e["subject"]
    ]
    assert not offline_subjects, (
        f"expected NO session.offline after stale NDEATH; got: {offline_subjects}"
    )

    # Assertion 2: KV state preserved — alive=True, bd_seq=5.
    kv_sessions = fresh_kv_buckets["sparkplug_sessions"]
    entry = await kv_sessions.get(f"{GROUP}.{EDGE}")
    doc = json.loads(entry.value)
    assert doc["alive"] is True, f"expected alive=True, got {doc}"
    assert doc["bd_seq"] == 5, f"expected bd_seq=5, got {doc}"
