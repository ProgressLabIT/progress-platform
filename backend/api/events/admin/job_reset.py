from events.admin.progress_override_requested import ProgressOverrideRequestedEvent
from models.event import EventInfoModel, EventType


class JobResetEvent(ProgressOverrideRequestedEvent):
  """
  Resets a job to the initial state.
  Leverage ProgressOverrideRequestedEvent to reuse the logic with final quantity zero.
  """

  class InfoModel(EventInfoModel):
    job_key: str
    work_order_key: str | None = None

  @classmethod
  def get_event_type(cls):
    return EventType.JOB_RESET

  def apply(self):
    self.info.new_job_qt_completed = 0
    self.info.should_adjust_duration = True
    super().apply()
