from events.base_event import BaseEvent, EventInfoModel
from models.collaboration import TaskLink
from models.event import EventType
from typing import Literal

class TaskLinkedEvent(BaseEvent):

  class InfoModel(EventInfoModel):
    task_key: str
    link_type: Literal['issue', 'work_order', 'product', 'serial', 'task']
    link_key: str

  @classmethod
  def get_tx_collections(self):
    return ['task_rel']

  @classmethod
  def get_event_type(self):
    return EventType.TASK_LINKED

  @property
  def _link_type_map(self):
    return dict(
      issue='Issue',
      work_order='WorkOrder',
      product='Product',
      # equipment='Equipment',
      serial='Serial',
      task='Task'
    )

  @property
  def link_id(self):
    return f'{self._link_type_map[self.info.link_type]}/{self.info.link_key}'


  def _get_link_settings_status(self):
    """
    Get the status of the link settings for the task type.
    Returns:
      - allow_type: bool - Whether the task type can be linked to the link type
      - allow_multiple: bool - Whether the task type can be linked multiple times to the link type
      - current_links_of_type: int - The number of current links of the task type to the link type
    """
    query = """
      FOR t IN Task
      FILTER t._key == @task_key
      LET task_type = DOCUMENT(TaskType, t.task_type_key)
      LET current_links_of_type = (FOR v,e IN 1..1 OUTBOUND t task_rel FILTER PARSE_IDENTIFIER(e._to).collection == @link_collection RETURN v._key)
      LET link_already_exists = (current_links_of_type[? ANY FILTER CURRENT == @link_key]) > 0

      LET link_setting = FIRST(task_type.link_settings[* FILTER CURRENT.type == @link_type && CURRENT.enabled RETURN CURRENT])
      LET allow_type = NOT_NULL(link_setting.enabled, false)
      LET allow_multiple = NOT_NULL(link_setting.allow_multiple, false)
      RETURN { allow_type, allow_multiple, existing_links_count: LENGTH(current_links_of_type), link_already_exists }
    """
    return self.tx.aql.execute(query, bind_vars=dict(
      task_key=self.info.task_key,
      link_type=self.info.link_type,
      link_key=self.info.link_key,
      link_collection=self._link_type_map[self.info.link_type]
    )).next()

  def validate_link_settings(self):
    """
    Validate the link settings for the task type. Checks:
    - Whether the task type can be linked to the link type
    - Whether the task type can be linked multiple times to the link type
    - Whether the task is already linked to the link type

    Returns: True if the link settings are valid, Raises an HTTPException otherwise
    """
    link_settings_status = self._get_link_settings_status()
    if not link_settings_status['allow_type']:
      raise ValueError(f'Task type cannot be linked to {self.info.link_type}')

    if not link_settings_status['allow_multiple'] and link_settings_status['existing_links_count'] > 0:
      raise ValueError(f'Task type can only be linked to one {self.info.link_type}')

    if link_settings_status['link_already_exists']:
      raise ValueError('Task already linked to this item')

    return True


  # =================================================================================

  def apply(self):

    self.validate_link_settings()

    new_link = TaskLink(
      from_doc=f'Task/{self.info.task_key}',
      to_doc=self.link_id,
      created=self.info.timestamp,
      created_by=self.info.user_key
    )
    self.tx.collection('task_rel').insert(new_link.model_dump(by_alias=True, exclude_unset=True))

    self.response = dict(message='Task linked successfully')

