from datetime import timedelta, datetime
from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from .models import User, Token, TokenData
from utils.db import db


user_db = db.collection('User')

SECRET_KEY = "0ac33c11e3f6c4903f6f30c03edfda07e513288884a8d573690eb6d916fca034"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokerUrl="/login")


def verify_password(plain_psw, hashed_psw):
  return pwd_context.verify(plain_psw, hashed_psw)

def get_password_hash(password):
  return pwd_context.hash(password)


def get_user(user_db, username: str):
  try:
    user_record = user_db.find({ login_code: username }).pop()
  except CursorEmptyError:
    return False

  return User(**user_record)



def authenticate_user(user_db, username: str, password: str):
  user = get_user(user_db, username)
  if not user or not user.active:
    return False # User not present in DB or not active

  if not verify_password(password, user.psw_hash):
    return False # Wrong credentials

  return user


def create_access_token(*, data: dict, expires_delta: timedelta = None):
  to_encode = data.copy()
  if expires_delta:
    expire = datetime.utcnow() + expires_delta
  else:
    expire = datetime.utcnow() + timedelta(minutes=30)
  to_encode.update({"exp": expire})
  encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
  return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme))
  credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
  )
  try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username: str = payload.get("sub")
    if username is None:
      raise credentials_exception
    token_data = TokenData(username=username)

  except PyJWTError:
    raise credentials_exception

  user = get_user(user_db, userrname=token_data.username)
  
  if user is None:
    raise credentials_exception

  return user



@router.post("/login", response_model=Token)
async def login_for_access_token(
  form_data: OAuth2PasswordRequestForm = Depends()
):
  user = authenticate_user(user_db, form_data.username, form_data.password)
  if not user:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Incorrect username or password",
      headers={"WWW_Authenticate": "Bearer"},
    )

  access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
  access_token = create_access_token(
    data={"sub": user.username}, 
    expires_delta = access_token_expires
  )

  return { "access_token": access_token, "token_type": "bearer" }


