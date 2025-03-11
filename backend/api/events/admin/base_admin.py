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


class BaseAdmin(BaseProductionEvent):

  @property
  def event_first(self):
    return True

  def post_processing(self):
    self.update_work_order()
    self.flag_job_as_forced()

  def flag_job_as_forced(self):
    job_update = dict(_key=self.info.job_key, forced=self.event_key)
    self.tx.collection('Job').update(job_update)
