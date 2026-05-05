import secrets
import traceback

from time import time
from datetime import datetime, timedelta
from dateutil import tz
from typing import Optional, Annotated

import jwt
from fastapi import APIRouter, Body, Depends, Form, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status
from starlette.responses import JSONResponse


from models.auth import *
from models.org import User
from utils.api import APIResponse, AuthAPIResponse
from utils import auth
from utils.config import get_config
from utils.db import db
from utils.exceptions import *


router = APIRouter()
user_db = db.collection('User')

ACCESS_TOKEN_EXPIRE_MINUTES = 1440 # 24 hours
RESET_PASSWORD_TOKEN_EXPIRE_MINUTES = 5

USER_SESSION_TIMEOUT_MINUTES = 15


# ----------------------------------------------------------------------


@router.post(
  "/auth",
  response_model=AuthAPIResponse,
  responses={
    401: {"description": "Invalid credentials — username/password mismatch or user disabled"},
    500: {"description": "Unexpected server error during credential verification"},
  },
)
async def authenticate_user(
  form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
  """Authenticate a user and issue a bearer token.

  Validates the supplied username and password against the `User` collection.
  If the user has `reset_password=True`, returns a short-lived password-reset
  token (`action=reset_password`) instead of a full session token. Otherwise
  issues a 24-hour session token (`action=start_session`) and closes any
  previously active sessions for the same user.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** *(public — no auth)*
  """

  try:
    user = auth.verify_user(username=form_data.username, password=form_data.password, db=db)

  except (UserNotFoundError, UserDisabledError, UserPasswordMismatchError):
    raise auth.credentials_exception

  except Exception as e:
    traceback.print_exc()
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    response=dict(
      status_code=status_code,
      error=traceback.format_exc()
    )
    raise HTTPException(status_code, detail=response)

  # Verify user has no other active session. If yes, close them.
  active_user_sessions = db.collection('UserSession').find(dict(
    user_key=user.key,
    active=True
  ))
  if active_user_sessions.count():
    for session in active_user_sessions:
      token_key = session['token_key']
      auth.close_session(session['_key'], token_key)


  # Check if user should reset the password
  if user.reset_password:

    token, token_data = auth.issue_token(
      consumer_key = user.key,
      context = TokenContext.PASSWORD_RESET,
      seconds_until_expired = RESET_PASSWORD_TOKEN_EXPIRE_MINUTES * 60
    )

    response_data = AuthResponse(
      action='reset_password',
      user_key=user.key
    )

  else:
    # Issue session token with action 'session_start'
    token, token_data = auth.issue_token(
      consumer_key = user.key,
      scope = user.scope,
      seconds_until_expired = ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    response_data = AuthResponse(
      action='start_session',
      user_key=user.key
    )

  # Store token data
  _, _, token_signature = token.split('.')

  token_record = TokenRecord(
    key=token_data.token_key,
    issued_to=user.id,
    issued_at=token_data.issued_at,
    expires_at=token_data.expires_at,
    context=TokenContext.USER_SESSION,
    signature=token_signature
  )
  db.collection('Token').insert(token_record)


  response_headers = {
    'Cache-Control': 'no-store',
    'Pragma': 'no-cache'
  }

  response_content = AuthAPIResponse(detail=response_data)

  response_content.access_token = token
  response_content.token_type = "bearer"

  return JSONResponse(
    content= jsonable_encoder(response_content),
    headers=response_headers
  )

# ----------------------------------------------------------------------

@router.post(
  '/user/{user_key}/verify',
  response_model=APIResponse,
  responses={
    401: {"description": "Password does not match the stored hash for the given user"},
    500: {"description": "Unexpected error during password verification"},
  },
)
async def verify_user_password(
  user_key: str,
  password: str = Body(..., embed=True),
  token: TokenData = Depends(auth.verify_token)
):
  """Verify a user's current password.

  Checks the supplied plain-text password against the bcrypt hash stored for
  `user_key`. Returns 200 on success; raises 401 on mismatch. Used by the
  frontend before allowing sensitive operations that require re-confirmation.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `auth:user:verify`
  """
  try:
    auth.verify_user(user_key=user_key, password=password)
  except:
    raise auth.credentials_exception

  return APIResponse(detail="User credentials verified.")



# ----------------------------------------------------------------------


# ----------------------------------------------------------------------

@router.get(
  '/whoami',
  response_model=APIResponse,
  responses={
    401: {"description": "JWT is missing, expired, or otherwise invalid"},
  },
)
async def get_current_user(
  token: TokenData = Depends(auth.verify_token)
):
  """Return the user key extracted from the current session token.

  Decodes the bearer token from the `Authorization` header and returns the
  `consumer_key` (ArangoDB `_key` of the `User` document). Useful for
  frontend bootstrapping to confirm the session is still valid and to
  retrieve the caller's identity.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `auth:session:whoami`
  """
  credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
  try:
    user_key=token.consumer_key
    if user_key is None:
      raise credentials_exception
  except:
    raise credentials_exception

  return APIResponse(detail=dict(user_key=user_key), message="cookie is valid")



# ----------------------------------------------------------------------

@router.post(
  "/session",
  response_model=APIResponse,
  responses={
    401: {"description": "Token consumer key or context does not match expected values; token is revoked"},
    500: {"description": "Transaction error while creating UserSession or updating User record"},
  },
)
async def start_user_session(
  user_key: str = Body(..., embed=True),
  token: TokenData = Depends(auth.verify_token)
):
  """Open a new user session after token issuance.

  Called immediately after `POST /auth` with the same bearer token. Validates
  that `user_key` matches the token's `consumer_key` and that the token context
  is `USER_SESSION`. Creates a `UserSession` document and updates `User.last_login`
  within a single ArangoDB transaction. Returns session metadata including name,
  scope, and preferences for frontend initialisation.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `auth:session:start`
  """

  # Check all token data matches the use for session creation
  if not (
    user_key == token.consumer_key
    and token.consumer_type == ConsumerType.USER
    and token.context == TokenContext.USER_SESSION
  ):
    auth.revoke_token(token.token_key)
    raise auth.credentials_exception


  try:
    # -----------------------------------
    # TRANSACTION STARTS
    # -----------------------------------
    tx = db.begin_transaction(write=['User', 'UserSession'])

    # Create Session record
    query_params = dict(
      token_key=token.token_key,
      user_key=user_key
    )

    try:
      new_session_data = tx.aql.execute(auth.Queries.INSERT_USER_SESSION, bind_vars=query_params).next()
      new_user_session = UserSession(
        **new_session_data,
        timeout = timedelta(minutes=USER_SESSION_TIMEOUT_MINUTES)
      )

    except:
      tx.abort_transaction()
      status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
      response=dict(
        status_code=status_code,
        message="There was an error opening the session. Please contact the administrator.",
        error=traceback.format_exc()
      )
      raise HTTPException(status_code, detail=response)

    # Update User data
    user_update = dict(
      _key=user_key,
      last_user_session=new_user_session.key,
      last_login=new_user_session.login_at
    )

    new_user_data = tx.collection('User').update(user_update, return_new=True)['new']
    updated_user = User(**new_user_data)

  except Exception as e:
    tx.abort_transaction()
    status_code = 500
    response=dict(
      status=status_code,
      message="Errore durante la creazione della sessione utente",
      error=traceback.format_exc()
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )

  # Prepare response
  response_details = NewSessionData(
    user_key=user_key,
    name=updated_user.name,
    surname=updated_user.surname,
    session_key=new_user_session.key,
    scope=updated_user.scope,
    preferences=updated_user.preferences,
  )

  tx.commit_transaction()
  # -----------------------------------
  # TRANSACTION ENDS
  # -----------------------------------

  return APIResponse(detail=response_details)

# ----------------------------------------------------------------------

@router.delete(
  "/session/{session_key}",
  response_model=APIResponse,
  responses={
    401: {"description": "Token does not own the session and caller lacks admin/production scope for force-close"},
    500: {"description": "Database error while invalidating the session token"},
  },
)
async def close_user_session(
  session_key: str,
  force: bool | None = False,
  token_str: str = Depends(auth.bearer_token)
):
  """Close an active user session and revoke its token.

  Looks up the `UserSession` by `session_key`, validates that the caller owns
  it (token signature match), and calls `auth.close_session`. With `?force=true`
  an admin or production-scoped user can close another user's session. The bearer
  token is decoded with `verify_expiration=False` so expired tokens can still
  trigger a logout.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `auth:session:close`
  """

  token_json = jwt.decode(token_str, get_config().jwt_secret, algorithms=[auth.ALGORITHM], verify_expiration=False)
  token = TokenData(**token_json)

  is_entitled = False
  if force:
    caller = User( **db.collection('User').get(token.consumer_key))
    is_entitled = 'admin' in caller.scope or 'production' in caller.scope

  try:
    session = db.collection('UserSession').get(session_key)
    session_token_key = session['token_key']
    if (not session_token_key == token.token_key and not force) and (force and not is_entitled):
      raise auth.credentials_exception

    else:
      auth.close_session(session_key, session_token_key)

  except:
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    response = dict(
      status=status_code,
      message="Error while closing the session on the db.",
      error=traceback.format_exc()
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )

  return APIResponse(detail="Session closed successfully")
