"""Spike: session persistence across NATS restart (BEST-EFFORT per D-08).

This test failing does NOT trigger the HiveMQ fallback. CONTEXT.md D-08:
  "Session-persistence failure alone is treated as best-effort — the bridge can
   work around it with internal caching during reconnect, so it doesn't trigger
   the fallback by itself."

The test xfails on failure rather than failing the suite.
"""
import asyncio
import time

import aiomqtt
import pytest

pytestmark = pytest.mark.integration

MQTT_HOST = "localhost"
MQTT_PORT = 1883


@pytest.mark.asyncio
async def test_session_persistence_across_restart(docker_client, resolve_container):
    """Given a persistent subscriber (clean_session=False, stable client_id) is
         connected and messages are queued during a NATS restart,
    When the subscriber reconnects with the same client_id,
    Then queued QoS 1 messages are delivered.
    """
    received: list[bytes] = []
    persistent_id = "spike-persistent-1"

    # Round 1: connect with clean_session=False, subscribe, then close cleanly.
    c1 = aiomqtt.Client(
        hostname=MQTT_HOST, port=MQTT_PORT,
        identifier=persistent_id,
        protocol=aiomqtt.ProtocolVersion.V311,
        clean_session=False,  # KEY: enables broker-side session persistence.
    )
    async with c1:
        await c1.subscribe("spBv1.0/plant1/NDATA/edge1", qos=1)
    # c1 now disconnected; broker still tracks the session for `persistent_id`.

    # Round 2: restart NATS (simulator continues to publish into the void;
    # broker spool resumes once NATS is back).
    broker = resolve_container("progress_broker")
    broker.restart()
    await asyncio.sleep(8.0)  # cold-start + JetStream init window.

    # Round 3: reconnect with the same client_id.
    c2 = aiomqtt.Client(
        hostname=MQTT_HOST, port=MQTT_PORT,
        identifier=persistent_id,
        protocol=aiomqtt.ProtocolVersion.V311,
        clean_session=False,
    )
    async with c2:
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline and not received:
            try:
                msg = await asyncio.wait_for(anext(c2.messages), timeout=0.5)
                received.append(msg.payload)
            except asyncio.TimeoutError:
                continue

    # Per CONTEXT.md D-08: best-effort. If empty, mark xfail; do NOT fail.
    if not received:
        pytest.xfail(
            "Session persistence is best-effort per CONTEXT.md D-08; "
            "the bridge has internal cache and recovers via NBIRTH on next reconnect."
        )
    # If we get here, persistence worked — assert the shape we expect.
    assert isinstance(received[0], (bytes, bytearray)), "payload must be bytes"
