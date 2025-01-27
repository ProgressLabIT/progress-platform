from events.work_session.base_work_session import BaseWorkSession, BaseWorkSessionModel
from events.event_type import EventType
from events.event_model import EventModel
from datetime import datetime
from models.traceability import WorkSession
from utils.traceability import Queries as TraceabilityQueries



class WorkSessionClosedModel(BaseWorkSessionModel):
  event_type: str = EventType.WORK_SESSION_CLOSED.name
  work_session_end: datetime | None = None

class WorkSessionClosed(BaseWorkSession):
  event_data: WorkSessionClosedModel

  def set_model(self, base_model: EventModel):
    self.event_data = WorkSessionClosedModel(**base_model.model_dump())

  def apply(self):
    if self.event_data.work_session_end == None:
      self.event_data.work_session_end = self.event_data.timestamp

    updated_work_session = WorkSession(**self.tx.aql.execute(
      TraceabilityQueries.CLOSE_WORK_SESSION, bind_vars = dict(
        job_key = self.event_data.job_key,
        end = self.event_data.work_session_end,
    )).next())

    self.event_data.work_session = updated_work_session
    self.event_data.work_session_key = updated_work_session.key

    return updated_work_session
