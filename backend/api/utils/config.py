import os
from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    arango_url: str = "http://localhost:8529" # use default when running standalone containers
    api_root_path: str = "/api"
    media_path: str = "/media"
    db_name: str = "PROGRESS_TEST"
    api_db_username: str = "root" # use default when running standalone containers
    api_db_pwd: str = ""

    class Config:
        env_prefix = "progress_"
        secrets_dir = "/run/secrets"
        '''
        Provided as docker secrets:
        - progress_jwt_secret
        - progress_api_db_password
        '''


@lru_cache()
def get_config() -> Settings:
    return Settings()
