from events.work_session.base_work_session import BaseWorkSession, BaseWorkSessionModel
from events.event_type import EventType
from events.event_model import EventModel

class WorkSessionCanceledModel(BaseWorkSessionModel):
  event_type: str = EventType.WORK_SESSION_CANCELED.name

class WorkSessionCanceled(BaseWorkSession):
  event_data: WorkSessionCanceledModel

  def set_model(self, base_model: EventModel):
    self.event_data = WorkSessionCanceledModel(**base_model.model_dump())
