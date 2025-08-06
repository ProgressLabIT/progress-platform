from events.base_event import BaseEvent, EventInfoModel
from models.collaboration import TaskLink
from models.event import EventType
from fastapi import HTTPException

class TaskLinkedEvent(BaseEvent):

  class InfoModel(EventInfoModel):
    task_key: str
    link_type: str
    link_key: str

  @classmethod
  def get_tx_collections(self):
    return ['task_rel']

  @classmethod
  def get_event_type(self):
    return EventType.TASK_LINKED

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

    link_exists = self.tx.collection('task_rel').find(dict(
      _from=f'Task/{self.info.task_key}',
      _to=link_id
    )).count() > 0

    if not link_exists:
      new_link = TaskLink(
        from_doc=f'Task/{self.info.task_key}',
        to_doc=link_id,
        created=self.info.timestamp,
        created_by=self.info.user_key
      )
      self.tx.collection('task_rel').insert(new_link.model_dump(by_alias=True, exclude_unset=True))

      self.response = dict(message='Task linked successfully')

    else:
      raise HTTPException(status_code=409, detail='Task already linked to this item')
