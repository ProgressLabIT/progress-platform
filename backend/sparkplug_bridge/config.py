"""Bridge service configuration via pydantic-settings.

Env-var prefix: PROGRESS_  (matches backend/api/utils/config.py)
Secrets read from /run/secrets (Docker Swarm pattern, ADR-0006).
"""
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent / ".env"


class BridgeSettings(BaseSettings):
    # NATS connection (used via backend/api/utils/nats_client.py).
    nats_url: str = "nats://broker:4222"

    # MQTT 3.1.1 endpoint (the NATS MQTT side).
    # Format: tcp://<host>:<port>
    mqtt_url: str = "tcp://broker:1883"
    mqtt_client_id: str = "sparkplug-bridge-1"

    # Heartbeat cadence — D-09 default 5s; D-10 healthcheck `timeout: 12s` and `interval: 10s`
    # leave headroom around this value.
    bridge_heartbeat_interval_sec: float = 5.0

    # D-04 — Primary-host STATE handshake host id. Stable across container
    # restarts so retained STATE survives. Multi-bridge future-proof.
    bridge_host_id: str = Field(default="progress-bridge", alias="PROGRESS_BRIDGE_HOST_ID")

    # D-07 — Suspect-cap thresholds. When seq-gap or alias-miss count reaches
    # `gap_tolerance` within a rolling `gap_window_sec` window, bridge flips
    # the offending session to offline with reason="bridge_timeout".
    gap_tolerance: int = Field(default=5, alias="PROGRESS_BRIDGE_GAP_TOLERANCE")
    gap_window_sec: float = Field(default=60.0, alias="PROGRESS_BRIDGE_GAP_WINDOW_SEC")

    # Phase 5 (ADR-0010) — pump-anomaly automation HTTP POST target + JWT path.
    # env_prefix="progress_" prepends PROGRESS_ at lookup time, so the field
    # names here MUST NOT include "progress_" — otherwise pydantic-settings
    # looks for PROGRESS_PROGRESS_API_BASE_URL (doubled prefix, never matches).
    # These map to PROGRESS_API_BASE_URL and PROGRESS_SPARKPLUG_TOKEN_PATH.
    api_base_url: str = "http://api:8000/api"
    sparkplug_token_path: str = "/opt/progress/config/.sparkplug-token"

    model_config = SettingsConfigDict(
        env_prefix="progress_",
        secrets_dir="/run/secrets",
        env_file=_ENV_FILE,
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def mqtt_host(self) -> str:
        # tcp://broker:1883 -> 'broker'
        return self.mqtt_url.split("://", 1)[-1].split(":", 1)[0]

    @property
    def mqtt_port(self) -> int:
        # tcp://broker:1883 -> 1883
        return int(self.mqtt_url.split(":")[-1])


@lru_cache()
def get_config() -> BridgeSettings:
    return BridgeSettings()
