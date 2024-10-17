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

def convert_field(self, field, work_order_key, batch_key, step_key, phase_key):
  field_data = SerialFormFieldValue()
  setattr(field_data, 'form_field_key', field['form_field_key'])
  setattr(field_data, 'custom_field_key', field['custom_field_key'])
  field_value = field['value']
  try:
    for sub_key in field_value:
      if 'size' in sub_key:
        sub_key['bucket'] = 'traceability'
        sub_key['path'] = "/media/traceability/"+work_order_key+"/"+batch_key+"/"+step_key+"/"+field['custom_field_key']+"/"+field['form_field_key']+"/"+sub_key['name']
  except:
    field_value = field['value']
  setattr(field_data, 'value', field_value)
  setattr(field_data, 'batch_key', batch_key)
  setattr(field_data, 'phase_key', phase_key)
  setattr(field_data, 'step_key', step_key)
  return field_data

def convert_form_field(self, field, work_order_key, batch_key, step_key, phase_key):
  field_data = SerialFormFieldValue()
  setattr(field_data, 'form_field_key', field.form_field_key)
  setattr(field_data, 'custom_field_key', field.custom_field_key)
  field_value = field.value
  try:
    for sub_key in field_value:
      if 'size' in sub_key:
        sub_key['bucket'] = 'traceability'
        sub_key['path'] = "/media/traceability/"+work_order_key+"/"+batch_key+"/"+step_key+"/"+field.custom_field_key+"/"+field.form_field_key+"/"+sub_key['name']
  except:
    field_value = field.value
  setattr(field_data, 'value', field_value)
  setattr(field_data, 'batch_key', batch_key)
  setattr(field_data, 'phase_key', phase_key)
  setattr(field_data, 'step_key', step_key)
  return field_data


def convert_batch_data(self, batch_execution_data):
  batch_data = []
  if batch_execution_data != None and 'step_data' in batch_execution_data:
    for step in batch_execution_data['step_data']:
      if 'form_data' in step:
        for field in step['form_data']:
          if field['value']!=None:
            batch_data.append(convert_field(self, field=field, work_order_key=batch_execution_data['work_order_key'], batch_key=batch_execution_data['_key'], step_key=step['_key'], phase_key=batch_execution_data['phase_key']))
  return batch_data

def convert_form_data(self, form_data):
  batch_data = []
  for field in form_data:
    if field.value!=None:
            batch_data.append(convert_form_field(self, field=field, work_order_key=self.info.work_order_key, batch_key=self.info.active_batch_key, step_key=self.info.step_key, phase_key=self.info.phase_key))
  return batch_data


def store_form_data(self, completed_batch_qt = None, form_data = None):
  batch_execution_data = convert_form_data(self, form_data)
  if (len(batch_execution_data) > 0):
    SerialEventManager.getInstance().handle_event(self, SerialCommandType.STORE_BATCH_DATA, quantity=completed_batch_qt or self.info.active_batch_qt, batch_execution_data=batch_execution_data)

def store_batch_data(self, completed_batch_qt = None, batch_execution_data = None):
  batch_execution_data = convert_batch_data(self, batch_execution_data)
  if (len(batch_execution_data) > 0):
    SerialEventManager.getInstance().handle_event(self, SerialCommandType.STORE_BATCH_DATA, quantity=completed_batch_qt or self.info.active_batch_qt, batch_execution_data=batch_execution_data)

def finalize_batch_serial(self, completed_batch_qt = None, batch_execution_data = None):
  SerialEventManager.getInstance().handle_event(self, SerialCommandType.FINALIZE_BATCH, quantity=completed_batch_qt or self.info.active_batch_qt, batch_execution_data=convert_batch_data(self, batch_execution_data))

def finalize_wo_serial(self, batch_execution_data):
  SerialEventManager.getInstance().handle_event(self, SerialCommandType.FINALIZE_WO, batch_execution_data=convert_batch_data(self, batch_execution_data))

def send_link_batch_serial_event(self):
  SerialEventManager.getInstance().handle_event(self, SerialCommandType.LINK_BATCH, batch_serials=self.info.batch_serials)
