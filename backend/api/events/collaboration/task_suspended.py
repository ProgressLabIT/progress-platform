from events.base_event import EventInfoModel
from events.collaboration.base_task import BaseTaskEvent
from models.collaboration import TaskStatus
from models.event import EventType


class TaskSuspendedEvent(BaseTaskEvent):

  class InfoModel(EventInfoModel):
    task_key: str

  @classmethod
  def get_tx_collections(cls):
    return ['Task']

  @classmethod
  def get_event_type(self):
    return EventType.TASK_SUSPENDED

  def apply(self):
    # Read current task to validate status
    task = self.tx.collection('Task').get(self.info.task_key)
    if task is None:
      raise ValueError(f"Task {self.info.task_key} not found")

    if task.get('status') == TaskStatus.PENDING:
      raise ValueError('Task is already pending')

    # Set status to PENDING and clear closed metadata (pending is non-terminal)
    self.tx.collection('Task').update(dict(
      _key=self.info.task_key,
      status=TaskStatus.PENDING,
      closed=None,
      closed_by=None
    ))

    self.response = dict(
      message=f"Task {self.info.task_key} set to pending",
    )
