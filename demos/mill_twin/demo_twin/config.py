"""Demo-twin service configuration via pydantic-settings.

Env-var prefix: TWIN_
  TWIN_NATS_URL, TWIN_PUBLISH_INTERVAL_SEC, TWIN_RNG_SEED,
  TWIN_SOURCE, TWIN_HTTP_HOST, TWIN_HTTP_PORT, TWIN_LOG_LEVEL,
  TWIN_CORS_ALLOW_ORIGINS

All fields have sensible defaults so the service can start without any
environment setup (e.g. in tests that import main at module load without
a running broker).  NATS connection happens in the FastAPI lifespan, never
at import time.

No MQTT, JWT, or secrets fields — the twin is protocol-neutral (PUB-03).
"""
from functools import lru_cache
from pathlib import Path
from typing import Any, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent / ".env"

_DEFAULT_CORS_ORIGINS = "http://progress.localhost,http://localhost:9000"


class TwinSettings(BaseSettings):
    # NATS broker URL.  Default points at the compose service name.
    nats_url: str = "nats://broker:4222"

    # Physics loop cadence (seconds between ticks).  0.2 s = 5 Hz (PUB-01).
    publish_interval_sec: float = 0.2

    # Seeded RNG value used at startup and on POST /reset (TWIN-04 determinism).
    rng_seed: int = 0xDEADBEEF

    # Envelope source field value (RESEARCH discretion A2 / ADR-0013 §3.2 example).
    source: str = "demo-twin"

    # HTTP binding for uvicorn.
    http_host: str = "0.0.0.0"
    http_port: int = 8001

    # Logging level string passed to logging.basicConfig.
    log_level: str = "INFO"

    # B-04: CORS origins allowed to call the HTTP command endpoints. Defaults to the
    # Traefik-routed Progress host + the Quasar dev server. Replaces the Phase-4 "*".
    # Comma-separated in the env (TWIN_CORS_ALLOW_ORIGINS=http://a,http://b).
    # Union type ensures pydantic-settings tolerates JSON-parse failure on the raw
    # comma-separated string and passes it through to _split_origins unchanged.
    cors_allow_origins: Union[list[str], str] = ["http://progress.localhost", "http://localhost:9000"]

    @field_validator("rng_seed", mode="before")
    @classmethod
    def _parse_seed(cls, v: Any) -> int:
        # Accept hex ("0xDEADBEEF") or decimal env strings. Pydantic's native int
        # coercion is base-10 only, so a hex TWIN_RNG_SEED raises ValidationError
        # at import (get_config runs at module load) → worker never boots. int(v, 0)
        # honours the 0x prefix while still parsing plain decimal.
        if isinstance(v, str):
            return int(v.strip(), 0)
        return v

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _split_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            stripped = v.strip()
            # Empty string → fall back to the default origins rather than returning []
            # (an empty allow-list silently rejects every CORS preflight).
            if not stripped:
                return [o.strip() for o in _DEFAULT_CORS_ORIGINS.split(",") if o.strip()]
            # Accept a JSON array literal (e.g. '["http://a","http://b"]').
            if stripped.startswith("["):
                import json as _json
                try:
                    parsed = _json.loads(stripped)
                except ValueError:
                    # Malformed JSON → fall back to comma-split rather than crashing.
                    parsed = [o.strip() for o in stripped.split(",") if o.strip()]
                if "*" in parsed:
                    raise ValueError(
                        "Wildcard '*' is not permitted in TWIN_CORS_ALLOW_ORIGINS"
                    )
                return parsed
            origins = [o.strip() for o in stripped.split(",") if o.strip()]
            if "*" in origins:
                raise ValueError(
                    "Wildcard '*' is not permitted in TWIN_CORS_ALLOW_ORIGINS"
                )
            return origins
        # pydantic-settings pre-parses JSON arrays, so v may already be a list
        # here. Guard against wildcard in that path too.
        if isinstance(v, list) and "*" in v:
            raise ValueError(
                "Wildcard '*' is not permitted in TWIN_CORS_ALLOW_ORIGINS"
            )
        return v

    model_config = SettingsConfigDict(
        env_prefix="twin_",
        env_file=_ENV_FILE,
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache()
def get_config() -> TwinSettings:
    return TwinSettings()
