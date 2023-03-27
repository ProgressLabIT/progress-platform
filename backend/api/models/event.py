from datetime import datetime
from enum import Enum
from typing import Any, Union

from pydantic import Field

from models.quality import IssueWithLinks, Issue, Message
from utils.base_models import FlexModel
from utils.dt import timestamp

class EventType(Enum):
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
  MESSAGE_POSTED = 'MESSAGE_POSTED'
  MESSAGE_UPDATED = 'MESSAGE_UPDATED'
  MESSAGE_DELETED = 'MESSAGE_DELETED'

  # Admin Events
  # e.g. WorkSession time Forced, etc.


class EventModel(FlexModel):
  """fields marked with a comment are event attributes, the rest could be refactored into a generic "data" field, which can be defined with additional models specific for the event type."""
  key: str = Field(None, alias="_key") #
  event_type: EventType #
  user_key: str #
  user_session_key: str = None #
  timestamp: datetime = Field(default_factory=timestamp) #
  description: str = None # optional descriptive field for auditing reasons

  # Production Fields
  work_session_key: str = None
  job_key: str = None
  product_key: str = None
  work_order_key: str = None
  phase_key: str = None
  next_phase_key: str = None
  active_batch_key: str = None
  active_batch_qt: float = None
  step_key: str = None
  completed_batch_key: str = None
  completed_batch_qt: float = None
  new_batch_key: str = None
  project_code: str = None
  message_key: str = None
  user_data: Any

  # Quality Fields
  issue_data: IssueWithLinks = None
  message_data: Message = None
