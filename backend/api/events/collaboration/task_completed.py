from datetime import datetime

from events.base_event import BaseEvent, EventInfoModel
from models.collaboration import TaskStatus
from models.event import EventType
from models.form import FieldType
class TaskCompletedEvent(BaseEvent):

  class InfoModel(EventInfoModel):
    task_key: str
    closed: datetime | None = None
    closed_by: str | None = None

  @classmethod
  def get_tx_collections(cls):
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


  @property
  def _mandatory_fields_satisfied(self):
    """
    Ensure that all mandatory form fields have values.
    Returns True if all mandatory fields are filled, False otherwise.
    """
    task = self.tx.collection('Task').get(self.info.task_key)
    if not task:
      return True  # Task doesn't exist, let other validations handle this

    task_form_fields = task.get('form_fields', [])
    mandatory_fields = [f for f in task_form_fields if f.get('mandatory')]
    mandatory_fields_keys = [f.get('custom_field_key') for f in mandatory_fields]

    CUSTOM_FIELDS_TYPE_QUERY = """
      RETURN MERGE(
        FOR f IN CustomField
        FILTER f._key IN @mandatory_fields_keys
        RETURN { [f._key]: f.type }
      )
    """
    if len(mandatory_fields_keys) == 0:
      return True

    mandatory_fields_map = self.tx.aql.execute(CUSTOM_FIELDS_TYPE_QUERY, bind_vars=dict(mandatory_fields_keys=mandatory_fields_keys)).next()

    # Check if all mandatory fields have valid (non-empty) values
    for field in mandatory_fields:
      field_type = mandatory_fields_map.get(field['custom_field_key'])
      if field_type == FieldType.TERNARY.value and field.get('value') is None:
        return False

      if field_type != FieldType.TERNARY.value and field.get('value') in (None, '', [], False):
        return False

    return True


  def apply(self):
    if not self._mandatory_links_satisfied:
      raise ValueError('Task has missing mandatory links')

    if not self._mandatory_fields_satisfied:
      raise ValueError('Task has missing mandatory form fields')

    self.tx.collection('Task').update(dict(
      _key=self.info.task_key,
      status=TaskStatus.COMPLETED,
      closed=self.info.closed or self.info.timestamp,
      closed_by=self.info.closed_by or self.info.user_key
    ))

    self.response = dict(
      message=f"Task {self.info.task_key} flagged as completed",
    )



