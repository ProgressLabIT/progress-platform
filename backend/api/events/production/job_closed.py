from events.base_event import BaseEvent
from models.event import EventInfoModel
from models.production import Job, WorkStatus
from utils.production import Queries as ProductionQueries
from utils.traceability import Queries as TraceabilityQueries


class JobClosedEvent(BaseEvent):
  class InfoModel(EventInfoModel):
    job_key: str
    completed_qt: float
    update_planned_qt: bool = False
    phase_key: str | None = None
    work_order_key: str | None = None
    notes: str | None = None

  @classmethod
  def get_event_type(cls):
    return 'JOB_CLOSED'

  @classmethod
  def get_tx_collections(cls):
    return ['Job', 'Queue', 'WorkOrder', 'Task']

  def apply(self):
    job_data = self.tx.collection('Job').get(self.info.job_key)
    self.info.phase_key = job_data['phase_key']
    self.info.work_order_key = job_data['wo_key']

    bind_vars=dict(
      job_key=self.info.job_key,
      stage=WorkStatus.CLOSED,
      notes=self.info.notes or "Job closed",
      qt_completed=self.info.completed_qt,
      update_planned_qt=self.info.update_planned_qt or False,
      end=self.info.timestamp,
    )
    completed_job = Job(**self.tx.aql.execute(
      TraceabilityQueries.COMPLETE_JOB,
      bind_vars=bind_vars
    ).next())

    # Remove job from the assigned user's queue, not the event user's queue
    if completed_job.assigned_to:
      self.tx.aql.execute(
        ProductionQueries.REMOVE_JOB_FROM_QUEUE,
        bind_vars=dict(
          job_key=self.info.job_key,
          target_key=completed_job.assigned_to
        )
      )

    self.response = completed_job



