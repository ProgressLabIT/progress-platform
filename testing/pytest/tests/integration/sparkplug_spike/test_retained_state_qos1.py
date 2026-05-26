"""Spike: retained STATE survives a fresh subscriber's connect.

Validates INFRA-02 retained-STATE primitive (D-08 fallback tripwire):
  - If this test fails, fall back to HiveMQ CE 2025.5 per ADR-0001.

NOTE: ADR-0007's simulator publishes its own STATE retained message at startup.
Per RESEARCH §Example G, the spike uses that retained message to assert the
broker's retained-message store works.
"""
import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_retained_state_qos1(mqtt_state_subscriber):
    """Given the simulator publishes a retained STATE message at startup,
    When a fresh subscriber connects later (clean_session=True),
    Then the broker delivers the retained STATE within 2 seconds.
    """
    assert mqtt_state_subscriber, (
        "retained STATE not delivered to fresh subscriber within 2s — "
        "this triggers the D-08 fallback to HiveMQ CE 2025.5"
    )
    topic, _ = mqtt_state_subscriber[0]
    assert topic.startswith("spBv1.0/STATE/"), (
        f"expected spBv1.0/STATE/* topic, got {topic!r}"
    )
