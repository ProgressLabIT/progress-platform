from datetime import datetime
from dateutil import tz
from typing import List

from pydantic import BaseModel, Field

from utils.base_models import ArangoDocument


class Department(ArangoDocument):
  name: str
  code: str = None
  description: str = None  

class UserRoles(BaseModel):
  admin: bool = False
  manager: bool = False
  operator: bool = False

class UserListItem(ArangoDocument):
  active: bool = True
  name: str = None
  surname: str = None
  username: str
  email: str = None
  scopes: List[str] = []
  logged_in: bool = False
  hourly_cost: float = None
  department: Department = None
  roles: UserRoles = UserRoles()
  created_at: datetime = None
  last_login: datetime = None


class UserNew(BaseModel):
  name: str = None
  surname: str = None
  username: str
  department_id: str = None
  hourly_cost: float = None
  email: str = None
  scopes: List[str] = []


class User(ArangoDocument):
  created_at: datetime = datetime.now(tz.UTC)
  active: bool = True  # change to 'enabled'
  
  name: str = None
  surname: str = None
  username: str
  email: str = None
  
  department_id: str = None
  hourly_cost: float = None

  psw_hash: str = None
  scope: str
  reset_password: bool = False
  
  last_user_session: str = None
  last_login: datetime = None
  logged_in: bool = False

  trash: False

  # active_token_signature: str = None #active token signature
  # permissions: Permissions = None
