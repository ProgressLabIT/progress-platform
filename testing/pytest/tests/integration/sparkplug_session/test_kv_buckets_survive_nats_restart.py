"""Spike: sparkplug_* KV buckets survive a NATS container restart per CONTEXT.md SC-4.

Given a session is registered (NBIRTH) and the bridge has written
     sparkplug_sessions[<group>.<edge>] with bd_seq=11,
When we restart the broker container,
Then after broker recovery, sparkplug_sessions[<group>.<edge>] is still
     readable AND retains bd_seq=11.
"""
import asyncio
import json

import pytest

from .frames import DT_FLOAT, make_nbirth

pytestmark = pytest.mark.integration

GROUP = "test7"
EDGE = "edge94"


@pytest.mark.asyncio
async def test_kv_buckets_survive_nats_restart(
    fresh_kv_buckets,
    mqtt_publisher,
    nats_fixture,
    resolve_container,
):
    await asyncio.sleep(0.5)

    await mqtt_publisher(
        f"spBv1.0/{GROUP}/NBIRTH/{EDGE}",
        make_nbirth(
            bd_seq=11,
            seq=0,
            metrics=[{"name": "Voltage", "alias": 1, "datatype": DT_FLOAT, "value": 240.0}],
        ),
    )
    await asyncio.sleep(2.0)

    # Confirm pre-restart KV state.
    kv = fresh_kv_buckets["sparkplug_sessions"]
    before = json.loads((await kv.get(f"{GROUP}.{EDGE}")).value)
    assert before["bd_seq"] == 11

    # Restart broker container — JetStream store_dir is a mounted volume so
    # KV stream contents persist (RESEARCH §1 + INFRA-02 spike confirmation).
    # Check both Swarm service name and plain compose name.
    try:
        container = resolve_container("progress_broker")
    except RuntimeError:
        container = resolve_container("broker")
    container.restart(timeout=15)

    # Wait for NATS to come back up and the existing nats_fixture client to reconnect.
    # (nats-py auto-reconnects with reconnect_time_wait=2 by default.)
    await asyncio.sleep(10.0)

    # Re-bind to the bucket post-restart and read.
    js = nats_fixture.jetstream()
    kv_after = await js.key_value("sparkplug_sessions")
    entry_after = await kv_after.get(f"{GROUP}.{EDGE}")
    after = json.loads(entry_after.value)
    assert after["bd_seq"] == 11, (
        f"KV bucket lost data across NATS restart; before={before} after={after}"
    )
