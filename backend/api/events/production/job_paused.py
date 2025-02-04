from events.production.base_production import BaseProductionEvent, BaseProductionModel
from models.production import Job
from models.event import EventModel
from models.event import EventType
from events.work_session.work_session_closed import WorkSessionClosedModel
from events.event_manager import EventManager
class JobPausedModel(BaseProductionModel):
  event_type: str = EventType.JOB_PAUSED.name

class JobPausedEvent(BaseProductionEvent):
  event_data: JobPausedModel

  def set_model(self, base_model: EventModel):
    self.event_data = JobPausedModel(**base_model.model_dump())

  def apply(self):
    EventManager.trigger_event(self, WorkSessionClosedModel(
      job_key = self.event_data.job_key,
      work_session_end = self.event_data.work_session_end
    ));

    update_data = dict(
      _key=self.event_data.job_key,
      active=False
    )
    updated_job = self.tx.collection('Job').update(update_data, check_rev=False, return_new=True)['new']
    self.job = Job(**updated_job)
