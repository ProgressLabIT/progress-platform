from base64 import b64decode
from datetime import datetime, date
from enum import Enum
import json
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator, StringConstraints

from models.form import FormFieldDefinition, FormFieldValue, TaskFormFieldValue
from models.print import PrintTemplateRecord
from models.base_models import ArangoDocument, ArangoEdge
from utils.dt import timestamp


# ==============================================================================
# ISSUES
# ==============================================================================
class IssueType(ArangoDocument):
  name: str
  code: str | None = None
  active: bool = True
  description: str | None = None
  icon: str | None = None
  form_template: list[FormFieldDefinition] = []
  critical: bool = False
  # close_within: NonNegativeInt = 0 # Time in hours. After this make critical. If 0 ignore.


class IssueTypeUpdate(BaseModel):
  key: str | None = Field(None, alias='_key')
  code: str | None = None
  name: str | None = None
  active: bool | None = None
  description: str | None = None
  icon: str | None = None
  form_template: list[FormFieldDefinition] = []
  critical: bool = False


class IssueTypeFull(IssueType):
  print_templates: list[PrintTemplateRecord] | None = None


class Issue(ArangoDocument):
  """
  Issues can be connected to some other entity, such as Product, Phase, WorkOrder, Job, Operation, etc. To effectively track issues these links must be explicitly recorded. THis connection is stored in an edge collection.

  A job link is enough to establish within a graph single query all the relationships with Phase, Operation and Product and WorkOrder. However If the issue is raised within the WorkOrder in general there's no graph that can help, and the product must be associated explicitly.
  """
  issue_type_key: str | None = None # _key of the issue type
  created: datetime = Field(default_factory=timestamp)
  created_by: str # Creator ID
  closed: datetime | None = None
  closed_by: str | None = None # Closer ID
  critical: bool # Default value set at the IssueType level
  # close_within: NonNegativeInt # Value set at the IssueType level
  data: list[FormFieldValue] | None = None
  open: bool = True

  # Require issue type only when closing.
  @model_validator(mode="before")
  @classmethod
  def ensure_type_if_closing(cls, values):
    if not values.get('open') and values.get('issue_type_key') is None:
      raise ValueError('Issue must have type associated to be closed')
    return values


class IssueLinkType(str, Enum):
  PRODUCT = 'product'
  OPERATION = 'operation'
  PHASE = 'phase'
  WORK_ORDER = 'work_order'
  PROJECT = 'project'
  USER = 'user'
  JOB = 'job'
  SERIAL = 'serial'

class IssueLink(BaseModel):
  type: IssueLinkType
  key: str


class IssueWithLinks(Issue):
  linked_to: list[IssueLink] = [] # ids of entities connected

  # @validator('_from')
  # def check_from_issue(cls, value):
  #   if value.split('/')[0] != 'Issue':
  #     raise ValueError('This record is not related to an Issue')
  #   return value


# ==============================================================================
# MESSAGES
# ==============================================================================

class MessageContext(str, Enum):
  issue = 'issue'
  work_order = 'work_order'


class Message(ArangoDocument):
  sender: str = Field(..., alias="_from") # ID of creator (User/Machine/etc.)
  recipient: str = Field(..., alias="_to") # related issue or user
  content: str | None = None
  created: datetime | None = Field(default_factory=timestamp)
  updated: datetime | None = None
  deleted: datetime | None = None

class MessageUpdate(ArangoDocument):
  sender: str = Field(..., alias="_from") # ID of creator (User/Machine/etc.)
  recipient: str = Field(..., alias="_to") #
  content: str | None = None
  updated: datetime | None = None
  deleted: datetime | None = None

class IssueFullData(IssueWithLinks):
  messages: list[Message]
  history: list[dict]


# ==============================================================================
# TASKS
# ==============================================================================

class TaskLinkType(str, Enum):
  ISSUE = 'issue'
  WORK_ORDER = 'work_order'
  PRODUCT = 'product'
  EQUIPMENT = 'equipment'
  SERIAL = 'serial'
  TASK = 'task'

class TaskType(ArangoDocument):
  name: str
  description: str | None = None
  active: bool | None = True
  icon: str | None = None
  created: datetime = Field(default_factory=timestamp)
  form_fields: list[FormFieldDefinition] | None = []
  allowed_linked_entities: list[TaskLinkType] | None = []


class TaskTypeFull(TaskType):
  print_templates: list[PrintTemplateRecord] | None = None


class TaskStatus(str, Enum):
  OPEN = "open"
  COMPLETED = "completed"
  CANCELED = "canceled"



class TaskAssignmentRole(str, Enum):
  OWNER = 'owner'
  PARTICIPANT = 'participant'

class TaskAssignment(BaseModel):
  user_key: str
  role: TaskAssignmentRole | None = TaskAssignmentRole.PARTICIPANT

class Task(ArangoDocument):
  task_type_key: str
  code: Annotated[str, StringConstraints(to_upper=True, strip_whitespace=True, min_length=1)] | None = None
  status: TaskStatus | None = TaskStatus.OPEN
  owner_key: str | None = None
  assigned_to: list[TaskAssignment] | None = []
  start_from: datetime | None = None
  due_by: datetime | None = None
  created: datetime | None = None
  created_by: str | None = None
  closed: datetime | None = None
  closed_by: str | None = None
  title: str | None = None
  description: str | None = None
  form_fields: list[TaskFormFieldValue] | None = []

  @model_validator(mode='after')
  def validate_assignments(self):
    # Ensure single owner if assignments are provided
    owners = [a for a in self.assigned_to if a.role == TaskAssignmentRole.OWNER]
    if len(self.assigned_to) > 0 and len(owners) != 1:
      raise ValueError('You must provide one and only one owner when specifying assignments')

    # Set top level owner key for easier access and reorder assignments to put owner first
    self.owner_key = owners[0].user_key if owners else None
    if owners:
      owner = owners[0]
      participants = [a for a in self.assigned_to if a.role == TaskAssignmentRole.PARTICIPANT]
      self.assigned_to = [owner] + participants
    return self

class TaskLink(ArangoEdge):
  created: datetime = Field(default_factory=timestamp)
  created_by: str | None = None

class TaskSearchParameters(BaseModel):
  search: str | None = None
  task_type_key: str | None = None
  status_open: bool | None = None
  status_completed: bool | None = None
  status_canceled: bool | None = None
  owner_key: str | None = None # Owner is a special case of participant.
  assigned_to: list[str] | None = None
  start_from: date | None = None
  due_by: date | None = None
  created_from: date | None = None
  created_to: date | None = None
  closed_from: date | None = None
  closed_to: date | None = None
  advanced_filters: dict | None = None
  limit: int | None = 200
  offset: int | None = 0

  @field_validator('advanced_filters', 'assigned_to', mode='before')
  @classmethod
  def deserialize_base64(cls, value: str | None) -> dict | list[str] | None:
    if isinstance(value, str):
      return json.loads(b64decode(value).decode('latin-1'))
    return value


class TaskSearchResult(Task):
  icon: str | None = None
  task_type_name: str | None = None
