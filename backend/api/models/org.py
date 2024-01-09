from datetime import datetime
from dateutil import tz
from enum import Enum

from pydantic import BaseModel

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


class JobSelectionLayout(str, Enum):
  CARD = 'card'
  LIST = 'list'

class UserPreferences(BaseModel):
  home_page: str = None
  job_selection_layout: JobSelectionLayout = JobSelectionLayout.CARD
  work_session_tabs_order: list[str] = None

class User(ArangoDocument, UserNew):
  created_at: datetime = datetime.now(tz.UTC)
  active: bool = True  # change to 'enabled'
  email: str = None
  preferences: UserPreferences = UserPreferences()

  psw_hash: str = None
  reset_password: bool = False

  last_user_session: str = None
  last_login: datetime = None

  trash: bool = False
