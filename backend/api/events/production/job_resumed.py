from events.production.base_production import BaseProductionEvent
from events.production.batch_created import BatchCreatedEvent
from events.work_session.work_session_created import WorkSessionCreatedEvent
from models.event import EventInfoModel, EventType
from utils.production import Queries as ProductionQueries


class JobResumed(BaseProductionEvent):
  class InfoModel(EventInfoModel):
    job_key: str

  @classmethod
  def get_event_type(cls):
    return EventType.JOB_RESUMED

  def apply(self):
    self._get_job_data()

    # Create batch if none is active and store data for work session creation
    if self.job.active_batch_key:
      self.get_active_batch()
    else:
      self.batch = BatchCreatedEvent.create_as_child(self, dict(
        job_key = self.info.job_key,
        work_order_key = self.info.work_order_key,
        phase_key = self.info.phase_key,
        batch_serials = self.info.batch_serials,
      ))

    self.work_session = WorkSessionCreatedEvent.create_as_child(self, dict(job_key = self.info.job_key))

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
