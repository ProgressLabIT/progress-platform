from events.base_event import BaseEvent
from models.event import EventInfoModel, EventType


class CountSessionCompletedEvent(BaseEvent):
  class InfoModel(EventInfoModel):
    session_key: str

  @classmethod
  def get_event_type(cls):
    return EventType.COUNT_SESSION_COMPLETED

  @classmethod
  def get_tx_collections(cls):
    return []

  def apply(self):
    pass

