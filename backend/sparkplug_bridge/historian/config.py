"""Historian ingester configuration via pydantic-settings.

Sibling to backend/sparkplug_bridge/config.py:BridgeSettings — same image (D-04)
but distinct env-var surface so neither process pollutes the other's settings.
`extra="ignore"` is the contract (RESEARCH §Standard Stack — Sibling HistorianSettings).

Env-var prefix: PROGRESS_  (matches BridgeSettings + backend/api/utils/config.py)
Secrets read from /run/secrets (Docker Swarm pattern, ADR-0006).
"""
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent / ".env"


class HistorianSettings(BaseSettings):
    nats_url: str = "nats://broker:4222"

    historian_db_url: str = Field(
        default="postgresql://postgres:postgres@workflow-db:5432/progress_historian",
        alias="PROGRESS_HISTORIAN_DB_URL",
    )
    historian_admin_url: str = Field(
        default="postgresql://postgres:postgres@workflow-db:5432/postgres",
        alias="PROGRESS_HISTORIAN_ADMIN_URL",
    )
    historian_db_name: str = Field(
        default="progress_historian",
        alias="PROGRESS_HISTORIAN_DB_NAME",
    )

    historian_batch_size: int = Field(
        default=500, alias="PROGRESS_HISTORIAN_BATCH_SIZE",
    )
    historian_flush_ms: int = Field(
        default=100, alias="PROGRESS_HISTORIAN_FLUSH_MS",
    )

    historian_heartbeat_interval_sec: float = Field(
        default=5.0, alias="PROGRESS_HISTORIAN_HEARTBEAT_INTERVAL_SEC",
    )

    model_config = SettingsConfigDict(
        env_prefix="progress_",
        secrets_dir="/run/secrets",
        env_file=_ENV_FILE,
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache()
def get_historian_config() -> HistorianSettings:
    return HistorianSettings()
