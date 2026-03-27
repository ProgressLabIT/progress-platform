from functools import lru_cache
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent / ".env"


class Settings(BaseSettings):
    api_url: str | None = "http://localhost:8000/api"
    username: str | None = "print_service"
    api_password: str | None = "1234"
    non_ascii: Literal["replace", "error"] | None = "replace"
    reconnect_delay: float | None = 5.0
    printer_key: str | None = None  # PROGRESS_PRINT_SERVICE_PRINTER_KEY

    model_config = SettingsConfigDict(
        env_prefix="PROGRESS_PRINT_SERVICE_",
        env_file=_ENV_FILE,
        secrets_dir="/run/secrets",
    )


@lru_cache()
def get_config() -> Settings:
    return Settings()
