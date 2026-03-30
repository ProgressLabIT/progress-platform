from events.production.base_production import BaseProductionEvent
from events.production.batch_created import BatchCreatedEvent
from events.work_session.work_session_created import WorkSessionCreatedEvent
from models.event import EventInfoModel, EventType
from models.production import WorkStatus
from utils.production import Queries as ProductionQueries


class JobResumedEvent(BaseProductionEvent):
  class InfoModel(EventInfoModel):
    job_key: str
    batch_serials: list[str] | None = None
    work_order_key: str | None = None
    phase_key: str | None = None

  @classmethod
  def get_event_type(cls):
    return EventType.JOB_RESUMED

  def validate(self):
    if self.job.active:
      raise ValueError(f"Job {self.info.job_key} is already active.")
    if not self.job.assigned_to:
      raise ValueError(f"Job {self.info.job_key} has no assignee.")
    if not self.job.stage == WorkStatus.STARTED:
      raise ValueError(f"Job {self.info.job_key} is not started.")


  def apply(self):
    self._get_job_data()
    self.validate()


    # Create batch if none is active and store data for work session creation
    if self.job.active_batch_key:
      self.get_active_batch()
    else:
      self.batch = BatchCreatedEvent.create_as_child(self, dict(
        job_key = self.info.job_key,
        work_order_key = self.info.work_order_key,
        phase_key = self.info.phase_key,
        new_batch_serials = self.info.batch_serials,
      ))

    self.work_session = WorkSessionCreatedEvent.create_as_child(self, dict(
      job_key = self.info.job_key,
      batch_key = self.batch.key,
      work_order_key = self.info.work_order_key,
      phase_key = self.info.phase_key,
      product_key = self.info.product_key,
    ))

    self.info.work_session_key = self.work_session.key

    # Update job data
    job_update=dict(
      _key = self.info.job_key,
      last_work_session_started = self.info.work_session_key,
      active=True
    )

    if not self.job.active_batch_key:
      job_update['active_batch_key'] = self.batch.key

    job_update['active_batch_qt'] = self.batch.qt_total
    self.tx.collection('Job').update(job_update, return_new=True)['new']

    self.response = dict(
      message=f"Job {self.info.job_key} resumed",
      batch_data = self.get_batch_execution_data(),
      job_data = self.tx.aql.execute(ProductionQueries.GET_WORKING_JOB_DATA, bind_vars=dict(job_key = self.info.job_key)).next()
    )
