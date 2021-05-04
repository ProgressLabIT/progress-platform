import os
from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    arango_url: str = "http://localhost:8529"
    api_root_path: str = ""
    openapi_root_path: str = ""
    media_path: str = "/media"
    db_name: str = "PROGRESS_TEST"
    api_db_username: str = "root"
    # db password file path via docker secrets
    api_db_pwd_file: str = ""

    class Config:
        env_prefix = "progress_"


@lru_cache()
def get_config() -> Settings:
    return Settings()
