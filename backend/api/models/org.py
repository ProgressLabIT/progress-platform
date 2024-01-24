from datetime import datetime
from dateutil import tz
from enum import Enum

from pydantic import BaseModel

from utils.base_models import ArangoDocument


class Site(ArangoDocument):
  code: str | None = None
  name: str
  description: str | None = None
  address: str | None = None
  iso_country_code: str | None = None


class Department(ArangoDocument):
  name: str
  code: str | None = None
  description: str | None = None


class UserListItem(ArangoDocument):
  active: bool = True
  name: str | None = None
  surname: str | None = None
  username: str
  email: str | None = None
  scope: str | None = None
  logged_in: bool = False
  hourly_cost: float | None = None
  department: Department | None = None
  # roles: UserRoles = UserRoles()
  created_at: datetime | None = None
  last_login: datetime | None = None


class UserNew(BaseModel):
  name: str | None = None
  surname: str | None = None
  username: str
  site_key: str = '0'
  department_key: str | None = None
  hourly_cost: float | None = None
  email: str | None = None
  scope: str


class JobSelectionLayout(str, Enum):
  CARD = 'card'
  LIST = 'list'

class DisplayFont(str, Enum):
  ORBITRON = 'orbitron'
  RED_HAT_DISPLAY = 'red-hat-display'

class UserPreferences(BaseModel):
  theme: str | None = None
  locale: str | None = None
  display_font: DisplayFont = DisplayFont.ORBITRON
  home_page: str | None = None
  job_selection_layout: JobSelectionLayout = JobSelectionLayout.CARD
  work_session_tabs_order: list[str] | None = None

class User(ArangoDocument, UserNew):
  created_at: datetime = datetime.now(tz.UTC)
  active: bool = True  # change to 'enabled'
  email: str | None = None
  preferences: UserPreferences = UserPreferences()

  psw_hash: str | None = None
  reset_password: bool = False

  last_user_session: str | None = None
  last_login: datetime | None = None

  trash: bool = False
