from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    arango_url: str = "http://localhost:8529"
    root_path: str = ""
    openapi_root_path: str = ""
    media_path: str = "/media"

    class Config:
        env_prefix = "progress_"


@lru_cache()
def get_config() -> Settings:
    return Settings()
