from datetime import datetime

from events.production.job_paused import JobPausedEvent
from events.work_session.work_session_closed import WorkSessionClosedEvent
from models.event import EventInfoModel, EventType
from models.production import Job


class JobPausedOffline(JobPausedEvent):
  class InfoModel(EventInfoModel):
    work_session_end: datetime | None = None

  @classmethod
  def get_event_type(cls):
    return EventType.JOB_PAUSED_OFFLINE

  def apply(self):
    self._get_job_data()
    WorkSessionClosedEvent.create_as_child(self, dict(
      job_key = self.info.work_session_key,
      work_session_end = self.info.work_session_end
    ))

    update_data = dict(
      _key=self.info.job_key,
      active=False
    )
    updated_job = self.tx.collection('Job').update(update_data, check_rev=False, return_new=True)['new']
    self.job = Job(**updated_job)
