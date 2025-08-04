from events.base_event import BaseEvent, EventInfoModel
from models.form import TaskFormFieldValue

class TaskUpdatedEvent(BaseEvent):

  class InfoModel(EventInfoModel):
    task_key: str = Field(..., serialization_alias='_key')
    title: str | None = None
    description: str | None = None
    assigned_to: list[str] | None = None
    start_from: date | None = None
    due_by: date | None = None
    form_data: list[TaskFormFieldValue] | None = None

  def apply(self):

    # Exclude null values unless explicitly set and convert to dictionary
    updates = self.info.model_dump(exclude_unset=True, by_alias=True)

    if len(updates) > 1:  # More than just task_key
      updated_task = self.tx.collection('Task').update(updates, return_new=True)['new']

    self.response = dict(
      message=f"Task {self.info.task_key} updated successfully",
      detail=updated_task
    )
