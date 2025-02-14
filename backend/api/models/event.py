from datetime import datetime
from enum import Enum
from typing import Any, Set

from arango.database import TransactionDatabase
from pydantic import BaseModel, Field, ConfigDict

from models.base_models import ArangoDocument
from models.serial import SerialLink
from utils.dt import timestamp

class EventType(str, Enum):

  # Production Events
  ACTIVE_BATCH_CHANGED = 'ACTIVE_BATCH_CHANGED'
  BATCH_COMPLETED = 'BATCH_COMPLETED'
  STEP_COMPLETED = 'STEP_COMPLETED'
  STEP_EDITED = 'STEP_EDITED'
  JOB_STARTED = 'JOB_STARTED'
  JOB_PAUSED = 'JOB_PAUSED'
  JOB_RESUMED = 'JOB_RESUMED'


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
  BATCH_CREATED = 'BATCH_CREATED'
  BATCH_CANCELED = 'BATCH_CANCELED'
  JOB_RESET = 'JOB_RESET'
  JOB_PAUSED_OFFLINE = 'JOB_PAUSED_OFFLINE'
  JOB_BACK_ONLINE = 'JOB_BACK_ONLINE'
  PROGRESS_OVERRIDE_REQUESTED = 'PROGRESS_OVERRIDE_REQUESTED'
  TIME_OVERRIDE_REQUESTED = 'TIME_OVERRIDE_REQUESTED'
  #STEP_CANCELED = 'STEP_CANCELED'
  #STEP_MODIFIED = 'STEP_MODIFIED'

  ## Serial Events
  SERIAL_BOOKED = 'SERIAL_BOOKED'
  SERIAL_CREATED = 'SERIAL_CREATED'
  SERIAL_DELETED = 'SERIAL_DELETED'
  SERIAL_LINKED = 'SERIAL_LINKED'
  SERIAL_UPDATED = 'SERIAL_UPDATED'
  SERIAL_BATCH_CONFIRMED = 'SERIAL_BATCH_CONFIRMED'
  SERIAL_DATA_UPDATED = 'SERIAL_DATA_UPDATED'
  SERIAL_RELEASED = 'SERIAL_RELEASED'

  ##Inventory Events
  MOVEMENT_COMPLETED = 'MOVEMENT_COMPLETED'
  MOVEMENT_DELETED = 'MOVEMENT_DELETED'
  INVENTORY_PRODUCED = 'INVENTORY_PRODUCED'
  INVENTORY_CONSUMED = 'INVENTORY_CONSUMED'
  MOVEMENT_CREATED = 'MOVEMENT_CREATED'
  MOVEMENT_UPDATED = 'MOVEMENT_UPDATED'
  MOVEMENT_CANCELED = 'MOVEMENT_CANCELED'
  INVENTORY_CHANGED = 'INVENTORY_CHANGED'
  WAREHOUSE_LIST_CLOSED = 'WAREHOUSE_LIST_CLOSED'
  WAREHOUSE_LIST_CREATED = 'WAREHOUSE_LIST_CREATED'

  #Work Order
  WORK_ORDER_CLOSED = 'WORK_ORDER_CLOSED'
  WORK_ORDER_STARTED = 'WORK_ORDER_STARTED'

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


class EventInfoModel(BaseModel):
  """
  Event info model to be extended by the event class
  """
  model_config = ConfigDict(extra='allow')

  event_type: EventType
  primary: bool = True
  user_key: str | None = None
  user_session_key: str | None = None
  timestamp: datetime | None = Field(default_factory=timestamp)
  description: str | None = None # optional descriptive field for auditing reasons
  event_group: str | None = None #

  # Override model_dump to exclude extra fields when saving events
  # so we don't store data from parent event in each child
  def model_dump(self, exclude_extra: bool = False, **kwargs) -> dict[str, Any]:
    if exclude_extra is True:
      kwargs["exclude"] = list(kwargs.get("exclude", [])) + list(self.model_extra.keys())
    return super().model_dump(**kwargs)

class EventModel(BaseModel):
  model_config = ConfigDict(arbitrary_types_allowed=True, extra='allow')
  tx: TransactionDatabase | None = Field(None, exclude=True)
  info: Any # model to be set at the event class level as a subclass of EventInfoModel


class SerialNotificationEventModel(ArangoDocument):
  event_type: str | EventType | None = None #
  user_key: str | None = None #
  event_group: str | None = None #
  user_session_key: str | None = None #
  timestamp: datetime = Field(default_factory=timestamp) #
  primary: bool = True
  description: str | None = None # optional descriptive field for auditing reasons
  # Traceability fields
  serial_key: Any | None = None
  serial_data: Any | None = None
  batch_serials: Set[str] | None = None # prevent duplicated entries from client
  serial_link_data: list[SerialLink] | None = None
  delete_children: bool | None = False

