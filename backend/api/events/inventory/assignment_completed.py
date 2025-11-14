from events.base_event import BaseEvent
from models.event import EventInfoModel, EventType


class AssignmentCompletedEvent(BaseEvent):
  class InfoModel(EventInfoModel):
    assignment_key: str

  @classmethod
  def get_event_type(cls):
    return EventType.ASSIGNMENT_COMPLETED

  @classmethod
  def get_tx_collections(cls):
    return []

  def apply(self):
    pass

