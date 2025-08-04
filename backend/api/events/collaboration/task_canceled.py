from events.base_event import BaseEvent, EventInfoModel
from models.collaboration import TaskStatus


class TaskCancelledEvent(BaseEvent):

  class InfoModel(EventInfoModel):
    task_key: str

  def apply(self):
    self.tx.collection('Task').update(dict(
      _key=self.info.task_key,
      status=TaskStatus.CANCELED,
      closed=self.info.timestamp
    ))

    self.response = dict(
      message=f"Task {self.info.task_key} flagged as canceled",
    )
