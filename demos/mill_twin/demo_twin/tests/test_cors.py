"""CORS narrowing tests for demo_twin (Phase 5, B-04).

Tests verify that:
1. TwinSettings.cors_allow_origins defaults to the two demo origins (not ["*"]).
2. Setting TWIN_CORS_ALLOW_ORIGINS to a comma-separated string parses to a list.
3. The FastAPI app's CORSMiddleware echoes an allowed origin but not a disallowed one.

Design: pure-Python, no broker.  The lifespan connects NATS on startup — TestClient
used without entering the lifespan context (use client.app directly, not the
contextmanager form) so the NATS connect is never triggered.
"""
import os
import importlib

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fresh_settings(**env_overrides):
    """Return a fresh TwinSettings built from the given env vars.

    Clears any cached instance so each test is independent.
    """
    import demo_twin.config as cfg_mod
    cfg_mod.get_config.cache_clear()
    original = {}
    # Set supplied overrides and remember what was there before.
    for k, v in env_overrides.items():
        original[k] = os.environ.get(k)
        os.environ[k] = v
    try:
        return cfg_mod.get_config()
    finally:
        # Restore original env state.
        for k, orig_v in original.items():
            if orig_v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = orig_v
        cfg_mod.get_config.cache_clear()


def _build_app():
    """Import (or reimport) main to get a fresh app instance.

    Reloads so that the module-level `settings = get_config()` picks up the
    current environment without the lru_cache carrying over between tests.
    """
    import demo_twin.config as cfg_mod
    cfg_mod.get_config.cache_clear()
    import demo_twin.main as main_mod
    importlib.reload(main_mod)
    return main_mod.app


# ---------------------------------------------------------------------------
# Test 1: default cors_allow_origins does NOT contain "*"
# ---------------------------------------------------------------------------

def test_default_cors_origins_are_not_wildcard():
    """TwinSettings().cors_allow_origins defaults to the two demo origins, not ['*']."""
    settings = _fresh_settings()
    assert "*" not in settings.cors_allow_origins, (
        "Default cors_allow_origins must not be ['*'] — got: %s" % settings.cors_allow_origins
    )
    assert "http://progress.localhost" in settings.cors_allow_origins
    assert "http://localhost:9000" in settings.cors_allow_origins


# ---------------------------------------------------------------------------
# Test 2: comma-separated env string parses to list
# ---------------------------------------------------------------------------

def test_cors_origins_env_comma_split():
    """TWIN_CORS_ALLOW_ORIGINS='http://a,http://b' parses to ['http://a', 'http://b']."""
    settings = _fresh_settings(TWIN_CORS_ALLOW_ORIGINS="http://a,http://b")
    assert settings.cors_allow_origins == ["http://a", "http://b"]


# ---------------------------------------------------------------------------
# Test 3: CORS middleware echoes allowed origin, rejects disallowed
# ---------------------------------------------------------------------------

def test_cors_middleware_allows_and_rejects():
    """CORSMiddleware echoes an allowed origin; a disallowed origin is not echoed."""
    app = _build_app()
    client = TestClient(app, raise_server_exceptions=False)

    # Allowed origin — OPTIONS preflight should return ACAO header echoing the origin.
    allowed = "http://progress.localhost"
    resp = client.options(
        "/setpoints",
        headers={
            "Origin": allowed,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    acao = resp.headers.get("access-control-allow-origin", "")
    assert acao == allowed, (
        "Expected ACAO header to echo allowed origin '%s', got '%s'" % (allowed, acao)
    )

    # Disallowed origin — should NOT echo the origin.
    disallowed = "http://evil.example.com"
    resp2 = client.options(
        "/setpoints",
        headers={
            "Origin": disallowed,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    acao2 = resp2.headers.get("access-control-allow-origin", "")
    assert acao2 != disallowed, (
        "Disallowed origin '%s' must not appear in ACAO header, got '%s'" % (disallowed, acao2)
    )


# ---------------------------------------------------------------------------
# Test 4: empty string env var falls back to default origins (not empty list)
# ---------------------------------------------------------------------------

def test_cors_origins_empty_string_falls_back_to_default():
    """TWIN_CORS_ALLOW_ORIGINS='' must return the default list, not []."""
    settings = _fresh_settings(TWIN_CORS_ALLOW_ORIGINS="")
    assert settings.cors_allow_origins, "cors_allow_origins must not be empty"
    assert "http://progress.localhost" in settings.cors_allow_origins


# ---------------------------------------------------------------------------
# Test 5: wildcard is rejected in both comma-separated and JSON forms
# ---------------------------------------------------------------------------

def test_cors_origins_wildcard_rejected():
    """TWIN_CORS_ALLOW_ORIGINS='*' and '["*"]' must raise ValueError."""
    import pytest
    with pytest.raises(Exception):
        _fresh_settings(TWIN_CORS_ALLOW_ORIGINS="*")

    with pytest.raises(Exception):
        _fresh_settings(TWIN_CORS_ALLOW_ORIGINS='["*"]')
