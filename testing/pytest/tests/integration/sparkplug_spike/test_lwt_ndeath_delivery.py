"""Spike: NDEATH (LWT) is delivered when the simulator container dies uncleanly.

Validates INFRA-02 LWT primitive (CONTEXT.md D-08 fallback tripwire):
  - If this test fails, fall back to HiveMQ CE 2025.5 per ADR-0001.

Run with:
  uv run pytest tests/integration/sparkplug_spike/test_lwt_ndeath_delivery.py -x -v
"""
import asyncio
import time

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_lwt_ndeath_delivery(mqtt_subscriber, resolve_container):
    """Given the simulator is publishing,
    When we kill its container with SIGKILL (unclean disconnect),
    Then within 5 seconds an NDEATH payload arrives on spBv1.0/<group>/NDEATH/<edge>.
    """
    # Allow the subscriber to subscribe + the simulator to publish at least one frame
    # before we kill the simulator. Without this, the simulator might not have established
    # its session yet, and the broker has nothing to LWT.
    await asyncio.sleep(2.0)

    # Force unclean disconnect.
    container = resolve_container("progress_sparkplug_sim")
    container.kill(signal="SIGKILL")

    # Poll for arrival within 5s.
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline and not mqtt_subscriber:
        await asyncio.sleep(0.1)

    assert mqtt_subscriber, "NDEATH not delivered within 5s of unclean disconnect"
    topics = {t for t, _ in mqtt_subscriber}
    assert any(t.startswith("spBv1.0/plant1/NDEATH/") for t in topics), (
        f"expected plant1 NDEATH topic, got: {topics}"
    )
