from events.production.base_production import BaseProductionEvent
from events.work_session.work_session_closed import WorkSessionClosedEvent
from models.event import EventInfoModel, EventType
from models.production import Job


class JobPausedEvent(BaseProductionEvent):
  class InfoModel(EventInfoModel):
    job_key: str

  @classmethod
  def get_event_type(cls):
    return EventType.JOB_PAUSED

  def apply(self):
    self._get_job_data()
    if not self.job.active or self.info.work_session_key is None:
      raise ValueError("Job is not active or work session key is not set")

    WorkSessionClosedEvent.create_as_child(self, dict(
      work_session_key = self.info.work_session_key,
      work_session_end = self.info.timestamp
    ))

    update_data = dict(
      _key=self.info.job_key,
      active=False
    )
    updated_job = self.tx.collection('Job').update(update_data, check_rev=False, return_new=True)['new']
    self.job = Job(**updated_job)
