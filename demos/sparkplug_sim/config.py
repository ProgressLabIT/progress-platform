"""Simulator service configuration via pydantic-settings.

Same env-var prefix and secrets path as the bridge — uses the bare PROGRESS_*
namespace per CONTEXT.md `code_context.Established Patterns`.
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent / ".env"


class SimulatorSettings(BaseSettings):
    # NATS connection — used only by the heartbeat path (sim publishes to MQTT,
    # not native NATS, but heartbeats reuse the existing nats_client helper).
    nats_url: str = "nats://broker:4222"

    # MQTT 3.1.1 endpoint (NATS MQTT side or HiveMQ fallback per D-08).
    mqtt_url: str = "tcp://broker:1883"

    # Heartbeat cadence — D-09 default 5s.
    sim_heartbeat_interval_sec: float = 5.0

    # Scenario knob — start offset in seconds. 0 = start immediately. Useful
    # for rehearsals where the operator wants to delay the first NBIRTH.
    scenario_start_offset_sec: float = 0.0

    # Scenario parameters file (per ADR-0007 Amendment 2026-04-29). Default
    # resolves to the package-relative scenario.yaml. Override via
    # PROGRESS_SIM_SCENARIO_PATH at deploy time to bind-mount a tweaked file.
    sim_scenario_path: Path = Path(__file__).resolve().parent / "scenario.yaml"

    model_config = SettingsConfigDict(
        env_prefix="progress_",
        secrets_dir="/run/secrets",
        env_file=_ENV_FILE,
        extra="ignore",
    )

    @property
    def mqtt_host(self) -> str:
        return self.mqtt_url.split("://", 1)[-1].split(":", 1)[0]

    @property
    def mqtt_port(self) -> int:
        return int(self.mqtt_url.split(":")[-1])


@lru_cache()
def get_config() -> SimulatorSettings:
    return SimulatorSettings()
