from events.production.base_production import BaseProduction, BaseProductionModel
from utils.dt import timestamp
from models.production import Job
from utils.production import Queries as ProductionQueries
from events.event_model import EventModel
from events.event_type import EventType
from events.event_manager import EventManager
from events.work_session.work_session_created import WorkSessionCreatedModel
from events.batch.batch_created import BatchCreatedModel
class JobResumedModel(BaseProductionModel):
  event_type: str = EventType.JOB_RESUMED.name

class JobResumed(BaseProduction):
  event_data: JobResumedModel

  def set_model(self, base_model: EventModel):
    self.event_data = JobResumedModel(**base_model.model_dump())

  def apply(self):
    self._get_job_data()

    # Create batch if none is active and store data for work session creation
    if self.job.active_batch_key:
      self.get_active_batch()
    else:
      self.batch = EventManager.trigger_event(self, BatchCreatedModel(
        job_key = self.event_data.job_key,
        work_order_key = self.event_data.work_order_key,
        phase_key = self.event_data.phase_key,
        batch_serials = self.event_data.batch_serials,
      ))['new_batch_out']

    self.event_data.work_session_key = EventManager.trigger_event(self, WorkSessionCreatedModel(
      job_key = self.event_data.job_key,
      work_order_key = self.event_data.work_order_key,
      phase_key = self.event_data.phase_key,
      batch_key = self.batch.key
    ))['work_session_key']

    job_update=dict(
      _key = self.event_data.job_key,
      last_work_session_started = self.event_data.work_session_key,
      active=True
    )


    if not self.job.active_batch_key:
      job_update['active_batch_key'] = self.batch.key

    job_update['active_batch_qt'] = self.batch.qt_total
    self.tx.collection('Job').update(job_update, return_new=True)['new']

    self.set_response(dict(
      message=f"Job {self.event_data.job_key} resumed",
      batch_data = self.get_batch_execution_data(),
      job_data = self.tx.aql.execute(ProductionQueries.GET_WORKING_JOB_DATA, bind_vars=dict(job_key = self.event_data.job_key)).next()
    ))

