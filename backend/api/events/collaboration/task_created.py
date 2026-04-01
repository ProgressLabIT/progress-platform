from datetime import date, datetime
from typing import Any

from events.base_event import EventInfoModel
from events.collaboration.base_task import BaseTaskEvent
from models.event import EventType
from models.form import TaskFormFieldValue
from models.collaboration import Task, TaskAssignment
from utils.counter import _generate_counter


class TaskCreatedEvent(BaseTaskEvent):

  class InfoModel(EventInfoModel):
    task_key: str | None = None # So it appears in the event record
    task_type_key: str
    code: str | None = None
    title: str | None = None
    description: str | None = None
    assigned_to: list[TaskAssignment] | None = []
    start_from: date | None = None
    due_by: date | None = None
    created: datetime | None = None
    created_by: str | None = None
    extra: Any | None = None

  @classmethod
  def get_tx_collections(cls):
    return ['Task', 'Counter']

  @classmethod
  def get_event_type(self):
    return EventType.TASK_CREATED


  def apply(self):
    # prepare task data
    task_data = Task(**self.info.model_dump())

    # generate task code if not provided
    if self.info.code is None:
      counter_key = self.tx.collection('Config').get('system_counters').get('tasks', 'default')
      try:
        task_data.code = _generate_counter(self.tx, counter_key)
      except Exception as e:
        raise Exception("Cannot generate task code. Please check if the counter is configured correctly.") from e

    else:
      # Check if task with the same code already exists
      if self.tx.collection('Task').find(dict(code=self.info.code)).count() > 0:
        raise ValueError(f"Task with code {self.info.code} already exists")

    # Prepare form fields
    task_type = self.tx.collection('TaskType').get(self.info.task_type_key)
    task_data.form_fields = [
      TaskFormFieldValue(
        **f,
        form_field_key=f['_key'],
        value=None
      ) for f in task_type['form_fields']
    ]

    # set created and created_by
    task_data.created = self.info.created or self.info.timestamp
    task_data.created_by = self.info.created_by or self.info.user_key

    # insert task
    task_key = self.tx.collection('Task').insert(task_data.model_dump())['_key']
    self.info.task_key = task_key

    # return response
    self.response = dict(
      message=f"Task {task_key} created successfully with code {task_data.code}",
      task_key=task_key
    )
