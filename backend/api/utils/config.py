from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
  arango_url: str = "http://localhost:8529" # use default when running standalone containers
  api_root_path: str = "/api"
  media_path: str = "/media"
  db_name: str = "PROGRESS_TEST"
  api_db_username: str = "root" # use default when running standalone containers
  api_db_pwd: str = ""
  kafka_bootstrap_server: str = "localhost:9000"
  kafka_group_id: str = "fooo"
  kafka_session_to_ms: int = 10000

  model_config = SettingsConfigDict(
    env_prefix = "progress_",
    secrets_dir = "/run/secrets"
  )
  """
  Provided as docker secrets:
  - progress_api_db_pwd
  - progress_admin_pwd
  - progress_jwt_secret
  """


@lru_cache()
def get_config() -> Settings:
  return Settings()
