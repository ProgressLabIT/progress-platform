from events.work_session.base_work_session import BaseWorkSession, WorkSessionEventModel
from models.event import EventType
from models.event import EventModel
from datetime import datetime
from models.traceability import WorkSession
from utils.traceability import Queries as TraceabilityQueries


class WorkSessionClosedEvent(BaseWorkSession):
  class InfoModel(WorkSessionEventModel):
    work_session_end: datetime | None = None

  @classmethod
  def get_event_type(cls):
    return EventType.WORK_SESSION_CLOSED

  @property
  def tx_collections(self):
    return [
      'WorkSession'
    ]

  def apply(self):
    if self.info.work_session_end == None:
      self.info.work_session_end = self.info.timestamp

    updated_work_session = WorkSession(**self.tx.aql.execute(
      TraceabilityQueries.CLOSE_WORK_SESSION, bind_vars = dict(
        job_key = self.info.job_key,
        end = self.info.work_session_end,
    )).next())

    return updated_work_session
