import secrets
import traceback
from time import time
from datetime import datetime, timedelta
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
from utils.auth import (
  credentials_exception,
  get_password_hash, 
  issue_token,
  revoke_token,
  verify_password,
  verify_token,
  verify_user
)
from utils.db import db
from utils.exceptions import *


router = APIRouter()
user_db = db.collection('User')

ACCESS_TOKEN_EXPIRE_MINUTES = 1440 # 24 hours
RESET_PASSWORD_TOKEN_EXPIRE_MINUTES = 5



# ----------------------------------------------------------------------


@router.post("/auth")
async def authenticate_user(username: str = Body(...), password: str = Body(...)):

  try: 
    user = verify_user(username, password, db)

  except (UserNotFoundError, UserDisabledError, UserPasswordMismatchError):
    raise credentials_exception

  except UserAlreadyLoggedInError:
    raise HTTPException(
      status_code=status.HTTP_409_CONFLICT,
      detail="User already logged in. Logout of any other session before trying again."
    )
    
  # Check if user should reset the password
  if user.reset_password:
    
    token, token_data = issue_token(
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
    token, token_data = issue_token(
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


@router.post("/user/{user_key}/session")
async def start_user_session(user_key: str, token: TokenData = Depends(verify_token)):

  # Check all token data matches the use for session creation
  if not (
    user_key == token.consumer_key 
    and token.consumer_type == ConsumerType.USER
    and token.context == TokenContext.USER_SESSION
  ):
    revoke_token(token.token_key)
    raise credentials_exception
  

  try:
    # -----------------------------------
    # TRANSACTION STARTS
    # -----------------------------------
    tx = db.begin_transaction(write=['User', 'UserSession'])

    # Create Session record
    user_id = f'User/{user_key}'
    token_id = f'Token/{token.token_key}'

    new_session_query = """
      FOR u IN User
      FILTER u._id == @user_id
      LET session_data = {
        active: true,
        token_id: @token_id,
        user_id: @user_id,
        login_at: DATE_ISO8601(DATE_NOW()),
        logout_at: null,
        scope: u.scope,
        name: u.name,
        surname: u.surname
      }
      INSERT session_data IN UserSession RETURN NEW
    """

    query_params = {
      'token_id': token_id,
      'user_id': user_id
    }

    try:
      new_session_data = tx.aql.execute(new_session_query, bind_vars=query_params).next()
      print(new_session_data)
      new_user_session = UserSession(**new_session_data)
    except:
      status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
      response = {
        'status_code': status_code,
        'message': "There was an error opening the session. Please contact the administrator.",
        'error': traceback.format_exc()
      }
      raise HTTPException(status_code, detail=response)

    # Update User data
    user_update = { 
      '_id': user_id, 
      'last_user_session': new_user_session.id,
      'logged_in': True,
      'last_login': new_user_session.login_at
    }
    new_user_data = tx.collection('User').update(user_update, return_new=True)['new']
    updated_user = User(**new_user_data)

  except Exception as e:
    tx.abort_transaction()
    status_code = 500
    response = {
      "status": status_code,
      "message": "Errore durante la creazione della sessione utente",
      "error": traceback.format_exc()
    }
    raise HTTPException(
      status_code=status_code,
      detail=response
    )

  print(vars(new_user_session))
  # Prepare response 
  response_details = NewSessionData( 
    user_id=user_id,
    name=updated_user.name,
    surname=updated_user.surname,
    session_id=new_user_session.id,
    scope=updated_user.scope
  )

  tx.commit_transaction()
  # -----------------------------------
  # TRANSACTION ENDS
  # -----------------------------------

  return APIResponse(detail=new_user_session)

# ----------------------------------------------------------------------
