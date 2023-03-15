from datetime import datetime
from enum import Enum
from typing import Any, List

from pydantic import BaseModel, root_validator

from utils.base_models import ArangoDocument, ArangoEdge
from utils.dt import timestamp

class FieldType(Enum)
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
  type: FieldType = FieldType.TEXT_SHORT
  label: str
  description: str = None
  required: bool = False

class IssueCustomData(FormField):
  value: Any = None

  @root_validator(pre=True)
  def ensure_required_value(cls, field):
    if field.get('required') and field.get('value') == None
      raise ValueError(f'Value for field { field.get('label') } is required')
    return field


# ISSUE TYPE
class IssueType(ArangoDocument):
  name: str
  description: str = None
  icon: str = None
  template: List[FormField] = None
  critical: bool = False
  close_within: int = 0 # Time in minutes. After this make critical. If 0 ignore.

# ISSUE
class Issue(ArangoDocument):
  """
  Issues can be connected to some other entity, such as Product, Phase, WorkOrder, Job, Operation, etc. To effectively track issues these links must be explicitly recorded.

  A job link is enough to establish within a graph single query all the relationships with Phase, Operation and Product and WorkOrder. However If the issue is raised withing the WorkOrder in general there's no graph that can help, and the product must be associated explicitly.
  """
  issue_type: str # _key of the issue type
  title: str
  description = str = None
  created: datetime = timestamp()
  created_by: str # Creator ID
  closed: datetime = None
  critical: bool # Default value set at the IssueType level
  close_within: int # Value set at the IssueType level
  data:
  open: bool = True


class NewIssue(Issue):
  linked_to: List[str] = None # ids of entities


# MESSAGE
class Message
