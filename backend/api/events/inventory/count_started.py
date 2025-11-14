from events.base_event import BaseEvent
from models.event import EventInfoModel, EventType


class CountStartedEvent(BaseEvent):
  class InfoModel(EventInfoModel):
    count_key: str
    assignment_key: str | None = None
    inventory_key: str

  @classmethod
  def get_event_type(cls):
    return EventType.COUNT_STARTED

  @classmethod
  def get_tx_collections(cls):
    return []

  def apply(self):
    pass

