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
  TEXT = 'text'
  NUMBER = 'number'
  BOOLEAN = 'boolean'
  TERNARY = 'ternary'
  RADIO = 'radio'
  CHECKLIST = 'checklist'
  SELECT = 'select'
  DATE = 'date'
  TIME = 'time'
  # Files will added to the form through a boolean parameter in the endpoint
  # No need to specify a field of type "file"
  # In the future these will be saved as in a Media collection with metadata
  # and pointing to an object storage location

field_type_map = {
  FieldType.TEXT.value: str,
  FieldType.NUMBER.value: float,
  FieldType.BOOLEAN.value: bool,
  FieldType.TERNARY.value: Union[bool, None],
  FieldType.RADIO.value: str,
  FieldType.SELECT.value: str,
  FieldType.DATE.value: date,
  FieldType.TIME.value: time
}
# if the field model has multiple = True, the type becomes List[type]


class CustomListMeta(ArangoDocument):
  name: str
  description: str = None


class CustomListValue(ArangoDocument):
  list_key: str # Reference to CustomField
  ext_key: str = None # Optional reference to external identification, e.g. ERP id
  value: str


class CustomField(ArangoDocument):
  type: FieldType
  name: str # To search when building the form
  default_label: str # To show to the user when filling up the forms
  default_hint: str = None # To show to the user when filling up the forms
  description: str = None
  list_key: str = None

  @root_validator(pre=True)
  def ensure_list_for_selects(cls, values):
    if (values.get('type') == FieldType.SELECT
      and values.get('list_key') == None):
      raise ValueError('Select fields must have a custom list associated')
    return values

class CustomFieldInstance(BaseModel):
  field_key: str
  multiple: bool = False
  label: str = None
  hint: str = None
  default: str = None # this value should be able to be parsed to get current data
  required: bool = True
  hidden: bool = None

  @root_validator(pre=True)
  def ensure_default_for_hidden(cls, values):
    if values.get('hidden') and values.get('default') == None:
      raise ValueError('Hidden fields must have a default value')
    return values


# ISSUE TYPE
class IssueType(ArangoDocument):
  code: str
  name: str
  active: bool = True
  description: str = None
  icon: str = None
  form_template: List[CustomField] = []
  critical: bool = False
  # close_within: NonNegativeInt = 0 # Time in hours. After this make critical. If 0 ignore.


class FieldValue(BaseModel):
  field_key: str # Reference to CustomField record
  value: Any


# ISSUE
class Issue(ArangoDocument):
  """
  Issues can be connected to some other entity, such as Product, Phase, WorkOrder, Job, Operation, etc. To effectively track issues these links must be explicitly recorded. THis connection is stored in an edge collection.

  A job link is enough to establish within a graph single query all the relationships with Phase, Operation and Product and WorkOrder. However If the issue is raised within the WorkOrder in general there's no graph that can help, and the product must be associated explicitly.
  """
  issue_type: str = None # _key of the issue type
  created: datetime = Field(default_factory=timestamp)
  created_by: str # Creator ID
  closed: datetime = None
  critical: bool # Default value set at the IssueType level
  # close_within: NonNegativeInt # Value set at the IssueType level
  data: dict = None
  open: bool = True

  # Require issue type only when closing.
  @root_validator
  def ensure_type_if_closing(cls, values):
    if not values.get('open') and values.get('issue_type') is None:
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
