from events.base_event import BaseEvent, EventInfoModel
from models.collaboration import TaskStatus
from models.event import EventType
class TaskCompletedEvent(BaseEvent):

  class InfoModel(EventInfoModel):
    task_key: str

  @classmethod
  def get_tx_collections(self):
    return ['Task']

  @classmethod
  def get_event_type(self):
    return EventType.TASK_COMPLETED

  @property
  def _mandatory_links_satisfied(self):
    """
    Ensure that the task has all mandatory links.
    Raises an HTTPException if any mandatory link is missing.
    """

    query = """
      LET link_type_map = {
        issue: 'Issue',
        work_order: 'WorkOrder',
        product: 'Product',
        serial: 'Serial',
        task: 'Task'
      }
      FOR t IN Task
      FILTER t._key == @task_key

      // Get unique list of collections for required links
      LET required_links = DOCUMENT(TaskType, t.task_type_key).link_settings[* FILTER CURRENT.required RETURN link_type_map[CURRENT.type]]

      // Get unique list of linked entity collections
      LET linked_entities = UNIQUE(FOR l IN 1..1 ANY t task_rel RETURN PARSE_IDENTIFIER(l._id).collection)

      // Check if all mandatory links are linked
      LET can_close = NOT_NULL(required_links[? ALL FILTER CURRENT IN linked_entities], true)
      RETURN can_close
    """

    return self.tx.aql.execute(query, bind_vars=dict(task_key=self.info.task_key)).next()



  def apply(self):
    if not self._mandatory_links_satisfied:
      raise ValueError('Task has missing mandatory links')

    self.tx.collection('Task').update(dict(
      _key=self.info.task_key,
      status=TaskStatus.COMPLETED,
      closed=self.info.timestamp,
      closed_by=self.info.user_key
    ))

    self.response = dict(
      message=f"Task {self.info.task_key} flagged as completed",
    )



