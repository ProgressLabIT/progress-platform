import json
import traceback

from fastapi import HTTPException

from commons.kafka_utils.kafka_producer import KafkaProducer
from commons.models.serial import Serial, SerialEvent, SerialCommandType
from commons.models.form import SerialFormFieldValue
from managers.serial_event_manager import SerialEventManager


# ===================================================================
# Serial
# ===================================================================

def send_to_consumer(self, serial_event):
  try:
    KafkaProducer.getInstance().produce_async(topic="serials", key=serial_event.get('_key'), value=json.dumps(serial_event))
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error managing the serial.",
        error=traceback.format_exc()
      )
    )

def create_serial(self):
  '''serial_data = jsonable_encoder(Serial(**self.info.serial_data))
  serial_event = SerialEvent()
  setattr(serial_event, 'serial', serial_data)
  setattr(serial_event, 'operation', SerialCommandType.CREATE_AND_FINALIZE)
  self.send_to_consumer(serial_event.dict())'''
  SerialEventManager.getInstance().handle_event(self, SerialCommandType.CREATE_AND_FINALIZE)

def link_serial(self):
  '''serial_event = SerialEvent()
  setattr(serial_event, 'serial_link_data', self.info.serial_link_data)
  setattr(serial_event, 'operation', SerialCommandType.LINK_SERIALS)
  self.send_to_consumer(serial_event.dict())'''
  SerialEventManager.getInstance().handle_event(self, SerialCommandType.LINK_SERIALS)


def update_serial(self):
  '''serial_data = jsonable_encoder(Serial(**self.info.serial_data))
  serial_event = SerialEvent()
  setattr(serial_event, 'serial', serial_data)
  setattr(serial_event, 'operation', SerialCommandType.UPDATE)
  self.send_to_consumer(serial_event.dict())'''
  SerialEventManager.getInstance().handle_event(self, SerialCommandType.UPDATE)


def delete_serial(self):
  '''serial_data = jsonable_encoder(Serial(**self.info.serial_data))
  serial_event = SerialEvent()
  setattr(serial_event, 'serial', serial_data)
  setattr(serial_event, 'operation', SerialCommandType.DELETE)
  self.send_to_consumer(serial_event.dict())'''
  SerialEventManager.getInstance().handle_event(self, SerialCommandType.DELETE)

def create_batch_serial_records(self, quantity):
  if not self.job:
    self.job = self.get_job_data()

  '''serial_event = SerialEvent()
  setattr(serial_event, 'created_by', self.info.user_key)
  setattr(serial_event, 'wo_key', self.info.work_order_key)
  setattr(serial_event, 'product_key', self.info.product_key)
  setattr(serial_event, 'quantity', quantity)
  setattr(serial_event, 'batch_key', self.batch.key)
  setattr(serial_event, 'operation', SerialEventType.CREATE_FROM_BATCH)
  #self.send_to_consumer(serial_event.dict())

  batch_key = self.batch.key
  created_by = self.info.user_key
  wo_key = self.info.work_order_key
  product_key = self.info.product_key'''

  SerialEventManager.getInstance().handle_event(self, SerialCommandType.CREATE_FROM_BATCH, quantity=quantity)


def finalize_batch_serial(self, wo, completed_batch_qt = None):
  '''if not self.job:
    self.job = self.get_job_data()

  serial_event = SerialEvent()
  setattr(serial_event, 'created_by', self.info.user_key)
  setattr(serial_event, 'wo_key', self.info.work_order_key)
  setattr(serial_event, 'product_key', self.info.product_key)
  setattr(serial_event, 'quantity', completed_batch_qt or self.info.active_batch_qt)
  setattr(serial_event, 'batch_key', self.info.active_batch_key)
  setattr(serial_event, 'traceability_level', self.job.traceability_level)
  setattr(serial_event, 'last_phase', self.job.last_phase)
  setattr(serial_event, 'operation', SerialCommandType.FINALIZE_BATCH)
  self.send_to_consumer(serial_event.dict())'''

  SerialEventManager.getInstance().handle_event(self, SerialCommandType.FINALIZE_BATCH, quantity=completed_batch_qt or self.info.active_batch_qt)

def finalize_wo_serial(self):
  '''if not self.job:
    self.job = self.get_job_data()

  serial_event = SerialEvent()
  setattr(serial_event, 'created_by', self.info.user_key)
  setattr(serial_event, 'wo_key', self.info.work_order_key)
  setattr(serial_event, 'product_key', self.info.product_key)
  setattr(serial_event, 'quantity', completed_batch_qt)
  setattr(serial_event, 'batch_key', self.info.active_batch_key)
  setattr(serial_event, 'operation', SerialCommandType.FINALIZE_WO)
  self.send_to_consumer(serial_event.dict())
  SerialEventManager.getInstance().handle_event(self, SerialCommandType.FINALIZE_WO, quantity=completed_batch_qt)'''

  SerialEventManager.getInstance().handle_event(self, SerialCommandType.FINALIZE_WO)

def udpate_batch_serial_data(self, form_data):
  if not self.job:
    self.job = self.get_job_data()

  step_data = []
  for field in form_data:
    if field.value!=None:
      field_data = SerialFormFieldValue()
      setattr(field_data, 'form_field_key', field.form_field_key)
      setattr(field_data, 'custom_field_key', field.custom_field_key)
      setattr(field_data, 'value', field.value)
      setattr(field_data, 'phase_key', self.info.phase_key)
      setattr(field_data, 'step_key', self.info.step_key)
      step_data.append(field_data)

  if len(step_data)>0:
    '''serial_event = SerialEvent()
    setattr(serial_event, 'created_by', self.info.user_key)
    setattr(serial_event, 'wo_key', self.info.work_order_key)
    setattr(serial_event, 'product_key', self.info.product_key)
    setattr(serial_event, 'quantity', self.job.active_batch_qt)
    setattr(serial_event, 'batch_key', self.info.active_batch_key)
    setattr(serial_event, 'operation', SerialCommandType.UPDATE_DATA_FROM_BATCH)
    setattr(serial_event, 'step_data', step_data)

    self.send_to_consumer(serial_event.dict())'''
    SerialEventManager.getInstance().handle_event(self, SerialCommandType.UPDATE_DATA_FROM_BATCH, step_data=step_data)

def send_link_batch_serial_event(self):
  '''serial_event = SerialEvent()
  setattr(serial_event, 'batch_serials', self.info.batch_serials)
  setattr(serial_event, 'batch_key', self.batch.key)
  setattr(serial_event, 'operation', SerialCommandType.LINK_BATCH)
  self.send_to_consumer(serial_event.dict())'''
  SerialEventManager.getInstance().handle_event(self, SerialCommandType.LINK_BATCH, batch_serials=self.info.batch_serials)
