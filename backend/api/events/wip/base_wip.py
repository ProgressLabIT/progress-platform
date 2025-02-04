from typing import Any, Set
from events.base_event import BaseEvent
from models.event import EventModel
from abc import ABC, abstractmethod
from managers.notification_manager import NotificationManager
from utils.traceability import Queries as TraceabilityQueries

from utils.serial import Queries
import copy
import json
from models.serial import Serial, SerialNotificationType
from models.production import Job

from utils.dt import timestamp

class BaseWIPModel(EventModel):
   # WIP Fields
  job_key: str | None = None
  work_order_key: str | None = None
  phase_key: str | None = None
  batch_key: str | None = None


class BaseWIP(BaseEvent, ABC):
  event_data: BaseWIPModel

  job: Job | None = None

  from events.production.commons.job import (
    _get_job_data,
  )

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
        'Counter'
      ]))

  @abstractmethod
  def apply(self):
    pass

  @abstractmethod
  def set_model(self, base_model: EventModel):
    pass


  def update_wip_availability_for_phases(self, phase_keys: list[str]):
    self.tx.aql.execute(
      TraceabilityQueries.UPDATE_NEXT_BATCH_AVAILABLE_STATE_FOR_JOBS_IN_PHASES,
      bind_vars=dict(wo_key=self.work_order_key, phase_keys=phase_keys)
    )
