from models.production import WorkOrderFull, WorkStatus
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

    updated_wo = self.tx.aql.execute(
      TraceabilityQueries.UPDATE_WORK_ORDER,
      bind_vars=dict(wo_key=self.info.work_order_key)
    ).next()

    if updated_wo['status'] == WorkStatus.CLOSED.value:
      self.tx.aql.execute(
        ProductionQueries.REMOVE_WORK_ORDER_FROM_QUEUE,
        bind_vars=dict(wo_key=self.info.work_order_key)
      )
