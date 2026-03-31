from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
  arango_url: str = "http://localhost:8529" # use default when running standalone containers
  api_root_path: str = "/api"
  media_path: str = "/media"
  db_name: str = "PROGRESS_TEST"
  webapp_url: str = "http://localhost:9000"
  api_db_username: str = "root" # use default when running standalone containers
  api_db_pwd: str = ""
  jwt_secret: str = ""
  cors_allowed_origins: list[str] = ["*"]
  nats_url: str = "nats://broker:4222"

  model_config = SettingsConfigDict(
    env_prefix = "progress_",
    secrets_dir = "/run/secrets",
    env_file = ".env"
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
