from typing import List

from pydantic import BaseModel

from utils.base_models import ArangoDocument


class Token(BaseModel):
  access_token: str
  token_type: str


class TokenData(BaseModel): 
  username: str = None



class UserRoles(BaseModel):
  admin: bool = False
  planner: bool = False
  operator: bool = False


class User(ArangoDocument):
  active: bool = False
  roles: UserRoles = UserRoles()
  name: str = None
  surname: str = None
  login_code: str
  psw_hash: str
  last_user_session: str = None