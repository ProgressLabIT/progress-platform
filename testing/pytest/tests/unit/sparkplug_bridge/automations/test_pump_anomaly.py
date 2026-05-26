"""WEDGE-DEMO-01..06 — pump-anomaly automation unit tests.

Per ADR-0010 + 05-RESEARCH.md §Validation Architecture. Drives
PumpAnomalyAutomation directly; mocks httpx via MockTransport (conftest).
"""
import asyncio
import json

import pytest

from sparkplug_bridge.automations.pump_anomaly import (
    DWELL_SECONDS,
    LATCH_SECONDS,
    LINKED_TO,
    TARGET_METRIC_ID,
    THRESHOLD,
    PumpAnomalyAutomation,
)


def _payload(
    value,
    name: str = "Vibration",
    group: str = "plant1",
    edge: str = "edge1",
    device: str = "pump3",
) -> dict:
    """ADR-0002 metric.data envelope shape (publisher.py:108-122 source)."""
    return {
        "schema_version": 1,
        "ts_utc_ms": 0,
        "source_ts_utc_ms": 0,
        "group": group,
        "edge": edge,
        "device": device,
        "bd_seq": 1,
        "seq": 1,
        "kind": "metric.data",
        "name": name,
        "alias": 1,
        "type": "Float",
        "value": value,
        "quality": "good",
    }


# ---------------- WEDGE-DEMO-01 — constants ----------------

def test_constants_match_adr0010():
    assert TARGET_METRIC_ID == "plant1.edge1.pump3.Vibration"
    assert THRESHOLD == 100.0
    assert DWELL_SECONDS == 5
    assert LATCH_SECONDS == 60
    assert LINKED_TO == [
        {"type": "work_order", "key": "WO-DEMO-001"},
        {"type": "phase", "key": "PH-DEMO-001"},
    ]


# ---------------- WEDGE-DEMO-02 — token-from-file ----------------

def test_token_loaded_from_file(automation_factory):
    a = automation_factory()
    assert a._token == "FAKE_JWT_FOR_TESTS"


def test_missing_token_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        PumpAnomalyAutomation(
            api_base_url="http://api:8000/api",
            token_path=str(tmp_path / "does-not-exist"),
        )


# ---------------- WEDGE-DEMO-03 — POST shape ----------------

async def test_fire_post_shape(automation_factory, captured_requests, monkeypatch):
    a = automation_factory()
    monkeypatch.setattr(
        "sparkplug_bridge.automations.pump_anomaly.DWELL_SECONDS", 0
    )
    await a.on_metric_data(_payload(102.4))   # arms _first_violation_ts
    await a.on_metric_data(_payload(102.4))   # past dwell -> fire
    assert len(captured_requests) == 1
    req = captured_requests[0]
    assert req.method == "POST"
    assert str(req.url) == "http://api:8000/api/event"
    assert req.headers["authorization"] == "Bearer FAKE_JWT_FOR_TESTS"
    doc = json.loads(req.read())
    assert doc["event_type"] == "ISSUE_CREATED"
    # FLAT shape — issue_data at top level. RESEARCH §Pitfall 2.
    assert "issue_data" in doc
    assert "info" not in doc, (
        "ADR-0010 sketch's nested 'info' shape would silently drop issue_data"
    )
    # user_key + user_session_key ARE in the body — they're stored on the
    # Event for downstream UI joins (history tab). NOT decoded from the JWT;
    # operator-configured per environment via PUMP_ANOMALY_USER_KEY /
    # PUMP_ANOMALY_USER_SESSION_KEY.
    assert "user_key" in doc
    assert "user_session_key" in doc
    # created_by IS required by IssueWithLinks — must match the JWT's user
    # but is configured explicitly (no JWT decoding by the bridge).
    assert doc["issue_data"]["created_by"].startswith("User/")
    assert doc["issue_data"]["critical"] is False
    assert "issue_type_key" in doc["issue_data"]
    assert doc["issue_data"]["title"].startswith("Pump 3 vibration anomaly")
    assert doc["source_metric"] == "pump-anomaly-automation"


# ---------------- WEDGE-DEMO-04 — linked_to targets ----------------

async def test_linked_to_targets_demo_wo_and_phase(
    automation_factory, captured_requests, monkeypatch
):
    a = automation_factory()
    monkeypatch.setattr(
        "sparkplug_bridge.automations.pump_anomaly.DWELL_SECONDS", 0
    )
    await a.on_metric_data(_payload(120.0))
    await a.on_metric_data(_payload(120.0))
    doc = json.loads(captured_requests[0].read())
    assert doc["issue_data"]["linked_to"] == [
        {"type": "work_order", "key": "WO-DEMO-001"},
        {"type": "phase", "key": "PH-DEMO-001"},
    ]


# ---------------- WEDGE-DEMO-05a — dwell suppresses 4-s spike ----------------

async def test_short_spike_under_dwell_does_not_fire(
    automation_factory, captured_requests
):
    # Use real DWELL_SECONDS = 5; emit 4 in-violation calls 1s apart.
    # 4 s elapsed < 5 s dwell -> no fire. Then drop below threshold.
    a = automation_factory()
    for _ in range(4):
        await a.on_metric_data(_payload(120.0))
        await asyncio.sleep(1.0)
    await a.on_metric_data(_payload(22.0))
    assert captured_requests == []


# ---------------- WEDGE-DEMO-05a (variant) — non-violation resets streak ----

async def test_non_violation_resets_first_violation(
    automation_factory, captured_requests, monkeypatch
):
    monkeypatch.setattr(
        "sparkplug_bridge.automations.pump_anomaly.DWELL_SECONDS", 0
    )
    a = automation_factory()
    await a.on_metric_data(_payload(120.0))   # arm
    await a.on_metric_data(_payload(22.0))    # drop -> reset
    # Should NOT fire on the next violation pair from a fresh arm:
    # Single in-violation alone (after reset) is arming, not firing.
    await a.on_metric_data(_payload(120.0))   # rearm only
    assert captured_requests == []


# ---------------- WEDGE-DEMO-05b — latch suppresses re-fire ----------------

async def test_latch_blocks_second_fire_within_window(
    automation_factory, captured_requests, monkeypatch
):
    monkeypatch.setattr(
        "sparkplug_bridge.automations.pump_anomaly.DWELL_SECONDS", 0
    )
    # LATCH_SECONDS stays at 60 — this loop completes in ms.
    a = automation_factory()
    await a.on_metric_data(_payload(120.0))   # arm
    await a.on_metric_data(_payload(120.0))   # fire #1
    await a.on_metric_data(_payload(120.0))   # rearm
    await a.on_metric_data(_payload(120.0))   # blocked by latch
    assert len(captured_requests) == 1


# ---------------- WEDGE-DEMO-06 — kill switch ----------------

async def test_env_var_disables(
    automation_factory, captured_requests, monkeypatch
):
    monkeypatch.setenv("SPARKPLUG_AUTOMATIONS_ENABLED", "false")
    monkeypatch.setattr(
        "sparkplug_bridge.automations.pump_anomaly.DWELL_SECONDS", 0
    )
    a = automation_factory()
    await a.on_metric_data(_payload(120.0))
    await a.on_metric_data(_payload(120.0))
    assert captured_requests == []


# ---------------- WEDGE-DEMO-01 (case-preserving metric_id) -------------

async def test_subject_slug_case_does_not_match(
    automation_factory, captured_requests, monkeypatch
):
    # RESEARCH §Pitfall 5 — payload uses lowercase "vibration" (subject-slug
    # form). _id_from_envelope is case-preserving; this MUST NOT match
    # TARGET_METRIC_ID and MUST NOT fire.
    monkeypatch.setattr(
        "sparkplug_bridge.automations.pump_anomaly.DWELL_SECONDS", 0
    )
    a = automation_factory()
    await a.on_metric_data(_payload(120.0, name="vibration"))
    await a.on_metric_data(_payload(120.0, name="vibration"))
    assert captured_requests == []


# ---------------- API failure tolerated ----------------

async def test_api_500_does_not_propagate(
    automation_factory, captured_requests, monkeypatch, mock_transport
):
    # Override transport handler to return 500.
    import httpx
    def handler_500(request):
        captured_requests.append(request)
        return httpx.Response(500, json={"detail": "boom"})
    # Re-monkeypatch the AsyncClient binding to use a 500-returning transport.
    bad_transport = httpx.MockTransport(handler_500)
    real_client = httpx.AsyncClient
    def patched_client(*args, **kwargs):
        kwargs["transport"] = bad_transport
        return real_client(*args, **kwargs)
    monkeypatch.setattr(
        "sparkplug_bridge.automations.pump_anomaly.httpx.AsyncClient",
        patched_client,
    )
    monkeypatch.setattr(
        "sparkplug_bridge.automations.pump_anomaly.DWELL_SECONDS", 0
    )
    a = automation_factory()
    await a.on_metric_data(_payload(120.0))
    # Second call MUST not raise. _fire's logging is verified by the
    # captured request shape (the 500 was received).
    await a.on_metric_data(_payload(120.0))
    assert len(captured_requests) == 1
    assert captured_requests[0].method == "POST"
