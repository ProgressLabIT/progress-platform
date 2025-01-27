from events.work_session.base_work_session import BaseWorkSession, BaseWorkSessionModel
from events.event_type import EventType
from events.event_model import EventModel

class WorkSessionStartedModel(BaseWorkSessionModel):
  event_type: str = EventType.WORK_SESSION_STARTED.name

class WorkSessionStarted(BaseWorkSession):
  event_data: WorkSessionStartedModel

  def set_model(self, base_model: EventModel):
    self.event_data = WorkSessionStartedModel(**base_model.model_dump())
