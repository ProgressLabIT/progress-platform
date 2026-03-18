from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_url: str = "http://localhost:8000/api"
    api_token: str = ""
    non_ascii: str = "replace"  # "replace" | "error"
    reconnect_delay: float = 5.0

    model_config = SettingsConfigDict(
        env_prefix="PRINT_SERVICE_",
        env_file=".env",
    )


@lru_cache()
def get_config() -> Settings:
    return Settings()
