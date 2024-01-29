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
  theme: Theme = Theme.DARK
  locale: str = None
  display_font: DisplayFont = DisplayFont.ORBITRON
  home_page: HomePageOptions = None
  job_selection_layout: JobSelectionLayout = JobSelectionLayout.CARD
  work_session_tabs_order: list[WorkSessionTabs] = [WorkSessionTabs.PROCEDURE, WorkSessionTabs.DOCS, WorkSessionTabs.BOM, WorkSessionTabs.ISSUES, WorkSessionTabs.NOTES, WorkSessionTabs.MESSAGES, WorkSessionTabs.PROCESS]

class UserNew(BaseModel):
  name: str = None
  surname: str = None
  username: str
  site_key: str = '0'
  department_key: str = None
  hourly_cost: float = None
  email: str = None
  scope: str
  preferences: UserPreferences = UserPreferences()

class User(ArangoDocument, UserNew):
  created_at: datetime = datetime.now(tz.UTC)
  active: bool = True  # change to 'enabled'
  email: str = None

  psw_hash: str = None
  reset_password: bool = False

  last_user_session: str = None
  last_login: datetime = None

  trash: bool = False
