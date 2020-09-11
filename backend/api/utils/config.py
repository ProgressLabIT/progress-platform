from secrets import token_hex

from Pydantic import BaseSettings, DirectoryPath


class Settings(BaseSettings):
  TOKEN_KEY: str = 
  CUSTOMER_NAME: str
  DOMAIN_NAME: str
  CERT_FOLDER: DirectoryPath
