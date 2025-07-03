from datetime import datetime

from events.production.job_paused import JobPausedEvent
from events.work_session.work_session_closed import WorkSessionClosedEvent
from models.event import EventInfoModel, EventType
from models.production import Job


class JobPausedOfflineEvent(JobPausedEvent):
  class InfoModel(EventInfoModel):
    job_key: str
    work_session_end: datetime | None = None

  @classmethod
  def get_event_type(cls):
    return EventType.JOB_PAUSED_OFFLINE


  def post_processing(self):
    # override the post_processing method to avoid updating the job last_online field
    self.update_work_order()

  # Apply method inherited from JobPausedEvent