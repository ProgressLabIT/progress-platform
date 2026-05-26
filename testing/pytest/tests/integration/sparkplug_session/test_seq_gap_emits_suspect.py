"""Spike: seq gap emits a session.suspect notification per D-06.

Given the bridge has registered an NBIRTH at seq=0 with one aliased metric,
When we publish NDATA at seq=3 (gap of 2),
Then a notification arrives on `progress.notification.sparkplug` with
     kind="session.suspect", reason="seq_gap", and payload_ref carries
     expected_seq=1, observed_seq=3.
"""
import asyncio

import pytest

from .frames import DT_FLOAT, make_nbirth, make_ndata

pytestmark = pytest.mark.integration

GROUP = "test2"
EDGE = "edge98"


@pytest.mark.asyncio
async def test_seq_gap_emits_suspect(
    fresh_kv_buckets,
    mqtt_publisher,
    nats_subscriber,
):
    await asyncio.sleep(0.5)

    # Register a session with a Float metric aliased as 1.
    await mqtt_publisher(
        f"spBv1.0/{GROUP}/NBIRTH/{EDGE}",
        make_nbirth(
            bd_seq=1,
            seq=0,
            metrics=[{"name": "Temperature", "alias": 1, "datatype": DT_FLOAT, "value": 22.0}],
        ),
    )
    await asyncio.sleep(1.0)

    # Publish NDATA at seq=3 — gap of 2 (expected seq=1).
    await mqtt_publisher(
        f"spBv1.0/{GROUP}/NDATA/{EDGE}",
        make_ndata(
            seq=3,
            metrics=[{"alias": 1, "datatype": DT_FLOAT, "value": 23.0}],
        ),
    )
    # Wait for suspect notification to fan out.
    deadline = asyncio.get_event_loop().time() + 5.0
    suspects = []
    while asyncio.get_event_loop().time() < deadline and not suspects:
        await asyncio.sleep(0.1)
        suspects = [
            e for e in nats_subscriber
            if e.get("kind") == "session.suspect"
            and e.get("subject") == "progress.notification.sparkplug"
        ]

    assert suspects, (
        f"expected session.suspect notification; got subjects: "
        f"{[e['subject'] + ':' + str(e.get('kind')) for e in nats_subscriber]}"
    )
    doc = suspects[-1]["payload"]
    assert doc["reason"] == "seq_gap"
    assert doc["payload_ref"]["expected_seq"] == 1
    assert doc["payload_ref"]["observed_seq"] == 3
    assert doc["payload_ref"]["edge"] == EDGE
    assert doc["payload_ref"]["group"] == GROUP
