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
  name: str = Field(
    ...,
    description="Human-readable name for this issue type, shown in the UI.",
    examples=["Inspection Failure"],
  )
  code: str | None = Field(
    None,
    description="Short alphanumeric code used to identify the issue type in reports and forms.",
    examples=["INSP-FAIL"],
  )
  active: bool = Field(
    True,
    description="Whether this issue type is available for selection when creating new issues.",
    examples=[True],
  )
  description: str | None = Field(
    None,
    description="Extended description of the issue type, explaining when it should be used.",
    examples=["Used when an inspection step fails due to dimensional non-conformance."],
  )
  icon: str | None = Field(
    None,
    description="Icon identifier string used by the frontend to render a visual cue for this type.",
    examples=["warning"],
  )
  form_template: list[FormFieldDefinition] = Field(
    default_factory=list,
    description="Ordered list of form field definitions that must be filled when creating an issue of this type.",
  )
  critical: bool = Field(
    False,
    description="Whether issues of this type are automatically flagged as critical on creation.",
    examples=[False],
  )
  # close_within: NonNegativeInt = 0 # Time in hours. After this make critical. If 0 ignore.


class IssueTypeUpdate(BaseModel):
  key: str | None = Field(
    None,
    alias='_key',
    description="ArangoDB document key of the issue type to update.",
    examples=["issuetype_001"],
  )
  code: str | None = Field(
    None,
    description="Updated short code for the issue type.",
    examples=["INSP-FAIL"],
  )
  name: str | None = Field(
    None,
    description="Updated display name for the issue type.",
    examples=["Inspection Failure"],
  )
  active: bool | None = Field(
    None,
    description="Set to `false` to archive the issue type without deleting it.",
    examples=[True],
  )
  description: str | None = Field(
    None,
    description="Updated description for the issue type.",
    examples=["Used when an inspection step fails due to dimensional non-conformance."],
  )
  icon: str | None = Field(
    None,
    description="Updated icon identifier.",
    examples=["warning"],
  )
  form_template: list[FormFieldDefinition] = Field(
    default_factory=list,
    description="Replacement form template for this issue type. Replaces the existing template entirely.",
  )
  critical: bool = Field(
    False,
    description="Whether issues of this type are automatically flagged as critical.",
    examples=[False],
  )


class IssueTypeFull(IssueType):
  print_templates: list[PrintTemplateRecord] | None = Field(
    None,
    description="Print templates associated with this issue type.",
  )


class Issue(ArangoDocument):
  """
  Issues can be connected to some other entity, such as Product, Phase, WorkOrder, Job, Operation, etc. To effectively track issues these links must be explicitly recorded. THis connection is stored in an edge collection.

  A job link is enough to establish within a graph single query all the relationships with Phase, Operation and Product and WorkOrder. However If the issue is raised within the WorkOrder in general there's no graph that can help, and the product must be associated explicitly.
  """
  issue_type_key: str | None = Field(
    None,
    description="ArangoDB `_key` of the `IssueType` this issue belongs to. Required when closing an issue.",
    examples=["issuetype_001"],
  )
  created: datetime = Field(
    default_factory=timestamp,
    description="UTC timestamp at which this issue was created.",
    examples=["2026-05-04T09:15:00Z"],
  )
  created_by: str = Field(
    ...,
    description="Document ID of the User or entity that created this issue (e.g. `User/user42`).",
    examples=["User/user42"],
  )
  closed: datetime | None = Field(
    None,
    description="UTC timestamp at which this issue was closed. `null` while still open.",
    examples=["2026-05-04T11:30:00Z"],
  )
  closed_by: str | None = Field(
    None,
    description="Document ID of the User who closed this issue.",
    examples=["User/user42"],
  )
  critical: bool = Field(
    ...,
    description="Whether this issue is flagged as critical. Inherited from the `IssueType.critical` field at creation time.",
    examples=[False],
  )
  # close_within: NonNegativeInt # Value set at the IssueType level
  data: list[FormFieldValue] | None = Field(
    None,
    description="Form field values collected when the issue was created, according to the issue type's form template.",
  )
  open: bool = Field(
    True,
    description="Whether the issue is currently open. Set to `false` to close the issue.",
    examples=[True],
  )

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
  type: IssueLinkType = Field(
    ...,
    description="Category of entity this issue is linked to.",
    examples=["work_order"],
  )
  key: str = Field(
    ...,
    description="ArangoDB `_key` of the linked entity.",
    examples=["wo_2026_001"],
  )


class IssueWithLinks(Issue):
  linked_to: list[IssueLink] = Field(
    default_factory=list,
    description="Graph relationships connecting this issue to other entities (products, jobs, work orders, etc.).",
  )

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
  sender: str = Field(
    ...,
    alias="_from",
    description="Document ID of the entity that sent this message (e.g. `User/user42`).",
    examples=["User/user42"],
  )
  recipient: str = Field(
    ...,
    alias="_to",
    description="Document ID of the recipient entity — typically an `Issue` or `User` document ID.",
    examples=["Issue/issue_001"],
  )
  content: str | None = Field(
    None,
    description="Plain-text or markdown body of the message.",
    examples=["Inspection failed at step 3 — dimensional check out of tolerance."],
  )
  created: datetime | None = Field(
    default_factory=timestamp,
    description="UTC timestamp at which the message was posted.",
    examples=["2026-05-04T10:00:00Z"],
  )
  updated: datetime | None = Field(
    None,
    description="UTC timestamp of the most recent edit, or `null` if never edited.",
    examples=["2026-05-04T10:05:00Z"],
  )
  deleted: datetime | None = Field(
    None,
    description="UTC timestamp at which the message was soft-deleted, or `null` if still active.",
    examples=[None],
  )

class MessageUpdate(ArangoDocument):
  sender: str = Field(
    ...,
    alias="_from",
    description="Document ID of the original message sender.",
    examples=["User/user42"],
  )
  recipient: str = Field(
    ...,
    alias="_to",
    description="Document ID of the message recipient.",
    examples=["Issue/issue_001"],
  )
  content: str | None = Field(
    None,
    description="Updated message body.",
    examples=["Inspection failed at step 3 — dimensional check out of tolerance. Rework in progress."],
  )
  updated: datetime | None = Field(
    None,
    description="Timestamp to record when this update was applied.",
    examples=["2026-05-04T10:05:00Z"],
  )
  deleted: datetime | None = Field(
    None,
    description="Set to a timestamp to soft-delete this message.",
    examples=[None],
  )

class IssueFullData(IssueWithLinks):
  messages: list[Message] = Field(
    ...,
    description="All messages posted to this issue, sorted by creation time.",
  )
  history: list[dict] = Field(
    ...,
    description="Audit log of state transitions and field changes recorded against this issue.",
  )


# ==============================================================================
# TASKS
# ==============================================================================

class TaskLinkType(str, Enum):
  ISSUE = 'issue'
  WORK_ORDER = 'work_order'
  PRODUCT = 'product'
  # EQUIPMENT = 'equipment'
  SERIAL = 'serial'
  TASK = 'task'

class TaskLinkedEntitySettings(BaseModel):
  type: TaskLinkType = Field(
    ...,
    description="Category of entity that can be linked to tasks of this type.",
    examples=["issue"],
  )
  enabled: bool | None = Field(
    False,
    description="Whether linking to this entity type is enabled for the parent task type.",
    examples=[True],
  )
  allow_multiple: bool | None = Field(
    False,
    description="Whether a task can be linked to multiple entities of this type simultaneously.",
    examples=[False],
  )
  required: bool | None = Field(
    False,
    description="Whether at least one link to this entity type is required before the task can be completed.",
    examples=[False],
  )


def set_default_task_linked_entity_settings():
  return [
    TaskLinkedEntitySettings(type=TaskLinkType.ISSUE),
    TaskLinkedEntitySettings(type=TaskLinkType.WORK_ORDER),
    TaskLinkedEntitySettings(type=TaskLinkType.PRODUCT),
    # TaskLinkedEntitySettings(type=TaskLinkType.EQUIPMENT),
    TaskLinkedEntitySettings(type=TaskLinkType.SERIAL),
    TaskLinkedEntitySettings(type=TaskLinkType.TASK)
  ]


class TaskType(ArangoDocument):
  name: str = Field(
    ...,
    description="Display name of this task type, shown in the UI when creating or filtering tasks.",
    examples=["Quality Inspection"],
  )
  description: str | None = Field(
    None,
    description="Optional extended description of the task type and its intended use.",
    examples=["Covers all quality checks mandated by the production process."],
  )
  active: bool | None = Field(
    True,
    description="Whether this task type is available for selection when creating new tasks.",
    examples=[True],
  )
  icon: str | None = Field(
    None,
    description="Icon identifier used by the frontend to render a visual indicator for tasks of this type.",
    examples=["check_circle"],
  )
  created: datetime = Field(
    default_factory=timestamp,
    description="UTC timestamp at which this task type was created.",
    examples=["2026-05-01T08:00:00Z"],
  )
  form_fields: list[FormFieldDefinition] | None = Field(
    default_factory=list,
    description="Form field definitions that operators must fill when working on a task of this type.",
  )
  link_settings: list[TaskLinkedEntitySettings] | None = Field(
    default_factory=set_default_task_linked_entity_settings,
    description="Per-entity-type linking rules. Controls which entity types can or must be linked.",
  )
  require_time_entry: bool | None = Field(
    False,
    description="Whether a time entry is required before the task can be marked complete.",
    examples=[False],
  )


class TaskTypeFull(TaskType):
  print_templates: list[PrintTemplateRecord] | None = Field(
    None,
    description="Print templates associated with this task type.",
  )


class TaskStatus(str, Enum):
  PENDING = "pending"
  OPEN = "open"
  COMPLETED = "completed"
  CANCELED = "canceled"



class TaskAssignmentRole(str, Enum):
  OWNER = 'owner'
  PARTICIPANT = 'participant'

class TaskAssignment(BaseModel):
  user_key: str = Field(
    ...,
    description="ArangoDB `_key` of the User assigned to this task.",
    examples=["user42"],
  )
  role: TaskAssignmentRole | None = Field(
    TaskAssignmentRole.PARTICIPANT,
    description="Role of this user in the task: `owner` (exactly one required) or `participant`.",
    examples=["participant"],
  )

class Task(ArangoDocument):
  task_type_key: str = Field(
    ...,
    description="ArangoDB `_key` of the `TaskType` this task belongs to.",
    examples=["tasktype_001"],
  )
  code: Annotated[str, StringConstraints(to_upper=True, strip_whitespace=True, min_length=1)] | None = Field(
    None,
    description="Optional short alphanumeric code for this task, stored in uppercase.",
    examples=["TASK-2026-001"],
  )
  status: TaskStatus | None = Field(
    TaskStatus.OPEN,
    description="Current lifecycle status of the task.",
    examples=["open"],
  )
  owner_key: str | None = Field(
    None,
    description="ArangoDB `_key` of the user who owns this task. Derived from `assigned_to` on save.",
    examples=["user42"],
  )
  assigned_to: list[TaskAssignment] | None = Field(
    default_factory=list,
    description="List of user assignments. Must include exactly one `owner` role when non-empty.",
  )
  start_from: datetime | None = Field(
    None,
    description="Earliest date/time from which work on this task can begin.",
    examples=["2026-05-05T08:00:00Z"],
  )
  due_by: datetime | None = Field(
    None,
    description="Deadline by which this task must be completed.",
    examples=["2026-05-10T17:00:00Z"],
  )
  created: datetime | None = Field(
    None,
    description="UTC timestamp at which this task was created.",
    examples=["2026-05-04T09:00:00Z"],
  )
  created_by: str | None = Field(
    None,
    description="ArangoDB `_key` of the User who created this task.",
    examples=["user42"],
  )
  closed: datetime | None = Field(
    None,
    description="UTC timestamp at which this task was completed or canceled.",
    examples=["2026-05-08T14:00:00Z"],
  )
  closed_by: str | None = Field(
    None,
    description="ArangoDB `_key` of the User who closed this task.",
    examples=["user42"],
  )
  title: str | None = Field(
    None,
    description="Short title describing what needs to be done.",
    examples=["Verify dimensional tolerance after rework"],
  )
  description: str | None = Field(
    None,
    description="Detailed description of the task, including acceptance criteria or instructions.",
    examples=["Check all 6 key dimensions against drawing rev. B. All must be within ±0.1 mm."],
  )
  form_fields: list[TaskFormFieldValue] | None = Field(
    default_factory=list,
    description="Form field values collected during task execution.",
  )

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
  created: datetime = Field(
    default_factory=timestamp,
    description="UTC timestamp at which this task-entity link was created.",
    examples=["2026-05-04T09:00:00Z"],
  )
  created_by: str | None = Field(
    None,
    description="ArangoDB `_key` of the User who created this link.",
    examples=["user42"],
  )

class TaskSearchParameters(BaseModel):
  search: str | None = Field(
    None,
    description="Free-text search string matched against task title and description.",
    examples=["rework"],
  )
  task_type_key: str | None = Field(
    None,
    description="Filter to tasks belonging to a specific task type.",
    examples=["tasktype_001"],
  )
  status_pending: bool | None = Field(
    None,
    description="Include tasks with status `pending` when `true`.",
    examples=[True],
  )
  status_open: bool | None = Field(
    None,
    description="Include tasks with status `open` when `true`.",
    examples=[True],
  )
  status_completed: bool | None = Field(
    None,
    description="Include tasks with status `completed` when `true`.",
    examples=[False],
  )
  status_canceled: bool | None = Field(
    None,
    description="Include tasks with status `canceled` when `true`.",
    examples=[False],
  )
  owner_key: str | None = Field(
    None,
    description="Filter to tasks owned by a specific user.",
    examples=["user42"],
  )
  assigned_to: list[str] | None = Field(
    None,
    description="Filter to tasks assigned to any of the listed user keys.",
    examples=[["user42", "user99"]],
  )
  start_from_min: date | None = Field(
    None,
    description="Lower bound for the `start_from` date filter (inclusive).",
    examples=["2026-05-01"],
  )
  start_from_max: date | None = Field(
    None,
    description="Upper bound for the `start_from` date filter (inclusive).",
    examples=["2026-05-31"],
  )
  due_by_min: date | None = Field(
    None,
    description="Lower bound for the `due_by` date filter (inclusive).",
    examples=["2026-05-01"],
  )
  due_by_max: date | None = Field(
    None,
    description="Upper bound for the `due_by` date filter (inclusive).",
    examples=["2026-05-31"],
  )
  created_min: date | None = Field(
    None,
    description="Lower bound for the `created` date filter (inclusive).",
    examples=["2026-05-01"],
  )
  created_max: date | None = Field(
    None,
    description="Upper bound for the `created` date filter (inclusive).",
    examples=["2026-05-31"],
  )
  closed_min: date | None = Field(
    None,
    description="Lower bound for the `closed` date filter (inclusive).",
    examples=["2026-05-01"],
  )
  closed_max: date | None = Field(
    None,
    description="Upper bound for the `closed` date filter (inclusive).",
    examples=["2026-05-31"],
  )
  advanced_filters: dict | None = Field(
    None,
    description="Additional filter criteria as a JSON object (or base64-encoded JSON string, decoded by validator).",
  )

  # Linked entity filters
  issue_key: str | None = Field(
    None,
    description="Filter to tasks linked to a specific issue.",
    examples=["issue_001"],
  )
  work_order_key: str | None = Field(
    None,
    description="Filter to tasks linked to a specific work order.",
    examples=["wo_2026_001"],
  )
  product_key: str | None = Field(
    None,
    description="Filter to tasks linked to a specific product.",
    examples=["prod_abc"],
  )
  serial_key: str | None = Field(
    None,
    description="Filter to tasks linked to a specific serial number record.",
    examples=["serial_xyz"],
  )
  linked_task_key: str | None = Field(
    None,
    description="Filter to tasks linked to another specific task.",
    examples=["task_001"],
  )

  limit: int | None = Field(
    200,
    description="Maximum number of results to return. Defaults to 200.",
    examples=[200],
  )
  offset: int | None = Field(
    0,
    description="Number of results to skip for pagination.",
    examples=[0],
  )

  @field_validator('advanced_filters', mode='before')
  @classmethod
  def deserialize_base64(cls, value: str | None) -> dict | list[str] | None:
    if isinstance(value, str):
      return json.loads(b64decode(value).decode('latin-1'))
    return value


class TaskSearchResult(Task):
  icon: str | None = Field(
    None,
    description="Icon identifier from the task's `TaskType`, denormalised for display.",
    examples=["check_circle"],
  )
  task_type_name: str | None = Field(
    None,
    description="Display name of the task's `TaskType`, denormalised for display.",
    examples=["Quality Inspection"],
  )
