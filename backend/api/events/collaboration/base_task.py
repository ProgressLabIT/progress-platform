from abc import ABC, abstractmethod

from events.base_event import BaseEvent, EventInfoModel
from models.collaboration import TaskStatus
from models.production import WorkOrderFull


class BaseTaskEvent(BaseEvent, ABC):
  """
  Base class for task events that need to update job phase readiness
  when task status changes.
  """

  @classmethod
  def get_tx_collections(cls):
    return ['Task', 'Job', 'WorkOrder', 'task_rel']

  @abstractmethod
  def apply(self):
    """Override in child classes to handle specific task status updates"""
    pass

  def post_processing(self):
    """Update phase readiness for jobs after task status change"""
    self._update_phase_readiness()

  def _update_phase_readiness(self):
    """
    Check if this task affects job phase readiness and update accordingly.

    Logic:
    1. Check if task is linked to a work order
    2. Get the task's before_phase from the work order
    3. Check if all tasks with same before_phase are completed/canceled
    4. If so, set phase_ready = true for all jobs in that phase
    """

    work_order_links = self._get_work_order_links(self.info.task_key)

    if not work_order_links: # Task is not linked to a work order
      return

    # Process each linked work order
    for wo in work_order_links:
      self._update_work_order_phase_readiness(wo)

  def _get_work_order_links(self, task_key: str):
    """Get the work order links for a specific task"""

    query = """
      FOR wo IN 1..1 OUTBOUND CONCAT('Task/', @task_key) task_rel
      FILTER PARSE_IDENTIFIER(wo._id).collection == 'WorkOrder'
      RETURN wo
    """

    return [WorkOrderFull(**wo) for wo in self.tx.aql.execute(
      query,
      bind_vars=dict(task_key=task_key)
    )]

  def _update_work_order_phase_readiness(self, wo: WorkOrderFull):
    wo_task_defitition = next(task for task in wo.tasks if task.task_key == self.info.task_key)

    if wo_task_defitition.before_phase is None:
      return

    phase_readiness_update_query = """
      FOR wo IN WorkOrder
      FILTER wo._key == @wo_key

      LET phase_ready = (
        FOR task IN wo.tasks
        FILTER task.before_phase == @phase_key
        RETURN DOCUMENT(Task, task.task_key)
      )[? ALL FILTER CURRENT.status IN ['done', 'canceled']]

      FOR job IN Job
      FILTER job.wo_key == @wo_key && job.phase_key == @phase_key
      UPDATE job WITH { phase_ready } IN Job
    """

    self.tx.aql.execute(
      phase_readiness_update_query,
      bind_vars=dict(wo_key=wo.key, phase_key=wo_task_defitition.before_phase)
    )
