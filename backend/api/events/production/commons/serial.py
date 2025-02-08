import json
import traceback

from fastapi import HTTPException

from utils.kafka.kafka_producer import KafkaProducer
from models.event import EventModel
from models.form import SerialFormFieldValue
from models.serial import Serial, SerialNotificationType, SerialNotificationErrorCode
from utils.process import Queries as ProcessQueries
from events.base_event import BaseEvent


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

def _retrieve_serial_phases_data(self):
  cursor = self.tx.aql.execute(ProcessQueries.GET_PRODUCTION_PROCESS,
     bind_vars=dict(
       product_key = self.info.product_key,
     )
   )
  return [e for e in cursor]

def _convert_form_field(self, field, work_order_key, batch_key, step_key, phase_key):
  field_value = field['value']

  try:
    for sub_key in field_value:
      if 'size' in sub_key:
        sub_key['bucket'] = 'traceability'
        sub_key['path'] = "/media/traceability/"+work_order_key+"/"+batch_key+"/"+step_key+"/"+field['custom_field_key']+"/"+field['form_field_key']+"/"+sub_key['name']
  except TypeError: # field_value not a dict (type 'files' or 'choice')
    pass

  field_data = SerialFormFieldValue(
    form_field_key = field['form_field_key'],
    custom_field_key = field['custom_field_key'],
    batch_key = batch_key,
    phase_key = phase_key,
    step_key = step_key,
    value = field_value
  )
  return field_data


def convert_batch_data(self, data):
  batch_data = []
  if data != None and 'step_data' in data:
    for step in data['step_data']:
      if 'form_data' in step:
        for field in step['form_data']:
          if field['value']!=None:
            batch_data.append(self._convert_form_field(field=field, work_order_key=data['work_order_key'], batch_key=data['_key'], step_key=step['_key'], phase_key=data['phase_key']))
  return batch_data


def convert_form_data(self, form_data):
  batch_data = []
  for field in form_data:
    if field.value!=None:
      batch_data.append(self._convert_form_field(field=field.model_dump(), work_order_key=self.info.work_order_key, batch_key=self.info.active_batch_key, step_key=self.info.step_key, phase_key=self.info.phase_key))
  return batch_data

