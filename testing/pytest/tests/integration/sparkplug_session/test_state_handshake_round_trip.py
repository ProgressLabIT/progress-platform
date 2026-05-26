"""Spike: bridge primary-host STATE handshake (INGEST-06 + D-02/D-03).

Given the bridge is running with default PROGRESS_BRIDGE_HOST_ID=progress-bridge,
When we open a fresh subscriber to spBv1.0/STATE/progress-bridge AND collect
     heartbeats on progress.notification.health.sparkplug.bridge,
Then the retained b"ONLINE" payload arrives on the STATE topic within 5s
AND at least one heartbeat carries state_online=True within 30s.
"""
import asyncio

import pytest

pytestmark = pytest.mark.integration

EXPECTED_HOST_ID = "progress-bridge"


@pytest.mark.asyncio
async def test_state_handshake_round_trip(
    mqtt_state_subscriber,
    bridge_heartbeat_subscriber,
):
    # Assertion 1: the bridge has published a retained ONLINE for its host_id.
    # mqtt_state_subscriber subscribes with clean_session=True so it should
    # receive the broker's stored retained payload immediately.
    deadline = asyncio.get_event_loop().time() + 5.0
    online_topic = None
    while asyncio.get_event_loop().time() < deadline and not online_topic:
        await asyncio.sleep(0.1)
        for topic, payload in mqtt_state_subscriber:
            if topic == f"spBv1.0/STATE/{EXPECTED_HOST_ID}" and payload == b"ONLINE":
                online_topic = topic
                break

    assert online_topic, (
        f"retained ONLINE not received within 5s on spBv1.0/STATE/{EXPECTED_HOST_ID}; "
        f"got: {[(t, p) for t, p in mqtt_state_subscriber]}"
    )

    # Assertion 2: a heartbeat carries state_online=True (D-03 round-trip observed).
    deadline = asyncio.get_event_loop().time() + 30.0
    observed = False
    while asyncio.get_event_loop().time() < deadline and not observed:
        await asyncio.sleep(0.5)
        for hb in bridge_heartbeat_subscriber:
            if hb.get("state_online") is True:
                observed = True
                break

    assert observed, (
        f"no heartbeat with state_online=True within 30s; "
        f"received: {bridge_heartbeat_subscriber[-3:]}"
    )

    # Bonus assertion: the heartbeat preserves Phase 1 fields (subtopic, ts, ok, service).
    last = bridge_heartbeat_subscriber[-1]
    for field in ("subtopic", "ts", "ok", "service"):
        assert field in last, f"heartbeat missing Phase 1 field {field}: {last}"
    # And carries the four D-02 enrichment fields.
    for field in ("mqtt_connected", "nats_connected", "state_online", "active_session_count"):
        assert field in last, f"heartbeat missing Phase 2 field {field}: {last}"
