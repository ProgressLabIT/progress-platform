from typing import Any
from events.base_event import BaseEvent
from pydantic import model_validator
from models.production import WorkStatus, WorkOrderFull
from utils.traceability import Queries as TraceabilityQueries
from utils.production import Queries as ProductionQueries, update_target_queue

class Queries:
  CANCEL_JOB_WORK_SESSIONS = """
    FOR ws IN WorkSession
    FILTER ws.job_key == @job_key && ws.canceled == null
    UPDATE ws WITH { canceled: @event_id } IN WorkSession
    RETURN NEW
  """
  NON_CANCELED_BATCHES_BY_JOB = """
    LET now = DATE_NOW()

    FOR b IN Batch
    FILTER b.job_key == @job_key && b.canceled == null
    SORT b.end DESC
    RETURN b
    """
class BaseAdmin(BaseEvent):
    # Admin fields
    new_job_duration: int | None = None # milliseconds
    new_job_qt_completed: float | None = None
    new_job_qt_released: float | None = None
    should_adjust_duration: bool | None = None

    from events.production.commons.job import (
      set_job_active_state,
      update_job_last_online,
      _get_job_data,
      get_job_steps_count,
      update_job_step_progress,
    )

    @model_validator(mode="before")
    @classmethod
    def pre_process(cls, data: Any) -> Any:
      return data

    @classmethod
    def is_event_first(self):
      return True

    @classmethod
    def get_computed_event(self):
      return self

    @classmethod
    def get_read_collections(self):
      return list(set(super().get_read_collections() + ['WorkOrder']))

    @classmethod
    def get_write_collections(self):
      return list(set(super().get_write_collections() + ['Job']))

    def post_processing(self):
      self.update_work_order()
      self.flag_job_as_forced()

    def flag_job_as_forced(self):
       job_update = dict(_key=self.info.job_key, forced=self.id)
       self.tx.collection('Job').update(job_update)

    @classmethod
    def get_work_order_data(self):
      wo_data = self.tx.collection('WorkOrder').get(self.info.work_order_key)
      wo_data_out = WorkOrderFull(**wo_data)
      return wo_data_out

    @classmethod
    def update_work_order(self):
      if not self.info.work_order_key:
        self._get_job_data()
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

