from datetime import datetime
from typing import Any, Set, ClassVar
from models.form import FormFieldValue
from events.base_event import BaseEvent
from pydantic import model_validator
from models.production import WorkOrderFull
from utils.traceability import Queries as TraceabilityQueries
from models.traceability import *
from utils.production import Queries as ProductionQueries
from utils.traceability import Queries as TraceabilityQueries
from models.production import Job, WorkStatus
from utils.production import Queries as ProductionQueries
from events.event_model import EventModel
from abc import ABC, abstractmethod
from utils.dt import timestamp
class BaseProductionModel(EventModel):
  # Production Fields
    work_session_key: str | None = None
    work_session_end: datetime | None = None
    job_key: str | None = None
    product_key: str | None = None
    work_order_key: str | None = None
    phase_key: str | None = None
    next_phase_key: str | None = None
    active_batch_key: str | None = None
    active_batch_qt: float | None = None
    step_key: str | None = None
    completed_batch_key: str | None = None
    completed_batch_qt: float | None = None
    new_active_batch_qt: float | None = None
    new_batch_key: str | None = None
    project_code: str | None = None
    message_key: str | None = None
    step_changed_qt: float | None = None
    form_data: list[FormFieldValue] = []

    batch_serials: Set[str] | None = None # prevent duplicated entries from client

class BaseProduction(BaseEvent, ABC):
  event_data: BaseProductionModel

  @abstractmethod
  def apply(self):
    pass

  @abstractmethod
  def set_model(self, base_model: EventModel):
    pass

  #Class variables
  job: Job | None = None
  batch: Batch | None = None
  work_session: WorkSession | None = None

  from events.production.commons.serial import(
    send_to_consumer,
    _create_batch_serial_records,
    _retrieve_serial_phases_data,
    _convert_field,
    _convert_form_field,
  )

  from events.production.commons.batch import(
    get_active_batch,
    get_batch_step_done_count,
    get_batch_execution_data,
    current_step_was_last_to_do
  )


  from events.production.commons.job import (
    set_job_active_state,
    update_job_last_online,
    _get_job_data,
    get_job_steps_count,
    update_job_step_progress,
    complete_job
  )

  @model_validator(mode="before")
  @classmethod
  def pre_process(cls, data: Any) -> Any:
    return data

  def get_write_collections(self):
    return list(set(super().get_write_collections() + [
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
      ]))

  def post_processing(self):
    self.update_job_last_online()
    self.update_work_order()

  def update_job_last_online(self):
    update_data = dict(
      _key=self.event_data.job_key,
      last_online=self.event_data.timestamp
    )
    self.tx.collection('Job').update(update_data)

  def get_work_order_data(self):
    wo_data = self.tx.collection('WorkOrder').get(self.event_data.work_order_key)
    wo_data_out = WorkOrderFull(**wo_data)
    return wo_data_out

  def get_current_work_session(self):
    match=dict(
      job_key=self.event_data.job_key,
      active=True
    )
    data_from_db = self.tx.collection('WorkSession').find(match).next()
    work_session = WorkSession(**data_from_db)
    return work_session

  def update_work_order(self):
    if not self.event_data.work_order_key:
      self._get_job_data()
      self.event_data.work_order_key = self.job.wo_key
    wo_previous_state = self.get_work_order_data()
    updated_wo = WorkOrderFull(**self.tx.aql.execute(
      TraceabilityQueries.UPDATE_WORK_ORDER,
      bind_vars=dict(wo_key=self.event_data.work_order_key)
    ).next())
    # Remove work order from the queue if override closed it
    if updated_wo.status == WorkStatus.CLOSED:
      self.tx.aql.execute(
        ProductionQueries.REMOVE_WORK_ORDER_FROM_QUEUE,
        bind_vars=dict(wo_key=self.event_data.work_order_key)
      )
    # Restore work order in the queue if override reopens it
    elif wo_previous_state.status == WorkStatus.CLOSED:
      self.tx.aql.execute(
        ProductionQueries.ADD_WORK_ORDER_TO_QUEUE,
        bind_vars=dict(new_wo_key=self.event_data.work_order_key)
      )





