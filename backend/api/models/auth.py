from datetime import datetime, timedelta
from dateutil import tz
from enum import Enum

from fastapi import Form
from pydantic import BaseModel, Field

from models.base_models import ArangoDocument, FlexModel
from models.org import UserPreferences


class ConsumerType(str, Enum):
  PROGRESS_APP = 'app'
  EQUIPMENT = 'equipment'
  USER = 'user'
  THIRD_PARTY_SW = '3psw'


class TokenContext(str, Enum):
  JOB = "job"
  USER_SESSION = "session"
  PASSWORD_RESET = 'pwd_reset'
  API = "api"


class TokenRecord(ArangoDocument):
  signature: str
  revoked: bool = False
  issued_to: str
  issued_at: datetime
  expires_at: datetime
  context: str | None = None
  description: str | None = None


class Scope(str, Enum):
  ADMIN_USER_WRITE: 'admin.user'
  OPERATOR: 'operator'
  LIBRARY_READ: 'lib:r'
  LIBRARY_WRITE: 'lib:w'
  PRODUCTION_READ: 'prod:r'
  PRODUCTION_WRITE: 'prod:w'


class TokenData(FlexModel):
  token_key: str = Field(..., alias="jti")
  consumer_key: str = Field(..., alias="sub")
  consumer_type: ConsumerType = Field(ConsumerType.USER, alias="ctyp")
  issued_at: datetime = Field(..., alias="iat")
  expires_at: datetime | None = Field(..., alias="exp")
  context: TokenContext = Field(..., alias="ctx")
  # audience: str | None = Field(None, alias="aud") # identify third party apps
  # issuer: str | None = Field(None, alias="iss") # url of server


class AuthResponse(BaseModel):
  action: str
  user_key: str


class UserSession(ArangoDocument):
  active: bool
  user_key: str
  token_key: str
  login_at: datetime = datetime.now(tz.UTC)
  logout_at: datetime | None = None
  scope: str
  name: str | None = None
  surname: str | None = None

class NewSessionData(BaseModel):
  session_key: str
  user_key: str
  name: str | None = None
  surname: str | None = None
  scope: str
  preferences: UserPreferences = UserPreferences()
  timeout: timedelta = timedelta(minutes=30)

class GrantType(str, Enum):
  AUTHORIZATION_CODE: 'authorization_code'
  PASSWORD: 'password'


class ConsumerCredentials(BaseModel):
  username: str = Form(...)
  password: str = Form(...)
  # auth_code: str | None = None
  # grant_type: GrantType = Form(None)
