"""WEDGE-DEMO-05c — pump-anomaly e2e regression test.

Drives PumpAnomalyAutomation through a realistic dwell-cross-latch cycle
using ADR-0002-shaped envelopes and an httpx.MockTransport. Lives in the
integration suite because it asserts the cross-module contract; live API
+ real ArangoDB verification is owned by 05-VERIFICATION.md (May 14
rehearsal runbook), NOT pytest.

Run via: pytest -m integration tests/integration/sparkplug_session/test_pump_anomaly_e2e.py
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import httpx
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
_BACKEND_ROOT = _REPO_ROOT / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

pytestmark = pytest.mark.integration


def _payload(value, name: str = "Vibration") -> dict:
    return {
        "schema_version": 1,
        "ts_utc_ms": 0,
        "source_ts_utc_ms": 0,
        "group": "plant1",
        "edge": "edge1",
        "device": "pump3",
        "bd_seq": 1,
        "seq": 1,
        "kind": "metric.data",
        "name": name,
        "alias": 1,
        "type": "Float",
        "value": value,
        "quality": "good",
    }


@pytest.fixture
def captured():
    return []


@pytest.fixture
def transport(captured):
    def handler(request):
        captured.append(request)
        return httpx.Response(
            200,
            json={"detail": {"message": "Issue created", "issue_key": "ISS-FAKE-1"}},
        )
    return httpx.MockTransport(handler)


@pytest.fixture
def token_file(tmp_path):
    f = tmp_path / ".sparkplug-token"
    f.write_text("E2E_FAKE_JWT")
    f.chmod(0o600)
    return str(f)


async def test_full_dwell_cross_then_latch(transport, captured, token_file, monkeypatch):
    """E2E: 5-s dwell cross -> fire -> 60-s latch suppresses re-fire.

    Compresses LATCH_SECONDS to 0.5 (NOT 0 -- preserve "latch DOES exist" intent)
    and DWELL_SECONDS to 0.5 so the test runs in ~1 second.
    """
    from sparkplug_bridge.automations import pump_anomaly
    monkeypatch.setattr(pump_anomaly, "DWELL_SECONDS", 0.5)
    monkeypatch.setattr(pump_anomaly, "LATCH_SECONDS", 0.5)

    # Patch AsyncClient binding to use our MockTransport.
    real_client = httpx.AsyncClient

    def patched_client(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr(
        "sparkplug_bridge.automations.pump_anomaly.httpx.AsyncClient",
        patched_client,
    )

    a = pump_anomaly.PumpAnomalyAutomation(
        api_base_url="http://api:8000/api",
        token_path=token_file,
    )

    # Phase 1 — dwell cross. Sustained > THRESHOLD for > DWELL_SECONDS.
    await a.on_metric_data(_payload(120.0))   # arms _first_violation_ts
    await asyncio.sleep(0.6)                   # past 0.5s dwell
    await a.on_metric_data(_payload(120.0))   # fire #1
    assert len(captured) == 1, "first sustained crossing must fire exactly once"

    # Phase 2 — within latch window, sustained crossing MUST NOT re-fire.
    await a.on_metric_data(_payload(120.0))   # rearm
    await asyncio.sleep(0.05)                  # well under 0.5s latch
    await a.on_metric_data(_payload(120.0))   # blocked by latch
    assert len(captured) == 1, "latch must suppress re-fire within window"

    # Phase 3 — wait past latch; another sustained crossing fires again.
    await asyncio.sleep(0.6)                   # past 0.5s latch
    await a.on_metric_data(_payload(120.0))   # rearm
    await asyncio.sleep(0.6)                   # past 0.5s dwell
    await a.on_metric_data(_payload(120.0))   # fire #2
    assert len(captured) == 2, "post-latch crossing must fire again"

    # Wire-shape spot-check: every captured request is the canonical flat shape.
    for req in captured:
        assert req.method == "POST"
        assert str(req.url) == "http://api:8000/api/event"
        assert req.headers["authorization"] == "Bearer E2E_FAKE_JWT"
        doc = json.loads(req.read())
        assert doc["event_type"] == "ISSUE_CREATED"
        assert "issue_data" in doc
        assert "info" not in doc  # RESEARCH §Pitfall 2
        assert doc["issue_data"]["linked_to"] == [
            {"type": "work_order", "key": "WO-DEMO-001"},
            {"type": "phase", "key": "PH-DEMO-001"},
        ]


async def test_envelope_with_uppercase_name_matches(transport, captured, token_file, monkeypatch):
    """RESEARCH §Pitfall 5 — payload "name": "Vibration" (mixed-case)
    must match TARGET_METRIC_ID; subject-slug "vibration" must NOT.
    """
    from sparkplug_bridge.automations import pump_anomaly
    monkeypatch.setattr(pump_anomaly, "DWELL_SECONDS", 0)
    monkeypatch.setattr(pump_anomaly, "LATCH_SECONDS", 60)

    real_client = httpx.AsyncClient

    def patched_client(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr(
        "sparkplug_bridge.automations.pump_anomaly.httpx.AsyncClient",
        patched_client,
    )

    a = pump_anomaly.PumpAnomalyAutomation(
        api_base_url="http://api:8000/api",
        token_path=token_file,
    )
    # Mixed-case "Vibration" -- must fire.
    await a.on_metric_data(_payload(120.0, name="Vibration"))
    await a.on_metric_data(_payload(120.0, name="Vibration"))
    assert len(captured) == 1
