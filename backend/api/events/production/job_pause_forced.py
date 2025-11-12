from events.production.job_paused import JobPausedEvent
from events.work_session.work_session_closed import WorkSessionClosedEvent
from models.event import EventInfoModel, EventType
from models.production import Job


class JobPauseForcedEvent(JobPausedEvent):
  class InfoModel(EventInfoModel):
    job_key: str
    work_order_key: str | None = None
    phase_key: str | None = None

  @classmethod
  def get_event_type(cls):
    return EventType.JOB_PAUSE_FORCED

  # Apply method inherited from JobPausedEvent
