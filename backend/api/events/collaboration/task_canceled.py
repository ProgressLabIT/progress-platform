from events.base_event import EventInfoModel
from events.collaboration.base_task import BaseTaskEvent
from models.collaboration import TaskStatus
from models.event import EventType


class TaskCanceledEvent(BaseTaskEvent):

  class InfoModel(EventInfoModel):
    task_key: str
    reason: str | None = None

  @classmethod
  def get_tx_collections(cls):
    return ['Task']

  @classmethod
  def get_event_type(self):
    return EventType.TASK_CANCELED

  def apply(self):

    self.tx.collection('Task').update(dict(
      _key=self.info.task_key,
      status=TaskStatus.CANCELED,
      closed=self.info.timestamp,
      closed_by=self.info.user_key
    ))

    self.response = dict(
      message=f"Task {self.info.task_key} flagged as canceled",
    )
