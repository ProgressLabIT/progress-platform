from collections import deque
from typing import Any

from events.production.base_production import BaseProductionEvent
from models.production import WorkOrderFull, WorkStatus
from models.event import EventInfoModel
from pydantic import model_validator
from utils.production import Queries as ProductionQueries
from utils.traceability import Queries as TraceabilityQueries


class Queries:
  CANCEL_JOB_WORK_SESSIONS = """
    FOR ws IN WorkSession
    FILTER ws.job_key == @job_key && ws.canceled == null
    UPDATE ws WITH { canceled: @event_key } IN WorkSession
    RETURN NEW
  """
  NON_CANCELED_BATCHES_BY_JOB = """
    LET now = DATE_NOW()

    FOR b IN Batch
    FILTER b.job_key == @job_key && b.canceled == null
    SORT b.end DESC
    RETURN b
  """


class BaseAdmin(BaseProductionEvent):

  @property
  def event_first(self):
    return True

  def post_processing(self):
    self.update_work_order()
    self.flag_job_as_forced()

  # =================================================================================================

  def flag_job_as_forced(self):
    job_update = dict(_key=self.info.job_key, forced=self.event_key)
    self.tx.collection('Job').update(job_update)

  # =================================================================================================

  def _reduce_wip(self, wip_records, quantity):
    remaining_wip_to_remove = quantity
    wip_records = deque(wip_records)
    records_to_delete = deque()

    while remaining_wip_to_remove:
      current_wip = wip_records.popleft()

      if current_wip['quantity'] <= remaining_wip_to_remove:
        records_to_delete.append(current_wip)
        remaining_wip_to_remove -= current_wip['quantity']
      else:
        leftover_wip = current_wip['quantity'] - remaining_wip_to_remove
        new_value = round(current_wip.get('value', 0) * leftover_wip / current_wip['quantity'], 4)
        wip_update = dict(_key=current_wip['_key'], quantity=leftover_wip, value=new_value)
        self.tx.collection('wip').update(wip_update)
        remaining_wip_to_remove = 0

    self.tx.collection('wip').delete_many(records_to_delete)


  # =================================================================================================

  def _update_batch_available_states(self):
    """Updates batch available states for current and next phases"""
    wip_phases = [self.job.phase_key]

    if not self.job.last_phase:
        wip_phases.append(self.available_wip['next_phase_key'])

    self.tx.aql.execute(
        TraceabilityQueries.UPDATE_NEXT_BATCH_AVAILABLE_STATE_FOR_JOBS_IN_PHASES,
        bind_vars=dict(
            wo_key = self.job.wo_key,
            phase_keys = wip_phases
        )
    )