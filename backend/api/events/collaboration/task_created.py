from datetime import datetime, date

from events.base_event import BaseEvent, EventInfoModel
from models.form import TaskFormFieldValue
from models.collaboration import Task
from utils.counter import _generate_counter


class TaskCreatedEvent(BaseEvent):

  class InfoModel(EventInfoModel):
    task_type: str
    task_key: str | None = None
    code: str | None = None
    assigned_to: list[str]
    start_from: date | None = None
    due_by: date | None = None
    form_data: list[TaskFormFieldValue] | None = None


  def apply(self):
    # prepare task data
    task_data = Task(**self.info.model_dump())

    # generate task code if not provided
    if self.info.code is not None:
      counter_key = self.tx.collection('Config').get('system_counters')['tasks']
      task_data.code = _generate_counter(self.tx, counter_key)

    # insert task
    task_key = self.tx.collection('Task').insert(task_data.model_dump())['_key']
    self.info.task_key = task_key

    self.response = dict(
      message=f"Task {task_key} created successfully with code {task_data.code}",
      task_key=task_key
    )
