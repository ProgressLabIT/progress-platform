from datetime import datetime
from typing import Any, Set

from pydantic import Field

from models.base_models import ArangoDocument
from utils.dt import timestamp
from models.serial import SerialLink
from models.inventory import *
from events.event_type import EventType



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

