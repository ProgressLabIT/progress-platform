from events.production.base_production import BaseProductionEvent
from models.event import EventInfoModel, EventType
from models.traceability import *


class StepEdited(BaseProductionEvent):
  class InfoModel(EventInfoModel):
    batch_key: str
    step_key: str

  @classmethod
  def get_event_type(cls):
    return EventType.STEP_EDITED

  def is_event_first(self):
    return True

  def apply(self):
    self._get_job_data()
    self.get_active_batch()

    # Save current work session and batch keys in Event.info
    self.info.work_session_key = self.job.last_work_session_started

    # Flag record as canceled
    match = dict(job_key = self.info.job_key, step_key = self.info.step_key, canceled=None)
    update = dict(canceled = self.info.event_group)
    step_data = self.tx.collection('StepExecutionData').update_match(match, update)

    # Create new StepExecutionData record
    step_data = StepExecutionData(**vars(self))
    step_data.batch_key = self.info.active_batch_key
    step_data.status = StepStatus.DONE
    step_data.modified = self.info.event_group
    step_data.completed = self.info.timestamp
    self.tx.collection('StepExecutionData').insert(step_data)

    # Set response
    self.response = dict(
      message = f"Step edited for batch {self.info.active_batch_key}",
      job_data = self.job,
      batch_data = self.get_batch_execution_data()
    )
