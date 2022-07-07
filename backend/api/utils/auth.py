import secrets
import traceback
from time import time

import jwt
from arango.exceptions import DocumentGetError, DocumentUpdateError
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from starlette import status

from models.auth import *
from models.org import User
from utils.db import db
from utils.exceptions import *


scopes_description = {
  "admin": "User can access and edit users and system settings",
  # "admin.users": "User can read and modify data about other users",
  "library": "User can access and edit products",
  # "lib:r": "User can read library data such as products, processes and bills of materials",
  # "lib:w": "User can read, add, modify and delete library data such as products, processes and bills of materials",
  "production": "User can access and edit production plans",
  # "prod:r": "User can read production plans, job queues, and work order details",
  # "prod:w": "User can read, add, modify and delete data related to production plans, job queues and work orders",
  "operator": "User can access the operator panel and make production declarations"
}

TOKEN_SECRET = "0ac33c11e3f6c4903f6f30c03edfda07e513288884a8d573690eb6d916fca034"
ALGORITHM = "HS256"


bearer_token = OAuth2PasswordBearer(tokenUrl="/auth", scopes=scopes_description)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

debugging_info = dict(
  message="Could not validate credentials.",
  stacktrace=traceback.format_exc()
)

credentials_exception = HTTPException(
  status_code=status.HTTP_401_UNAUTHORIZED,
  detail=debugging_info,
  headers={"WWW-Authenticate": "Bearer"},
)

# ----------------------------------------------------------------------

def get_password_hash(password):
    return pwd_context.hash(password)

# ----------------------------------------------------------------------

def verify_password(plain_password, hashed_password):
  return pwd_context.verify(plain_password, hashed_password)


# ----------------------------------------------------------------------

def verify_token(token_str: str = Depends(bearer_token)):

  try: 
    try:
      token_json = jwt.decode(token_str, TOKEN_SECRET, algorithms=[ALGORITHM])
    
    except jwt.ExpiredSignatureError:
      print('Token expired')
      raise TokenExpiredError

    except jwt.InvalidSignatureError:
      print('TokenSignatureVerificationError')
      raise TokenSignatureVerificationError
    
    except:
      raise Exception(traceback.format_exc())
    
    try:  
      token_data = TokenData(**token_json)
    except:
      raise Exception(traceback.format_exc())

    try:
      token_record = TokenRecord( **db.collection('Token').get(token_data.token_key) )
    except:
      print('TokenNotFoundError')
      raise TokenNotFoundError

    if not token_str.split('.')[-1] == token_record.signature:
      print('TokenSignatureMismatchError')
      raise TokenSignatureMismatchError

    if token_record.revoked:
      print('TokenRevokedError')
      raise TokenRevokedError

  except Exception as e:
    print(e)
    traceback.print_exc()
    raise credentials_exception

  return token_data

# ----------------------------------------------------------------------

def revoke_token(token_key, db=db):
  try:
    db.collection('Token').update(dict(_key=token_key, revoked=True))
  except DocumentUpdateError:
    pass
  except:
    traceback.print_exc()
    print(vars())

# ----------------------------------------------------------------------


def issue_token(
  consumer_key: str,
  seconds_until_expired: int,
  scope: str = None,
  consumer_type: ConsumerType = ConsumerType.USER,
  context: TokenContext = TokenContext.USER_SESSION,
):
  now = datetime.utcnow()
  token_key = secrets.token_hex(6)
  access_token_data = TokenData(
    token_key = token_key,
    consumer_key = consumer_key, 
    consumer_type = consumer_type, 
    context = context,
    scope = scope,
    issued_at = now,
    expires_at = now + timedelta(seconds=seconds_until_expired)
  )

  access_token = jwt.encode(
    access_token_data.dict(by_alias=True, exclude_none=True), 
    TOKEN_SECRET, 
    algorithm=ALGORITHM
  )

  return access_token, access_token_data


# ----------------------------------------------------------------------


def verify_user(password, username=None, user_key=None, db=db):
  # Verify User exists in DB
  if username:
    try:
      user = User( **db.collection('User').find(dict(username=username)).next() )
    except StopIteration:
      raise UserNotFoundError
    except Exception as e:
      raise HTTPException(
        status_code=500,
        detail=dict(
          message="Error while validating credentials.",
          error=e,
          stacktrace=traceback.format_exc()
        ),
      )
  
  elif user_key:
    try: 
      user = User( **db.collection('User').get(user_key) )
    except DocumentGetError:
      raise UserNotFoundError

  else:
    raise TypeError('Username or user key must be provided')

  #Verify use is enabled
  if not user.active or user.trash:
    raise UserDisabledError
 
  # Verify password
  if not verify_password(password, user.psw_hash):
    raise UserPasswordMismatchError

  return user

# ----------------------------------------------------------------------

def close_session(session_key, token_key, db=db):
  tx = db.begin_transaction(write=['Token', 'UserSession'])
  
  session_update = dict(
    _key=session_key,
    active=False,
    logout_at=datetime.now(tz.UTC)
  )
  tx.collection('UserSession').update(session_update, return_new=True)['new']
  revoke_token(token_key, tx)
  tx.commit_transaction()




class Queries:

  INSERT_USER_SESSION = """
    FOR u IN User
      FILTER u._key == @user_key
      LET session_data = {
        active: true,
        token_key: @token_key,
        user_key: u._key,
        login_at: DATE_ISO8601(DATE_NOW()),
        logout_at: null,
        scope: u.scope,
        name: u.name,
        surname: u.surname
      }
      INSERT session_data IN UserSession RETURN NEW
  """
