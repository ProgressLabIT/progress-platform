from events.base_event import EventInfoModel
from events.collaboration.base_task import BaseTaskEvent
from models.event import EventType


class TaskDeletedEvent(BaseTaskEvent):

  class InfoModel(EventInfoModel):
    task_key: str

  @classmethod
  def get_tx_collections(cls):
    return ['Task', 'task_rel']

  @classmethod
  def get_event_type(cls):
    return EventType.TASK_DELETED

  def apply(self):
    task_key = self.info.task_key

    # Check whether any events beyond TASK_CREATED reference this task.
    # LIMIT 1 keeps the scan fast; we only need existence, not count.
    has_history = self.tx.aql.execute(
      """
      RETURN LENGTH(
        FOR e IN Event
          FILTER e.task_key == @task_key AND e.event_type != 'TASK_CREATED'
          LIMIT 1
          RETURN 1
      )
      """,
      bind_vars=dict(task_key=task_key)
    ).next()

    if has_history == 0:
      # Hard delete: no audit trail to preserve
      self.tx.collection('Task').delete(task_key)
      self.tx.collection('task_rel').delete_match(dict(_from=f'Task/{task_key}'))
      self.tx.collection('task_rel').delete_match(dict(_to=f'Task/{task_key}'))
      self.tx.aql.execute(
        """
        FOR e IN Event
          FILTER e.task_key == @task_key AND e.event_type == 'TASK_CREATED'
          REMOVE e IN Event
        """,
        bind_vars=dict(task_key=task_key)
      )
      self.response = dict(
        message=f"Task {task_key} permanently deleted",
        mode='hard',
      )
    else:
      # Soft delete: preserve history, hide from all listings
      self.tx.collection('Task').update(dict(
        _key=task_key,
        deleted=self.info.timestamp,
        deleted_by=self.event_key,
      ))
      self.response = dict(
        message=f"Task {task_key} hidden from results (history preserved)",
        mode='soft',
      )
