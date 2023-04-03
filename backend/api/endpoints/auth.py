import secrets
import traceback

from time import time
from datetime import datetime, timedelta
from dateutil import tz
from typing import Optional

import jwt
from fastapi import APIRouter, Body, Depends, Form, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status
from starlette.responses import JSONResponse


from models.auth import *
from models.org import User
from utils.api import APIResponse
from utils import auth
from utils.db import db
from utils.exceptions import *


router = APIRouter()
user_db = db.collection('User')

ACCESS_TOKEN_EXPIRE_MINUTES = 1440 # 24 hours
RESET_PASSWORD_TOKEN_EXPIRE_MINUTES = 5

USER_SESSION_TIMEOUT_MINUTES = 15


# ----------------------------------------------------------------------


@router.post("/auth")
async def authenticate_user(
  username: str = Body(...), 
  password: str = Body(...)
):

  try: 
    user = auth.verify_user(username=username, password=password, db=db)

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
      token=token 
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
      token=token 
    )

  # Store token data
  _, _, token_signature = token.split('.')

  token_record = TokenRecord(
    key=token_data.token_key,
    issued_to=user.id,
    issued_at=token_data.issued_at,
    expires_at=token_data.expires_at,
    signature=token_signature
  )
  db.collection('Token').insert(token_record)


  response_headers = {
    'Cache-Control': 'no-store',
    'Pragma': 'no-cache'
  }

  response_content = APIResponse(detail=response_data)

  return JSONResponse(
    content= jsonable_encoder(response_content), 
    headers=response_headers
  )
    

# ----------------------------------------------------------------------

@router.post('/user/{user_key}/verify')
async def verify_user_password(
  user_key: str, 
  password: str = Body(..., embed=True),
  token: TokenData = Depends(auth.verify_token)
):
  try:
    auth.verify_user(user_key=user_key, password=password)
  except:
    raise auth.credentials_exception

  return APIResponse(detail="User credentials verified.")



# ----------------------------------------------------------------------


@router.post("/session")
async def start_user_session(
  user_key: str = Body(..., embed=True), 
  token: TokenData = Depends(auth.verify_token)
):

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
    scope=updated_user.scope
  )

  tx.commit_transaction()
  # -----------------------------------
  # TRANSACTION ENDS
  # -----------------------------------

  return APIResponse(detail=response_details)

# ----------------------------------------------------------------------

@router.delete("/session/{session_key}")
async def close_user_session(
  session_key: str, 
  token_str: str = Depends(auth.bearer_token)
):

  token_json = jwt.decode(token_str, auth.TOKEN_SECRET, algorithms=[auth.ALGORITHM], verify_expiration=False)
  token = TokenData(**token_json)

  try:
    session = db.collection('UserSession').get(session_key)
    session_token_key = session['token_key']
    if not session_token_key == token.token_key:
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
