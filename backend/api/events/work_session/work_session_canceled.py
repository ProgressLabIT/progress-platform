from events.work_session.base_work_session import BaseWorkSession, WorkSessionEventModel
from models.event import EventType
from models.event import EventModel

class WorkSessionCanceledModel(WorkSessionEventModel):
  event_type: str = EventType.WORK_SESSION_CANCELED.name

class WorkSessionCanceledEvent(BaseWorkSession):
  event_data: WorkSessionCanceledModel

  def set_model(self, base_model: EventModel):
    self.info = WorkSessionCanceledModel(**base_model.model_dump())
