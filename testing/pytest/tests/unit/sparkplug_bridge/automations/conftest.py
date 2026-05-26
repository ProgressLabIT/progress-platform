"""Phase 5 unit-of-work fixtures for the pump-anomaly automation.

Per ADR-0010 + 05-RESEARCH.md §Validation Architecture.
Conftest depth-6 from repo root:
  testing/pytest/tests/unit/sparkplug_bridge/automations/conftest.py
                                                         [0]
                                                  [1]
                                           [2]
                                     [3]
                             [4]
                     [5]
  [6] = repo root
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
_BACKEND_ROOT = _REPO_ROOT / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

import httpx
import pytest


@pytest.fixture
def tmp_token_file(tmp_path):
    """JWT bearer file at a tmp path (mode 0600 for parity with /opt/progress/config)."""
    f = tmp_path / ".sparkplug-token"
    f.write_text("FAKE_JWT_FOR_TESTS")
    f.chmod(0o600)
    return str(f)


@pytest.fixture
def captured_requests():
    """List into which the MockTransport handler appends each request."""
    return []


@pytest.fixture
def mock_transport(captured_requests):
    """httpx.MockTransport that records calls and returns 200 by default.

    Matches the API's success-shape (issue_key in detail.message);
    mirrors backend/api/endpoints/traceability.py:45-71 response.
    """
    def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(
            200,
            json={"detail": {"message": "Issue created", "issue_key": "ISS-FAKE-1"}},
        )
    return httpx.MockTransport(handler)


@pytest.fixture
def automation_factory(tmp_token_file, monkeypatch, mock_transport):
    """Build a PumpAnomalyAutomation wired to the MockTransport.

    Patches httpx.AsyncClient inside pump_anomaly.py so the per-fire
    AsyncClient gets our MockTransport without modifying production code.

    Note: pump_anomaly.py does not exist until Plan 03 lands. Tests
    that consume this fixture will fail at import time until then --
    that is expected; this fixture is part of Wave 0 scaffolding.
    """
    # Defer the import -- Plan 03 lands the module; this fixture only
    # imports it when actually invoked by a test.
    from sparkplug_bridge.automations.pump_anomaly import PumpAnomalyAutomation

    real_client = httpx.AsyncClient

    def patched_client(*args, **kwargs):
        kwargs["transport"] = mock_transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr(
        "sparkplug_bridge.automations.pump_anomaly.httpx.AsyncClient",
        patched_client,
    )

    def make(api_base_url: str = "http://api:8000/api") -> PumpAnomalyAutomation:
        return PumpAnomalyAutomation(
            api_base_url=api_base_url,
            token_path=tmp_token_file,
        )

    return make
