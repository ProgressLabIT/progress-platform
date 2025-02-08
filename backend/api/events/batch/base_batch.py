from models.event import EventModel
from models.event import EventType
from events.base_event import BaseEvent

from models.event import EventModel, EventInfoModel
from abc import ABC, abstractmethod
from typing import Set
from models.production import Job
from models.serial import Serial, SerialNotificationType, SerialNotificationErrorCode
from models.form import SerialFormFieldValue
from events.serial.serial_created import SerialCreatedEvent

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

  def _create_batch_serial_records(self, quantity):
    if not self.job:
      self.job = self.get_job_data()

    batch_key = self.batch.key
    created_by = self.info.user_key
    wo_key = self.info.work_order_key
    product_key = self.info.product_key
    product = self.tx.collection('Product').get(product_key)
    counter_key = product.get('counter_key', None)

    if self.job.serialcode_on_batchstart and not counter_key:
      self.notify_results(dict(
          notification = SerialNotificationType.ERROR,
          error_code = SerialNotificationErrorCode.COUNTER_NOT_DEFINED,
          error = 'Counter not defined'
      ))
      raise ValueError(f"Counter not defined for batch {self.batch.key}")

    phases_data = self._retrieve_serial_phases_data()
    data = []
    for phase in phases_data:
      for step in phase['steps']:
        if 'form_fields' in step:
          for field in step['form_fields']:
            field_data = SerialFormFieldValue(
              form_field_key = field['_key'],
              custom_field_key = field['custom_field_key'],
              phase_key = phase['_key'],
              step_key = step['_key']
            )
            data.append(field_data)

    serial_data = Serial(
      data = data,
      created_by = 'User/'+created_by,
      user_key = created_by,
      wo_key = wo_key,
      product_key = product_key,
      counter_key = counter_key
    )

    for i in range(int(quantity)):
      SerialCreatedEvent.create_as_child(self, dict(
        batch_key = batch_key,
        counter = self.job.serialcode_on_batchstart,
        finalize = False,
        serial_data = serial_data.model_dump(),
        user_key = self.info.user_key
      ))
