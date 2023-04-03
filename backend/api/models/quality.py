from datetime import datetime
from enum import Enum
from typing import Any, List

from pydantic import (
  BaseModel,
  constr,
  NonNegativeInt,
  Field,
  root_validator,
  validator
)

from utils.base_models import ArangoDocument, ArangoEdge
from utils.dt import timestamp


class FieldType(Enum):
  TEXT_SHORT: 'text_short'
  TEXT_LONG: 'text_long'
  SINGLE_CHOICE: 'single_choice'
  MULTIPLE_CHOICE: 'multiple_choice'
  NUMBER: 'number'
  BOOLEAN: 'boolean'
  TERNARY: 'ternary'
  FILE: 'file'


# FIELD
class FormField(BaseModel):
  type: FieldType = None
  label: str
  description: str = None
  required: bool = False

class IssueField(FormField):
  value: Any = None

  @root_validator(pre=True)
  def ensure_required_value(cls, values):
    if values.get('required') and values.get('value') == None:
      raise ValueError(f'Value for field "{ values.get("label") }" is required')
    return values


# ISSUE TYPE
class IssueType(ArangoDocument):
  code: str
  name: str
  active: bool = True
  description: str = None
  icon: str = None
  template: List[FormField] = []
  critical: bool = False
  # close_within: NonNegativeInt = 0 # Time in hours. After this make critical. If 0 ignore.


# ISSUE
class Issue(ArangoDocument):
  """
  Issues can be connected to some other entity, such as Product, Phase, WorkOrder, Job, Operation, etc. To effectively track issues these links must be explicitly recorded. THis connection is stored in an edge collection.

  A job link is enough to establish within a graph single query all the relationships with Phase, Operation and Product and WorkOrder. However If the issue is raised withing the WorkOrder in general there's no graph that can help, and the product must be associated explicitly.
  """
  issue_type: str = None # _key of the issue type
  created: datetime = Field(default_factory=timestamp)
  created_by: str # Creator ID
  closed: datetime = None
  critical: bool # Default value set at the IssueType level
  # close_within: NonNegativeInt # Value set at the IssueType level
  data: List[IssueField] = None
  open: bool = True

  # Require issue type only when closing.
  @root_validator
  def ensure_type_if_closing(cls, values):
    if not open and issue_type is None:
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
  linked_to: List[IssueLink] = None # ids of entities connected

  # @validator('_from')
  # def check_from_issue(cls, value):
  #   if value.split('/')[0] != 'Issue':
  #     raise ValueError('This record is not related to an Issue')
  #   return value



# MESSAGE
class Message(ArangoDocument):
  sender: str = Field(..., alias="_from") # ID of creator (User/Machine/etc.)
  recipient: str = Field(..., alias="_to") # related issue or user
  content: str
  created: datetime = Field(default_factory=timestamp)
  updated: datetime = None
  deleted: bool = False

class IssueFullData(IssueWithLinks):
  messages: List[Message]
  history: List[dict]
