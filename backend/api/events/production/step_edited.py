from events.production.base_production import BaseProductionEvent
from models.event import EventInfoModel, EventType
from models.traceability import *


class StepEditedEvent(BaseProductionEvent):
  class InfoModel(EventInfoModel):
    execution_record_key: str
    form_data: list[FormFieldValue]
    job_key: str | None = None
    batch_key: str | None = None
    work_session_key: str | None = None

  @classmethod
  def get_event_type(cls):
    return EventType.STEP_EDITED

  def apply(self):
    # Flag record as canceled
    update = dict(_key = self.info.execution_record_key, canceled = self.info.event_group)
    step_data = self.tx.collection('StepExecutionData').update(update, return_old=True)['old']

    # Set event metadata
    self.info.job_key = step_data['job_key']
    self._get_job_data()
    self.info.batch_key = self.job.active_batch_key

    # Create new StepExecutionData record
    new_step_data = StepExecutionData(
      form_data = self.info.form_data,
      job_key = self.info.job_key,
      batch_key = self.info.batch_key,
      step_key = step_data['step_key'],
      user_key = self.info.user_key,
      work_session_key = self.info.work_session_key,
      completed = self.info.timestamp,
      status = StepStatus.DONE,
      modified = self.info.event_group
    )
    self.tx.collection('StepExecutionData').insert(new_step_data)

    # Set response
    self.response = dict(
      message = f"Step edited for batch {self.info.active_batch_key}",
      job_data = self.job,
      batch_data = self.get_batch_execution_data()
    )
