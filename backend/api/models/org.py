from datetime import datetime
from dateutil import tz
from enum import Enum

from pydantic import BaseModel, Field

from models.base_models import ArangoDocument


class Site(ArangoDocument):
  code: str | None = Field(
    None,
    description="Short alphanumeric code identifying the site.",
    examples=["SITE-01"],
  )
  name: str = Field(
    ...,
    description="Full display name of the manufacturing site.",
    examples=["Main Plant"],
  )
  description: str | None = Field(
    None,
    description="Optional free-text description of the site.",
    examples=["Primary manufacturing facility in Bologna."],
  )
  address: str | None = Field(
    None,
    description="Physical address of the site.",
    examples=["Via Roma 1, 40121 Bologna, Italy"],
  )
  iso_country_code: str | None = Field(
    None,
    description="ISO 3166-1 alpha-2 country code for the site's location.",
    examples=["IT"],
  )


class Department(ArangoDocument):
  name: str = Field(
    ...,
    description="Display name of the department.",
    examples=["Quality Assurance"],
  )
  code: str | None = Field(
    None,
    description="Short alphanumeric code for the department.",
    examples=["QA"],
  )
  description: str | None = Field(
    None,
    description="Optional description of the department's responsibilities.",
    examples=["Handles all inspection and non-conformance processes."],
  )


class UserListItem(ArangoDocument):
  active: bool = Field(
    True,
    description="Whether this user account is currently active. Archived users have `active=false`.",
    examples=[True],
  )
  name: str | None = Field(
    None,
    description="User's given (first) name.",
    examples=["Alice"],
  )
  surname: str | None = Field(
    None,
    description="User's family (last) name.",
    examples=["Smith"],
  )
  username: str = Field(
    ...,
    description="Unique login username for this account.",
    examples=["alice.smith"],
  )
  email: str | None = Field(
    None,
    description="User's email address.",
    examples=["alice.smith@progresslab.it"],
  )
  scope: str | None = Field(
    None,
    description="Space-separated permission scope string assigned to this user.",
    examples=["admin production lib:r lib:w"],
  )
  logged_in: bool = Field(
    False,
    description="Whether the user currently has an active session.",
    examples=[False],
  )
  hourly_cost: float | None = Field(
    None,
    description="Hourly labour cost for this user, used in production cost calculations.",
    examples=[32.5],
  )
  department: Department | None = Field(
    None,
    description="The department this user belongs to, if assigned.",
  )
  # roles: UserRoles = UserRoles()
  created_at: datetime | None = Field(
    None,
    description="UTC timestamp at which this user account was created.",
    examples=["2026-01-15T09:00:00Z"],
  )
  last_login: datetime | None = Field(
    None,
    description="UTC timestamp of the user's most recent successful login.",
    examples=["2026-05-04T08:00:00Z"],
  )

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
  TASKS = 'taskRoot'
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
  theme: Theme | None = Field(
    Theme.DARK,
    description="UI colour theme. `dark` or `light`.",
    examples=["dark"],
  )
  locale: str | None = Field(
    None,
    description="BCP 47 locale tag for the UI language (e.g. `en-US`, `it-IT`).",
    examples=["en-US"],
  )
  display_font: DisplayFont | None = Field(
    DisplayFont.ORBITRON,
    description="Font family used in the operator display.",
    examples=["orbitron"],
  )
  home_page: HomePageOptions | None = Field(
    None,
    description="Route the user lands on after login.",
    examples=["productionRoot"],
  )
  job_selection_layout: JobSelectionLayout | None = Field(
    JobSelectionLayout.CARD,
    description="Layout style for the job selection screen: `card` or `list`.",
    examples=["card"],
  )
  work_session_tabs_order: list[WorkSessionTabs] | None = Field(
    default=[
      WorkSessionTabs.PROCEDURE, WorkSessionTabs.DOCS, WorkSessionTabs.BOM,
      WorkSessionTabs.ISSUES, WorkSessionTabs.NOTES, WorkSessionTabs.MESSAGES,
      WorkSessionTabs.PROCESS,
    ],
    description="Ordered list of tab identifiers shown in the work session view.",
    examples=[["jobSteps", "jobDocs", "jobBom", "jobIssues", "jobNotes", "jobMessages", "jobProcessView"]],
  )
  printer: str | None = Field(
    None,
    description="Default printer identifier used for label printing in the operator UI.",
    examples=["ZEBRA-ZT230-01"],
  )

class UserNew(BaseModel):
  name: str | None = Field(
    None,
    description="User's given name.",
    examples=["Alice"],
  )
  surname: str | None = Field(
    None,
    description="User's family name.",
    examples=["Smith"],
  )
  username: str = Field(
    ...,
    description="Unique login username. Must be unique across all users.",
    examples=["alice.smith"],
  )
  site_key: str = Field(
    '0',
    description="ArangoDB `_key` of the site this user is assigned to. Defaults to `'0'` (main site).",
    examples=["0"],
  )
  department_key: str | None = Field(
    None,
    description="ArangoDB `_key` of the department this user belongs to.",
    examples=["dept_qa"],
  )
  hourly_cost: float | None = Field(
    None,
    description="Hourly labour cost used in production cost tracking.",
    examples=[32.5],
  )
  email: str | None = Field(
    None,
    description="User's email address for notifications and identification.",
    examples=["alice.smith@progresslab.it"],
  )
  scope: str = Field(
    ...,
    description="Space-separated permission scope string granted to this user.",
    examples=["production lib:r lib:w"],
  )
  preferences: UserPreferences = Field(
    default_factory=UserPreferences,
    description="Initial UI preferences for this user. Defaults to system defaults.",
  )


class User(ArangoDocument, UserNew):
  created_at: datetime = Field(
    default_factory=lambda: datetime.now(tz.UTC),
    description="UTC timestamp at which this user was created.",
    examples=["2026-01-15T09:00:00Z"],
  )
  active: bool = Field(
    True,
    description="Whether this account is active. Archived accounts have `active=false`.",
    examples=[True],
  )
  email: str | None = Field(
    None,
    description="User's email address.",
    examples=["alice.smith@progresslab.it"],
  )

  psw_hash: str | None = Field(
    None,
    description="bcrypt hash of the user's password. Never returned in API responses.",
    examples=None,
  )
  reset_password: bool = Field(
    False,
    description="When `true`, the user must change their password on next login.",
    examples=[False],
  )

  last_user_session: str | None = Field(
    None,
    description="ArangoDB `_key` of the most recent `UserSession` document for this user.",
    examples=["sess_xyz789"],
  )
  last_login: datetime | None = Field(
    None,
    description="UTC timestamp of the user's most recent successful login.",
    examples=["2026-05-04T08:00:00Z"],
  )

  trash: bool = Field(
    False,
    description="Soft-delete flag. Archived users have `trash=true` and are excluded from active user lists.",
    examples=[False],
  )
