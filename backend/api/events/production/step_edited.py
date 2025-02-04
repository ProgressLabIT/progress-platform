from events.production.base_production import BaseProductionEvent, BaseProductionModel
from models.traceability import *
from models.event import EventModel
from models.event import EventType
class StepEditedModel(BaseProductionModel):
  event_type: str = EventType.STEP_EDITED.name

class StepEdited(BaseProductionEvent):
  event_data: StepEditedModel

  def set_model(self, base_model: EventModel):
    self.info = StepEditedModel(**base_model.model_dump())

  def is_event_first(self):
    return True

  def apply(self):
    self._get_job_data()
    self.get_active_batch()

    # Save current work session and batch keys in Event.info
    if not self.work_session_key:
      self.work_session = self.get_current_work_session()
      self.work_session_key = self.work_session.key

    # Flag record as canceled
    match = dict(job_key = self.info.job_key, step_key = self.info.step_key, canceled=None)
    update = dict(canceled = self.id)
    step_data = self.tx.collection('StepExecutionData').update_match(match, update)

    # Create new StepExecutionData record
    step_data = StepExecutionData(**vars(self))
    step_data.batch_key = self.info.active_batch_key
    step_data.status = StepStatus.DONE
    step_data.modified = self.id
    step_data.completed = self.timestamp
    self.tx.collection('StepExecutionData').insert(step_data)

    # Set response
    self.set_response(dict(
      message = f"Step edited for batch {self.info.active_batch_key}",
      job_data = self.job,
      batch_data = self.get_batch_execution_data()
    ))
