"""Spike: 5 seq gaps within 60s flip session offline with reason='bridge_timeout' (D-07).

Given the bridge defaults to gap_tolerance=5 within a 60s rolling window,
When we publish NBIRTH then 5 NDATA frames each producing a seq gap,
Then a `session.offline` arrives on progress.sparkplug.<group>.<edge>.session.offline
     with reason="bridge_timeout".
"""
import asyncio

import pytest

from .frames import DT_FLOAT, make_nbirth, make_ndata

pytestmark = pytest.mark.integration

GROUP = "test3"
EDGE = "edge97"


@pytest.mark.asyncio
async def test_suspect_cap_flips_session_offline(
    fresh_kv_buckets,
    mqtt_publisher,
    nats_subscriber,
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

    # Five gaps. After every gap the bridge increments gaps_observed.
    # Pick seqs that each represent a gap from the prior frame:
    #   prior=0 -> publish 3 (gap 1->3)
    #   prior=3 -> publish 6 (gap 4->6)
    #   prior=6 -> publish 9 (gap 7->9)
    #   prior=9 -> publish 12 (gap 10->12)
    #   prior=12 -> publish 15 (gap 13->15) — fifth gap, cap reached
    for next_seq in (3, 6, 9, 12, 15):
        await mqtt_publisher(
            f"spBv1.0/{GROUP}/NDATA/{EDGE}",
            make_ndata(
                seq=next_seq,
                metrics=[{"alias": 1, "datatype": DT_FLOAT, "value": 22.5}],
            ),
        )
        await asyncio.sleep(0.3)

    # Wait for the bridge_timeout offline.
    deadline = asyncio.get_event_loop().time() + 5.0
    offlines = []
    while asyncio.get_event_loop().time() < deadline and not offlines:
        await asyncio.sleep(0.1)
        offlines = [
            e for e in nats_subscriber
            if e.get("kind") == "session.offline"
            and EDGE in e["subject"]
            and e["payload"].get("reason") == "bridge_timeout"
        ]

    assert offlines, (
        f"expected session.offline reason=bridge_timeout; got: "
        f"{[(e['subject'], e['payload'].get('reason')) for e in nats_subscriber if e.get('kind') == 'session.offline']}"
    )
