from datetime import datetime

from events.base_event import BaseEvent
from models.event import EventInfoModel, EventType
from models.traceability import WorkSession
from utils.traceability import Queries as TraceabilityQueries


class WorkSessionClosedEvent(BaseEvent):
  class InfoModel(EventInfoModel):
    work_session_key: str
    work_session_end: datetime

  @classmethod
  def get_event_type(cls):
    return EventType.WORK_SESSION_CLOSED

  @classmethod
  def get_tx_collections(cls):
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
