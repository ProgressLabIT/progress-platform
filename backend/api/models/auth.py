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
  SSE_TICKET = "sse_ticket"  # short-lived, topic-scoped, stateless


class SseTicketClaims(BaseModel):
  sub: str = Field(
    ...,
    description="Consumer key (ArangoDB _key of the User document) for whom the ticket was issued.",
    examples=["user42"],
  )
  topic: str = Field(
    ...,
    description="NATS / SSE topic the ticket grants access to (e.g. `user:user42` or `task`).",
    examples=["user:user42"],
  )
  ctx: str = Field(
    TokenContext.SSE_TICKET.value,
    description="Token context identifier — always `sse_ticket` for SSE tickets.",
    examples=["sse_ticket"],
  )
  iat: datetime = Field(
    ...,
    description="ISO 8601 UTC timestamp at which the ticket was issued.",
    examples=["2026-05-04T10:00:00Z"],
  )
  exp: datetime = Field(
    ...,
    description="ISO 8601 UTC timestamp at which the ticket expires.",
    examples=["2026-05-04T10:01:00Z"],
  )


class TokenRecord(ArangoDocument):
  signature: str = Field(
    ...,
    description="The base64-url-encoded signature segment of the JWT (third `.`-delimited part).",
    examples=["SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"],
  )
  revoked: bool = Field(
    False,
    description="Whether this token has been explicitly revoked. Revoked tokens are rejected on verification.",
    examples=[False],
  )
  issued_to: str = Field(
    ...,
    description="ArangoDB document ID (`User/<_key>`) of the entity this token was issued to.",
    examples=["User/user42"],
  )
  issued_at: datetime = Field(
    ...,
    description="UTC timestamp at which the token was issued.",
    examples=["2026-05-04T08:00:00Z"],
  )
  expires_at: datetime = Field(
    ...,
    description="UTC timestamp at which the token expires and will be rejected.",
    examples=["2026-05-05T08:00:00Z"],
  )
  context: str | None = Field(
    None,
    description="Token context string (e.g. `session`, `api`, `pwd_reset`, `sse_ticket`).",
    examples=["session"],
  )
  description: str | None = Field(
    None,
    description="Human-readable label for long-lived API tokens, set at issuance time.",
    examples=["CI pipeline token"],
  )


class Scope(str, Enum):
  ADMIN_USER_WRITE: 'admin.user'
  OPERATOR: 'operator'
  LIBRARY_READ: 'lib:r'
  LIBRARY_WRITE: 'lib:w'
  PRODUCTION_READ: 'prod:r'
  PRODUCTION_WRITE: 'prod:w'


class TokenData(FlexModel):
  token_key: str = Field(
    ...,
    alias="jti",
    description="JWT ID — ArangoDB `_key` of the corresponding `Token` document.",
    examples=["tok_a1b2c3d4"],
  )
  consumer_key: str = Field(
    ...,
    alias="sub",
    description="Subject — ArangoDB `_key` of the User (or other consumer) this token belongs to.",
    examples=["user42"],
  )
  consumer_type: ConsumerType = Field(
    ConsumerType.USER,
    alias="ctyp",
    description="Type of the token consumer: `user`, `app`, `equipment`, or `3psw`.",
    examples=["user"],
  )
  issued_at: datetime = Field(
    ...,
    alias="iat",
    description="UTC timestamp at which the token was issued (JWT `iat` claim).",
    examples=["2026-05-04T08:00:00Z"],
  )
  expires_at: datetime | None = Field(
    ...,
    alias="exp",
    description="UTC timestamp at which the token expires (JWT `exp` claim). `null` for non-expiring tokens.",
    examples=["2026-05-05T08:00:00Z"],
  )
  context: TokenContext = Field(
    ...,
    alias="ctx",
    description="Token context indicating its intended use (session, api, pwd_reset, sse_ticket).",
    examples=["session"],
  )
  scope: str | None = Field(
    None,
    description="Space-separated scope string copied from the User's scope at token issuance time.",
    examples=["admin production lib:r lib:w"],
  )
  # audience: str | None = Field(None, alias="aud") # identify third party apps
  # issuer: str | None = Field(None, alias="iss") # url of server


class AuthResponse(BaseModel):
  action: str = Field(
    ...,
    description="Describes the next required action: `start_session` for a normal login or `reset_password` when the user must change their password.",
    examples=["start_session"],
  )
  user_key: str = Field(
    ...,
    description="ArangoDB `_key` of the authenticated User document.",
    examples=["user42"],
  )


class UserSession(ArangoDocument):
  active: bool = Field(
    ...,
    description="Whether this session is currently open. Set to `false` on logout.",
    examples=[True],
  )
  user_key: str = Field(
    ...,
    description="ArangoDB `_key` of the User who owns this session.",
    examples=["user42"],
  )
  token_key: str = Field(
    ...,
    description="ArangoDB `_key` of the Token document issued for this session.",
    examples=["tok_a1b2c3d4"],
  )
  login_at: datetime = Field(
    default_factory=lambda: datetime.now(tz.UTC),
    description="UTC timestamp at which the session was opened.",
    examples=["2026-05-04T08:00:00Z"],
  )
  logout_at: datetime | None = Field(
    None,
    description="UTC timestamp at which the session was closed. `null` while the session is active.",
    examples=["2026-05-04T16:30:00Z"],
  )
  scope: str = Field(
    ...,
    description="Space-separated scope string that was active for this session.",
    examples=["admin production lib:r lib:w"],
  )
  name: str | None = Field(
    None,
    description="Given name of the user at session creation time (denormalised copy).",
    examples=["Alice"],
  )
  surname: str | None = Field(
    None,
    description="Family name of the user at session creation time (denormalised copy).",
    examples=["Smith"],
  )

class NewSessionData(BaseModel):
  session_key: str = Field(
    ...,
    description="ArangoDB `_key` of the newly created `UserSession` document.",
    examples=["sess_xyz789"],
  )
  user_key: str = Field(
    ...,
    description="ArangoDB `_key` of the User who opened the session.",
    examples=["user42"],
  )
  name: str | None = Field(
    None,
    description="User's given name, for display in the frontend.",
    examples=["Alice"],
  )
  surname: str | None = Field(
    None,
    description="User's family name, for display in the frontend.",
    examples=["Smith"],
  )
  scope: str = Field(
    ...,
    description="Space-separated scope string for this session, used by the frontend to gate UI features.",
    examples=["admin production lib:r lib:w"],
  )
  preferences: UserPreferences = Field(
    default_factory=UserPreferences,
    description="User's saved UI preferences (theme, locale, home page, etc.).",
  )
  timeout: timedelta = Field(
    default=timedelta(minutes=30),
    description="Inactivity timeout for this session.",
    examples=["PT15M"],
  )

class GrantType(str, Enum):
  AUTHORIZATION_CODE: 'authorization_code'
  PASSWORD: 'password'


class ConsumerCredentials(BaseModel):
  username: str = Field(
    ...,
    description="Username (login name) of the platform user.",
    examples=["alice.smith"],
  )
  password: str = Field(
    ...,
    description="Plain-text password submitted at login. Compared against the stored bcrypt hash.",
    examples=["s3cr3t!"],
  )
  # auth_code: str | None = None
  # grant_type: GrantType = Form(None)
