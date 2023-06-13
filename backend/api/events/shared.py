from models.production import WorkOrderFull, WorkStatus
from utils.production import Queries as ProductionQueries
from utils.traceability import Queries as TraceabilityQueries

class EventMeta:
  def __init__(self,
    collections,
    action,
    event_first: bool = False,
    post_processing = None
    ):
    self.collections = collections
    self.action = action
    self.post_processing = post_processing
    self.event_first = event_first



class SharedEventMethods:

  # ===================================================================
  # WorkOrder
  # ===================================================================

  def get_work_order_data(self):
    wo_data = self.tx.collection('WorkOrder').get(self.info.work_order_key)
    wo_data_out = WorkOrderFull(**wo_data)
    return wo_data_out


  def update_work_order(self):
    if not self.info.work_order_key:
      self.get_job_data()
      self.info.work_order_key = self.job.wo_key

    wo_previous_state = self.get_work_order_data()

    updated_wo = WorkOrderFull(**self.tx.aql.execute(
      TraceabilityQueries.UPDATE_WORK_ORDER,
      bind_vars=dict(wo_key=self.info.work_order_key)
    ).next())

    # Remove work order from the queue if override closed it
    if updated_wo.status == WorkStatus.CLOSED:
      self.tx.aql.execute(
        ProductionQueries.REMOVE_WORK_ORDER_FROM_QUEUE,
        bind_vars=dict(wo_key=self.info.work_order_key)
      )

    # Restore work order in the queue if override reopens it
    elif wo_previous_state.status == WorkStatus.CLOSED:
      self.tx.aql.execute(
        ProductionQueries.ADD_WORK_ORDER_TO_QUEUE,
        bind_vars=dict(new_wo_key=self.info.work_order_key)
      )

    elif getattr(self, 'job_reset', False):
      # Figure out if the wo should be reset too
      should_reset_wo = self.tx.aql.execute(
        """
        RETURN SUM(FOR j IN Job
        FILTER j.wo_key == @wo_key && j.stage != 'created'
        RETURN 1)
        """,
        bind_vars=dict(wo_key=self.info.work_order_key)
      ).next() == 0

      if should_reset_wo:
        wo_update = dict(
          _key=self.info.work_order_key,
          start = None,
          status = WorkStatus.CREATED
        )
        self.tx.collection('WorkOrder').update(wo_update)

