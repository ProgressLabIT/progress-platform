from events.production.base_production import BaseProductionEvent
from models.event import EventInfoModel, EventType


class WorkSessionCanceledEvent(BaseProductionEvent):
  class InfoModel(EventInfoModel):
    work_session_key: str

  @classmethod
  def get_event_type(cls):
    return EventType.WORK_SESSION_CANCELED

  def apply(self):
    ...
