from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# TODO: OBJECT STORAGE MIGRATION - Add object storage configuration settings
# Need to add: object_storage_provider, bucket_name, access_key, secret_key, endpoint_url, region

class Settings(BaseSettings):
  arango_url: str = "http://localhost:8529" # use default when running standalone containers
  api_root_path: str = "/api"
  media_path: str = "/media"  # TODO: OBJECT STORAGE MIGRATION - Replace with object storage bucket configuration
  db_name: str = "PROGRESS_TEST"
  webapp_url: str = "http://localhost:9000"
  api_db_username: str = "root" # use default when running standalone containers
  api_db_pwd: str = ""
  cors_allowed_origins: list[str] = ["*"]
  kafka_bootstrap_server: str = "broker:19092"
  kafka_group_id: str = "backend"
  kafka_client_id_consumer: str = "backend-service-consumer"
  kafka_client_id_producer: str = "backend-service-producer"
  kafka_session_to_ms: int = 10000

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
