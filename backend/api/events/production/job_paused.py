from pydantic import BaseModel

from events.production.base_production import BaseProductionEvent, BaseProductionModel
from models.production import Job
from models.event import EventModel, EventInfoModel
from models.event import EventType
from events.work_session.work_session_closed import WorkSessionClosedEvent

class JobPausedEvent(BaseProductionEvent):
  class InfoModel(EventInfoModel):
    job_key: str

  @classmethod
  def get_event_type(cls):
    return EventType.JOB_PAUSED

  def apply(self):
    WorkSessionClosedEvent.create_as_child(self, dict(job_key = self.info.job_key))

    update_data = dict(
      _key=self.info.job_key,
      active=False
    )
    updated_job = self.tx.collection('Job').update(update_data, check_rev=False, return_new=True)['new']
    self.job = Job(**updated_job)
