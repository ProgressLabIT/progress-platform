from datetime import datetime
from enum import Enum
from typing import Any

from arango.database import TransactionDatabase
from pydantic import BaseModel, ConfigDict, Field
from utils.dt import timestamp


class EventType(str, Enum):

  # Production Events
  ACTIVE_BATCH_CHANGED = 'ACTIVE_BATCH_CHANGED'
  BATCH_COMPLETED = 'BATCH_COMPLETED'
  BATCH_RELEASED = 'BATCH_RELEASED'
  STEP_COMPLETED = 'STEP_COMPLETED'
  STEP_EDITED = 'STEP_EDITED'
  JOB_STARTED = 'JOB_STARTED'
  JOB_PAUSED = 'JOB_PAUSED'
  JOB_PAUSE_FORCED = 'JOB_PAUSE_FORCED'
  JOB_RESUMED = 'JOB_RESUMED'
  JOB_CLOSED = 'JOB_CLOSED'


  # Collaboration Events
  ISSUE_CREATED = 'ISSUE_CREATED'
  ISSUE_UPDATED = 'ISSUE_UPDATED'
  ISSUE_CLOSED = 'ISSUE_CLOSED'
  ISSUE_REOPENED = 'ISSUE_REOPENED'
  ISSUE_DELETED = 'ISSUE_DELETED'
  MESSAGE_POSTED = 'MESSAGE_POSTED'
  MESSAGE_UPDATED = 'MESSAGE_UPDATED'
  MESSAGE_DELETED = 'MESSAGE_DELETED'
  TASK_CREATED = 'TASK_CREATED'
  TASK_UPDATED = 'TASK_UPDATED'
  TASK_COMPLETED = 'TASK_COMPLETED'
  TASK_CANCELED = 'TASK_CANCELED'
  TASK_REOPENED = 'TASK_REOPENED'
  TASK_LINKED = 'TASK_LINKED'
  TASK_UNLINKED = 'TASK_UNLINKED'

  # Admin Events
  # e.g. WorkSession time Forced, etc.
  BATCH_CREATED = 'BATCH_CREATED'
  BATCH_CANCELED = 'BATCH_CANCELED'
  JOB_RESET = 'JOB_RESET'
  JOB_PAUSED_OFFLINE = 'JOB_PAUSED_OFFLINE'
  JOB_BACK_ONLINE = 'JOB_BACK_ONLINE'
  PROGRESS_OVERRIDE_REQUESTED = 'PROGRESS_OVERRIDE_REQUESTED'
  TIME_OVERRIDE_REQUESTED = 'TIME_OVERRIDE_REQUESTED'
  EXTRA_UPDATE_REQUESTED = 'EXTRA_UPDATE_REQUESTED'
  #STEP_CANCELED = 'STEP_CANCELED'
  #STEP_MODIFIED = 'STEP_MODIFIED'

  ## Serial Events
  SERIAL_BOOKED = 'SERIAL_BOOKED'
  SERIAL_CREATED = 'SERIAL_CREATED'
  SERIAL_DELETED = 'SERIAL_DELETED'
  SERIAL_LINKED = 'SERIAL_LINKED'
  SERIAL_UNLINKED = 'SERIAL_UNLINKED'
  SERIAL_UPDATED = 'SERIAL_UPDATED'
  SERIAL_BATCH_CONFIRMED = 'SERIAL_BATCH_CONFIRMED'
  SERIAL_RELEASED = 'SERIAL_RELEASED'

  ##Inventory Events
  MOVEMENT_COMPLETED = 'MOVEMENT_COMPLETED'
  MOVEMENT_DELETED = 'MOVEMENT_DELETED'
  INVENTORY_PRODUCED = 'INVENTORY_PRODUCED'
  INVENTORY_CONSUMED = 'INVENTORY_CONSUMED'
  MOVEMENT_CREATED = 'MOVEMENT_CREATED'
  MOVEMENT_PLANNED = 'MOVEMENT_PLANNED'
  MOVEMENT_UPDATED = 'MOVEMENT_UPDATED'
  MOVEMENT_REVERSED = 'MOVEMENT_REVERSED'
  MOVEMENT_CANCELED = 'MOVEMENT_CANCELED'
  INVENTORY_CHANGED = 'INVENTORY_CHANGED'
  WAREHOUSE_LIST_CLOSED = 'WAREHOUSE_LIST_CLOSED'
  WAREHOUSE_LIST_CREATED = 'WAREHOUSE_LIST_CREATED'

  # Counting Events
  ASSIGNMENT_STARTED = 'ASSIGNMENT_STARTED'
  ASSIGNMENT_COMPLETED = 'ASSIGNMENT_COMPLETED'
  COUNT_STARTED = 'COUNT_STARTED'
  COUNT_COMPLETED = 'COUNT_COMPLETED'
  COUNT_CANCELED = 'COUNT_CANCELED'
  COUNT_DISCARDED = 'COUNT_DISCARDED'
  COUNT_SESSION_STARTED = 'COUNT_SESSION_STARTED'
  COUNT_SESSION_COMPLETED = 'COUNT_SESSION_COMPLETED'
  COUNT_SESSION_APPLIED = 'COUNT_SESSION_APPLIED'
  POSITION_CONFIRMED_EMPTY = 'POSITION_CONFIRMED_EMPTY'

  #Work Order
  WORK_ORDER_CREATED = 'WORK_ORDER_CREATED'
  WORK_ORDER_CLOSED = 'WORK_ORDER_CLOSED'
  WORK_ORDER_STARTED = 'WORK_ORDER_STARTED'
  WORK_ORDER_UPDATED = 'WORK_ORDER_UPDATED' # Change of quantity, dates, reopening/admin events, etc.
  WORK_ORDER_CANCELED = 'WORK_ORDER_CANCELED' # TODO: Add to endopint

  #Work Session
  WORK_SESSION_STARTED = 'WORK_SESSION_STARTED'
  WORK_SESSION_CLOSED = 'WORK_SESSION_CLOSED'
  WORK_SESSION_CREATED = 'WORK_SESSION_CREATED'
  WORK_SESSION_CANCELED = 'WORK_SESSION_CANCELED'

  #WIP
  WIP_BOOKED = 'WIP_BOOKED'
  WIP_UNBOOKED = 'WIP_UNBOOKED'
  WIP_REMOVED = 'WIP_REMOVED'
  WIP_DECLARED = 'WIP_DECLARED'

  #Queue
  QUEUE_UPDATED = 'QUEUE_UPDATED'

class EventContextType(str, Enum):
  TASK = 'task'


class EventInfoModel(BaseModel):
  """
  Event info model to be extended by the event class
  """
  model_config = ConfigDict(extra='allow', populate_by_name=True)

  event_key: str | None = Field(None, alias='_key')
  event_type: EventType
  event_group: str | None = None #
  primary: bool = True
  context_type: str | None = None
  context_key: str | None = None
  user_key: str | None = None
  user_session_key: str | None = None
  timestamp: datetime | None = Field(default_factory=timestamp)
  description: str | None = None # optional descriptive field for auditing reasons

  # Override model_dump to exclude extra fields when saving events
  # so we don't store data from parent event in each child
  def model_dump(self, exclude_extra: bool = False, **kwargs) -> dict[str, Any]:
    if exclude_extra is True:
      kwargs["exclude"] = list(kwargs.get("exclude", [])) + list(self.model_extra.keys())
    return super().model_dump(**kwargs)

  # Context validation is done at the endpoint level once for the whole event chain

class EventModel(BaseModel):
  model_config = ConfigDict(arbitrary_types_allowed=True, extra='allow')
  tx: TransactionDatabase | None = Field(None, exclude=True)
  info: Any # model to be set at the event class level as a subclass of EventInfoModel


class BulkEventRequest(BaseModel):
  """Request model for bulk event creation. All events must be of the same type."""
  shared_data: EventInfoModel
  events: list[dict]


# class SerialNotificationEventModel(ArangoDocument):
#   event_type: str | EventType | None = None #
#   user_key: str | None = None #
#   event_group: str | None = None #
#   user_session_key: str | None = None #
#   timestamp: datetime = Field(default_factory=timestamp) #
#   primary: bool = True
#   description: str | None = None # optional descriptive field for auditing reasons
#   # Traceability fields
#   serial_key: Any | None = None
#   serial_data: Any | None = None
#   batch_serials: Set[str] | None = None # prevent duplicated entries from client
#   serial_link_data: list[SerialLink] | None = None
#   delete_children: bool | None = False

