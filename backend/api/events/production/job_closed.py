from events.base_event import BaseEvent
from models.event import EventInfoModel
from models.production import Job, WorkStatus
from utils.production import Queries as ProductionQueries
from utils.traceability import Queries as TraceabilityQueries


class JobClosedEvent(BaseEvent):
  class InfoModel(EventInfoModel):
    job_key: str
    completed_qt: float

  @classmethod
  def get_event_type(cls):
    return 'JOB_CLOSED'

  @classmethod
  def get_tx_collections(cls):
    return ['Job', 'Queue', 'WorkOrder']

  def apply(self):
    bind_vars=dict(
      job_key=self.info.job_key,
      stage=WorkStatus.CLOSED,
      notes="Job closed",
      qt_completed=self.info.completed_qt,
      end=self.info.timestamp,
    )
    completed_job = Job(**self.tx.aql.execute(
      TraceabilityQueries.COMPLETE_JOB,
      bind_vars=bind_vars
    ).next())

    self.tx.aql.execute(
      ProductionQueries.REMOVE_JOB_FROM_QUEUE,
      bind_vars=dict(
        job_key=self.info.job_key,
        target_key=self.info.user_key
      )
    )

    self.response = completed_job



