
from pydantic import model_validator, Field
from models.base_models import ArangoDocument
from events.event_type import EventType
from datetime import datetime
from utils.dt import timestamp
from pydantic import Extra


class EventModel(ArangoDocument, extra=Extra.allow):
  event_type: EventType | str | None = None #
  user_key: str | None = None #
  event_group: str | None = None #
  user_session_key: str | None = None #
  timestamp: datetime = Field(default_factory=timestamp) #
  primary: bool = True
  description: str | None = None # optional descriptive field for auditing reasons
