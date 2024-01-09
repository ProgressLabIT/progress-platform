from datetime import datetime
from dateutil import tz
from typing import List

from pydantic import BaseModel, Field

from utils.base_models import ArangoDocument


class Site(ArangoDocument):
  code: str = None
  name: str
  description: str = None
  address: str = None
  iso_country_code: str = None


class Department(ArangoDocument):
  name: str
  code: str = None
  description: str = None


class UserListItem(ArangoDocument):
  active: bool = True
  name: str = None
  surname: str = None
  username: str
  email: str = None
  scope: str = None
  logged_in: bool = False
  hourly_cost: float = None
  department: Department = None
  # roles: UserRoles = UserRoles()
  created_at: datetime = None
  last_login: datetime = None


class UserNew(BaseModel):
  name: str = None
  surname: str = None
  username: str
  site_key: str = '0'
  department_key: str = None
  hourly_cost: float = None
  email: str = None
  scope: str


class User(ArangoDocument, UserNew):
  created_at: datetime = datetime.now(tz.UTC)
  active: bool = True  # change to 'enabled'
  email: str = None
  home_page: str = None

  psw_hash: str = None
  reset_password: bool = False

  last_user_session: str = None
  last_login: datetime = None

  trash: bool = False
