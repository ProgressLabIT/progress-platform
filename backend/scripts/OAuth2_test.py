from datetime import datetime, timedelta

import jwt
from jwt import PyJWTError
from passlib.context import CryptContext

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from starlette.status import HTTP_401_UNAUTHORIZED


SECRET_KEY = "75eb59e0cacfba30408e25c59efff03edda1536576f4a9455def7c65405e9f66"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

fake_users_db = {
  "johndoe": {
    "username": "johndoe",
    "full_name": "John Doe",
    "email": "johndoe@example.com", 
    "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
    "disabled": False,
  },
  # "alice": {
  #   "username": "alice",
  #   "full_name": "Alice Wonderson",
  #   "email": "alice@example.com", 
  #   "hashed_password": "fakedhashedsecret2",
  #   "disabled": True,
  # }
}


class Token(BaseModel):
  access_token: str
  token_type: str

class TokenData(BaseModel):
  username: str = None

class User(BaseModel):
  username: str
  email: str = None
  full_name: str = None
  disabled: bool = None

class UserInDB(User):
  hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

app = FastAPI()


def verify_password(plain_psw, hashed_psw):
  return pwd_context.verify(plain_psw, hashed_psw)

def get_psw_hash(password):
  return pwd_context.hash(password)


def get_user(db, username: str):
  if username in db:
    user_dict = db[username]
    return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
  user = get_user(fake_db, username)
  if not user:
    return False
  if not verify_password(password, user.hashed_password)
    return False
  return user



def create_access_token(*, data: dict, expires_delta: timedelta = None):
  to_encode = data.copy()
  if expires_delta:
    expire = datetime.utcnow() + expires_delta
  else:
    expire = datetime.utcnow() + timedelta(minutes=15)
  to_encode.update({"exp": expire})
  encoded_jwt = jwt.econde(to_encode, SECRET_KEY, algorithm=ALGORITHM)
  return encoded_jwt


# Check password matches
async def get_current_user(token: str = Depends(oauth2_scheme)):
  credentials_exception = HTTPException(
    status_code=HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
  )
  try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username: str 0 Payload.get("sub")



# Make sure the user is not disabled
async def get_current_active_user(current_user: User = Depends(get_current_user)):
  if current_user.disabled:
    raise HTTPException(status_code=400, detail="Inactive user")
  return current_user


@app.post("/token"):
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
  user_dict = fake_users_db.get(form_data.username)
  if not user_dict:
    raise HTTPException(status_code=400, detail="incorrect username or password")
  user = UserInDB(**user_dict)
  hashed_password = fake_hash_password(form_data.password)
  if not hashed_password == user.hashed_password:
    raise HTTPException(status_code=400, detail="Incorrect username or password")

  return { "access_token": user.username, "token_type": "bearer"}


@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
  return current_user