from datetime import datetime
from enum import Enum
from typing import Any, Union

from pydantic import Field

from models.collaboration import Message
from models.form import FormFieldValue
from utils.base_models import ArangoDocument
from utils.dt import timestamp

class EventType(str, Enum):
  # Production Events
  JOB_STARTED = 'JOB_STARTED'
  JOB_PAUSED = 'JOB_PAUSED'
  JOB_PAUSED_OFFLINE = 'JOB_PAUSED_OFFLINE'
  JOB_RESUMED = 'JOB_RESUMED'
  JOB_BACK_ONLINE = 'JOB_BACK_ONLINE'
  STEP_COMPLETED = 'STEP_COMPLETED'
  BATCH_COMPLETED = 'BATCH_COMPLETED'

  # Issue Events
  ISSUE_CREATED = 'ISSUE_CREATED'
  ISSUE_UPDATED = 'ISSUE_UPDATED'
  ISSUE_CLOSED = 'ISSUE_CLOSED'
  ISSUE_REOPENED = 'ISSUE_REOPENED'
  ISSUE_DELETED = 'ISSUE_DELETED'
  MESSAGE_POSTED = 'MESSAGE_POSTED'
  MESSAGE_UPDATED = 'MESSAGE_UPDATED'
  MESSAGE_DELETED = 'MESSAGE_DELETED'

  # Admin Events
  # e.g. WorkSession time Forced, etc.
  TIME_OVERRIDE_REQUESTED = 'TIME_OVERRIDE_REQUESTED'
  PROGRESS_OVERRIDE_REQUESTED = 'PROGRESS_OVERRIDE_REQUESTED'
  BATCH_CANCELED = 'BATCH_CANCELED'
  STEP_CANCELED = 'STEP_CANCELED'
  STEP_MODIFIED = 'STEP_MODIFIED'

  # Serial Events
  SERIAL_CREATED = 'SERIAL_CREATED'


class EventModel(ArangoDocument):
  """fields marked with a comment are event attributes, the rest could be refactored into a generic "data" field, which can be defined with additional models specific for the event type."""
  event_type: EventType #
  user_key: str #
  user_session_key: str | None = None #
  timestamp: datetime = Field(default_factory=timestamp) #
  description: str | None = None # optional descriptive field for auditing reasons

  # Production Fields
  work_session_key: str | None = None
  work_session_end: datetime | None = None
  job_key: str | None = None
  product_key: str | None = None
  work_order_key: str | None = None
  phase_key: str | None = None
  next_phase_key: str | None = None
  active_batch_key: str | None = None
  active_batch_qt: float | None = None
  step_key: str | None = None
  completed_batch_key: str | None = None
  completed_batch_qt: float | None = None
  new_batch_key: str | None = None
  project_code: str | None = None
  message_key: str | None = None
  form_data: list[FormFieldValue] = []

  # Quality Fields
  issue_data: Any | None = None
  message_data: Message | None = None

  # Admin fields
  new_job_duration: int | None = None # milliseconds
  new_job_qt_completed: float | None = None
  new_job_qt_released: float | None = None
  should_adjust_duration: bool | None = None

  # Traceability fields
  serial_data: Any | None = None
