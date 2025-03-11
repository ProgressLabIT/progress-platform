
from events.base_event import BaseEvent
from events.production.commons.batch import BaseBatchEvent
from events.production.commons.job import BaseJobEvent
from events.production.commons.serial import BaseSerialEvent
from events.production.work_order_events import WorkOrderClosedEvent, WorkOrderStartedEvent
from models.production import WorkOrderFull, WorkStatus
from models.traceability import *
from utils.production import Queries as ProductionQueries
from utils.traceability import Queries as TraceabilityQueries


class BaseProductionEvent(BaseEvent, BaseBatchEvent, BaseJobEvent, BaseSerialEvent):

  def post_processing(self):
    self.update_job_last_online()
    self.update_work_order()


  @classmethod
  def get_tx_collections(cls) -> list[str]:
    return [
      'Batch',
      'batch_serial',
      'Event',
      'Job',
      'Queue',
      'Serial',
      'StepExecutionData',
      'wip',
      'WorkOrder',
      'WorkSession',
      'contains',
      'Config',
      'Counter',
      'is_in_position',
      'Position',
      'movement',
    ]

  def update_job_last_online(self):
    update_data = dict(
      _key=self.info.job_key,
      last_online=self.info.timestamp
    )
    self.tx.collection('Job').update(update_data)

  def get_work_order_data(self):
    wo_data = self.tx.collection('WorkOrder').get(self.info.work_order_key)
    wo_data_out = WorkOrderFull(**wo_data)
    return wo_data_out

  def get_current_work_session(self):
    match=dict(
      job_key=self.info.job_key,
      active=True
    )
    data_from_db = self.tx.collection('WorkSession').find(match).next()
    work_session = WorkSession(**data_from_db)
    return work_session

  def update_work_order(self):
    # Avoid updating work order multiple times in each child event of the main processing function
    if not self.info.primary:
      return

    if not self.info.work_order_key:
      self._get_job_data()
      self.info.work_order_key = self.job.wo_key
    wo_previous_state = self.get_work_order_data()

    updated_wo = WorkOrderFull(**self.tx.aql.execute(
      TraceabilityQueries.UPDATE_WORK_ORDER,
      bind_vars=dict(wo_key=self.info.work_order_key)
    ).next())

    # TODO: Add WORK_ORDER_STARTED and WORK_ORDER_CLOSED events, and include in them QUEUE_UPDATED events

    if wo_previous_state.status == WorkStatus.CREATED and updated_wo.status == WorkStatus.STARTED:
      WorkOrderStartedEvent.create_as_child(self, dict(
        work_order_key = self.info.work_order_key,
      ))

    # Remove work order from the queue if latest event closed it
    if wo_previous_state.status == WorkStatus.STARTED and updated_wo.status == WorkStatus.CLOSED:
      self.tx.aql.execute(
        ProductionQueries.REMOVE_WORK_ORDER_FROM_QUEUE,
        bind_vars=dict(wo_key=self.info.work_order_key)
      )
      WorkOrderClosedEvent.create_as_child(self, dict(
        work_order_key = self.info.work_order_key,
      ))
    # Restore work order in the queue if latest event reopened it
    if wo_previous_state.status == WorkStatus.CLOSED and updated_wo.status == WorkStatus.STARTED:
      self.tx.aql.execute(
        ProductionQueries.ADD_WORK_ORDER_TO_QUEUE,
        bind_vars=dict(new_wo_key=self.info.work_order_key)
      )

  def update_wip_availability_for_phases(self, phase_keys: list[str]):
    self.tx.aql.execute(
      TraceabilityQueries.UPDATE_NEXT_BATCH_AVAILABLE_STATE_FOR_JOBS_IN_PHASES,
      bind_vars=dict(wo_key=self.info.work_order_key, phase_keys=phase_keys)
    )


