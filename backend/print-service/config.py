from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_url: str = "http://localhost:8000/api"
    username: str = "print_service"
    api_password: str = "1234"
    non_ascii: str = "replace"  # "replace" | "error"
    reconnect_delay: float = 5.0

    model_config = SettingsConfigDict(
        env_prefix="PRINT_SERVICE_",
        env_file=".env",
        secrets_dir="/run/secrets",
    )


@lru_cache()
def get_config() -> Settings:
    return Settings()
