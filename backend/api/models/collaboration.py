from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from models.form import FormFieldDefinition, FormFieldValue
from models.print import PrintTemplateRecord
from utils.base_models import ArangoDocument
from utils.dt import timestamp


# ISSUE TYPE
class IssueType(ArangoDocument):
  code: str
  name: str
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


class FieldValue(BaseModel):
  field_key: str # Reference to CustomField record
  value: Any | None = None


# ISSUE
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



# MESSAGE

class MessageContext(str, Enum):
  issue = 'issue'
  work_order = 'work_order'


class Message(ArangoDocument):
  sender: str = Field(..., alias="_from") # ID of creator (User/Machine/etc.)
  recipient: str = Field(..., alias="_to") # related issue or user
  content: str
  created: datetime = Field(default_factory=timestamp)
  updated: datetime | None = None
  deleted: datetime | None = None

class IssueFullData(IssueWithLinks):
  messages: list[Message]
  history: list[dict]
