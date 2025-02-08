from models.event import EventModel
from models.event import EventType
from events.base_event import BaseEvent

from models.event import EventModel, EventInfoModel
from abc import ABC, abstractmethod
from typing import Set
from models.production import Job

class BaseBatchModel(EventInfoModel):
  #Batch Fields
  batch_serials: Set[str] | None = None
  job_key: str | None = None
  work_order_key: str | None = None
  phase_key: str | None = None
  product_key: str | None = None

class BaseBatchEvent(BaseEvent, ABC):

  from events.production.commons.job import (
    _get_job_data,
  )

  from events.production.commons.serial import (
    _create_batch_serial_records,
    _retrieve_serial_phases_data,
    _convert_form_field,
  )

  @property
  def tx_collections(self):
    return list(set(super().tx_collections + [
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
