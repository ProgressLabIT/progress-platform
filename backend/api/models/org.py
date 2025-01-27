from datetime import datetime
from dateutil import tz
from enum import Enum

from pydantic import BaseModel

from models.base_models import ArangoDocument


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

class JobSelectionLayout(str, Enum):
  CARD = 'card'
  LIST = 'list'

class DisplayFont(str, Enum):
  ORBITRON = 'orbitron'
  RED_HAT_DISPLAY = 'red-hat-display'

class HomePageOptions(str, Enum):
  ADMIN = 'adminPanel'
  PRODUCTS = 'libraryRoot'
  PRODUCTION = 'productionRoot'
  OPERATOR = 'operatorRoot'
  QUALITY = 'qualityRoot'
  REPORTS = 'reportRoot'
  WAREHOUSE = 'warehouseRoot'

class WorkSessionTabs(str, Enum):
  PROCEDURE = 'jobSteps'
  DOCS = 'jobDocs'
  BOM = 'jobBom'
  ISSUES = 'jobIssues'
  NOTES = 'jobNotes'
  MESSAGES = 'jobMessages'
  PROCESS = 'jobProcessView'

class Theme(str, Enum):
  DARK = 'dark'
  LIGHT = 'light'

class UserPreferences(BaseModel):
  theme: Theme | None = Theme.DARK
  locale: str | None = None
  display_font: DisplayFont | None = DisplayFont.ORBITRON
  home_page: HomePageOptions | None = None
  job_selection_layout: JobSelectionLayout | None = JobSelectionLayout.CARD
  work_session_tabs_order: list[WorkSessionTabs] | None = [WorkSessionTabs.PROCEDURE, WorkSessionTabs.DOCS, WorkSessionTabs.BOM, WorkSessionTabs.ISSUES, WorkSessionTabs.NOTES, WorkSessionTabs.MESSAGES, WorkSessionTabs.PROCESS]

class UserNew(BaseModel):
  name: str | None = None
  surname: str | None = None
  username: str
  site_key: str = '0'
  department_key: str | None = None
  hourly_cost: float | None = None
  email: str | None = None
  scope: str
  preferences: UserPreferences = UserPreferences()


class User(ArangoDocument, UserNew):
  created_at: datetime = datetime.now(tz.UTC)
  active: bool = True  # change to 'enabled'
  email: str | None = None

  psw_hash: str | None = None
  reset_password: bool = False

  last_user_session: str | None = None
  last_login: datetime | None = None

  trash: bool = False
