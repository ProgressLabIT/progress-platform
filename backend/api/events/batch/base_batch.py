
from events.event_model import EventModel
from events.event_type import EventType
from events.base_event import BaseEvent

from events.event_model import EventModel
from abc import ABC, abstractmethod
from typing import Set
from models.production import Job

class BaseBatchModel(EventModel):
  #Batch Fields
  batch_serials: Set[str] | None = None
  job_key: str | None = None
  work_order_key: str | None = None
  phase_key: str | None = None
  product_key: str | None = None

class BaseBatch(BaseEvent, ABC):
  event_data: BaseBatchModel

  job: Job | None = None

  from events.production.commons.job import (
    _get_job_data,
  )

  from events.production.commons.serial import (
    _create_batch_serial_records,
    _retrieve_serial_phases_data,
    _convert_field,
    _convert_form_field,
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
