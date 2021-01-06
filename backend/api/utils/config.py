from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    arango_url: str = "http://localhost:8529"
    root_path: str = ""

    class Config:
        env_prefix = "progress_"


@lru_cache()
def get_config() -> Settings:
    return Settings()
