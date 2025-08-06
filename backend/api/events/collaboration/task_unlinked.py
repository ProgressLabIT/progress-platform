from fastapi import HTTPException

from events.base_event import BaseEvent, EventInfoModel
from models.event import EventType

class TaskUnlinkedEvent(BaseEvent):

  class InfoModel(EventInfoModel):
    task_key: str
    link_type: str
    link_key: str

  @classmethod
  def get_tx_collections(self):
    return ['task_rel']

  @classmethod
  def get_event_type(self):
    return EventType.TASK_UNLINKED

  def apply(self):
    link_type_map = dict(
      issue='Issue',
      work_order='WorkOrder',
      product='Product',
      # equipment='Equipment',
      serial='Serial',
      task='Task'
    )

    link_collection = link_type_map[self.info.link_type]
    link_id = f'{link_collection}/{self.info.link_key}'

    deleted_count = self.tx.collection('task_rel').delete(dict(
      _from=f'Task/{self.info.task_key}',
      _to=link_id
    ))

    if deleted_count > 0:
      self.response = dict(
        message='Task unlinked successfully'
      )

    else:
      raise HTTPException(status_code=404, detail='Task not linked to this item')

