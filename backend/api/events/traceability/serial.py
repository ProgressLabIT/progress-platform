import json
import traceback

from fastapi import HTTPException

from utils.kafka.kafka_producer import KafkaProducer
from models.serial import Serial, SerialEvent, SerialCommandType
from models.form import SerialFormFieldValue
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
  SerialEventManager.getInstance().handle_event(self, SerialCommandType.CREATE_AND_FINALIZE)

def link_serial(self):
  SerialEventManager.getInstance().handle_event(self, SerialCommandType.LINK_SERIALS)


def update_serial(self):
  SerialEventManager.getInstance().handle_event(self, SerialCommandType.UPDATE)


def delete_serial(self):
  SerialEventManager.getInstance().handle_event(self, SerialCommandType.DELETE)

def create_batch_serial_records(self, quantity):
  if not self.job:
    self.job = self.get_job_data()

  SerialEventManager.getInstance().handle_event(self, SerialCommandType.CREATE_FROM_BATCH, quantity=quantity)

def convert_batch_data(self, batch_execution_data):
  batch_data = []
  if batch_execution_data != None and 'step_data' in batch_execution_data:
    for step in batch_execution_data['step_data']:
      if 'form_data' in step:
        for field in step['form_data']:
          if field['value']!=None:
            field_data = SerialFormFieldValue()
            setattr(field_data, 'form_field_key', field['form_field_key'])
            setattr(field_data, 'custom_field_key', field['custom_field_key'])
            setattr(field_data, 'value', field['value'])
            setattr(field_data, 'phase_key', self.info.phase_key)
            setattr(field_data, 'step_key', self.info.step_key)
            batch_data.append(field_data)
  return batch_data

def store_batch_data(self, completed_batch_qt = None, batch_execution_data = None):
  SerialEventManager.getInstance().handle_event(self, SerialCommandType.STORE_BATCH_DATA, quantity=completed_batch_qt or self.info.active_batch_qt, batch_execution_data=convert_batch_data(self, batch_execution_data))

def finalize_batch_serial(self, completed_batch_qt = None, batch_execution_data = None):
  SerialEventManager.getInstance().handle_event(self, SerialCommandType.FINALIZE_BATCH, quantity=completed_batch_qt or self.info.active_batch_qt, batch_execution_data=convert_batch_data(self, batch_execution_data))

def finalize_wo_serial(self, batch_execution_data):
  SerialEventManager.getInstance().handle_event(self, SerialCommandType.FINALIZE_WO, batch_execution_data=convert_batch_data(self, batch_execution_data))

def send_link_batch_serial_event(self):
  SerialEventManager.getInstance().handle_event(self, SerialCommandType.LINK_BATCH, batch_serials=self.info.batch_serials)
