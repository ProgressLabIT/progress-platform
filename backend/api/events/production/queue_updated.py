from events.base_event import BaseEvent
from models.event import EventInfoModel, EventType


class QueueUpdatedEvent(BaseEvent):
  _notification_subtopic = "production"

  class InfoModel(EventInfoModel):
    queue_key: str

  @classmethod
  def get_event_type(cls):
    return EventType.QUEUE_UPDATED

  @classmethod
  def get_tx_collections(cls):
    return []

  def apply(self):
    pass
