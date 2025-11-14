from events.base_event import BaseEvent
from models.event import EventInfoModel, EventType


class CountCompletedEvent(BaseEvent):
  class InfoModel(EventInfoModel):
    count_key: str
    inventory_key: str

  @classmethod
  def get_event_type(cls):
    return EventType.COUNT_COMPLETED

  @classmethod
  def get_tx_collections(cls):
    return []

  def apply(self):
    pass

