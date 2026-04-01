from datetime import datetime

from events.production.job_paused import JobPausedEvent
from models.event import EventInfoModel, EventType
from models.production import Job


class JobPausedOfflineEvent(JobPausedEvent):
  _notification_subtopic = "production"

  class InfoModel(EventInfoModel):
    job_key: str
    work_session_end: datetime | None = None
    work_order_key: str | None = None
    phase_key: str | None = None

  @classmethod
  def get_event_type(cls):
    return EventType.JOB_PAUSED_OFFLINE

  def post_processing(self):
    self.update_work_order()
