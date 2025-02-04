import json
import traceback

from fastapi import HTTPException

from utils.kafka.kafka_producer import KafkaProducer
from models.event import EventModel
from models.form import SerialFormFieldValue
from models.serial import Serial, SerialNotificationType, SerialNotificationErrorCode
from utils.process import Queries as ProcessQueries
from events.base_event import BaseEvent
from events.serial.serial_created import SerialCreatedModel


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

def _create_batch_serial_records(self, quantity):
  if not self.job:
    self.job = self.get_job_data()

  batch_key = self.batch.key
  created_by = self.event_data.user_key
  wo_key = self.event_data.work_order_key
  product_key = self.event_data.product_key
  product = self.tx.collection('Product').get(product_key)
  serial_data = Serial()
  counter_key = None
  if 'counter_key' in product:
     setattr(serial_data, 'counter_key', product['counter_key'])
     counter_key = product['counter_key']
  else:
     setattr(serial_data, 'counter_key', None)
  setattr(serial_data, 'product_key', product_key)
  if self.job.serialcode_on_batchstart and not counter_key:
     self.notify_results(dict(
        notification = SerialNotificationType.ERROR,
        error_code = SerialNotificationErrorCode.COUNTER_NOT_DEFINED,
        error = 'Counter not defined'
     ))
     raise ValueError(f"Counter not defined for batch {self.event.active_batch_key}")
  phases_data = self._retrieve_serial_phases_data()
  data = []
  for phase in phases_data:
    for step in phase['steps']:
      if 'form_fields' in step:
        for field in step['form_fields']:
          field_data = SerialFormFieldValue()
          setattr(field_data, 'form_field_key', field['_key'])
          setattr(field_data, 'custom_field_key', field['custom_field_key'])
          setattr(field_data, 'phase_key', phase['_key'])
          setattr(field_data, 'step_key', step['_key'])
          data.append(field_data)
  setattr(serial_data, 'data', data)
  setattr(serial_data, 'created_by', 'User/'+created_by)
  setattr(serial_data, 'user_key', created_by)
  setattr(serial_data, 'wo_key', wo_key)
  for i in range(int(quantity)):
     #self.create_serial(serial_data=serial_data.model_dump(), batch_key=batch_key, counter=self.event.job.serialcode_on_batchstart, finalize=False)
     EventManager.trigger_event(self, SerialCreatedModel(
       batch_key = batch_key,
       counter = self.job.serialcode_on_batchstart,
       finalize = False,
       serial_data = serial_data.model_dump(),
       user_key = self.event_data.user_key
     ))

def _retrieve_serial_phases_data(self):
  cursor = self.tx.aql.execute(ProcessQueries.GET_PRODUCTION_PROCESS,
     bind_vars=dict(
       product_key = self.event_data.product_key,
     )
   )
  return [e for e in cursor]

def _convert_field(self, field, work_order_key, batch_key, step_key, phase_key):
  field_data = SerialFormFieldValue()
  setattr(field_data, 'form_field_key', field['form_field_key'])
  setattr(field_data, 'custom_field_key', field['custom_field_key'])
  field_value = field['value']
  try:
    for sub_key in field_value:
      if 'size' in sub_key:
        sub_key['bucket'] = 'traceability'
        sub_key['path'] = "/media/traceability/"+work_order_key+"/"+batch_key+"/"+step_key+"/"+field['custom_field_key']+"/"+field['form_field_key']+"/"+sub_key['name']
  except TypeError: # field_value not a dict (type 'files' or 'choice')
    pass
  setattr(field_data, 'value', field_value)
  setattr(field_data, 'batch_key', batch_key)
  setattr(field_data, 'phase_key', phase_key)
  setattr(field_data, 'step_key', step_key)
  return field_data

def _convert_form_field(self, field, work_order_key, batch_key, step_key, phase_key):
  field_data = SerialFormFieldValue()
  setattr(field_data, 'form_field_key', field.form_field_key)
  setattr(field_data, 'custom_field_key', field.custom_field_key)
  field_value = field.value
  try:
    for sub_key in field_value:
      if 'size' in sub_key:
        sub_key['bucket'] = 'traceability'
        sub_key['path'] = "/media/traceability/"+work_order_key+"/"+batch_key+"/"+step_key+"/"+field.custom_field_key+"/"+field.form_field_key+"/"+sub_key['name']
  except TypeError: # field_value not a dict (type 'files' or 'choice')
    pass
  setattr(field_data, 'value', field_value)
  setattr(field_data, 'batch_key', batch_key)
  setattr(field_data, 'phase_key', phase_key)
  setattr(field_data, 'step_key', step_key)
  return field_data


def convert_batch_data(self, data):
  batch_data = []
  if data != None and 'step_data' in data:
    for step in data['step_data']:
      if 'form_data' in step:
        for field in step['form_data']:
          if field['value']!=None:
            batch_data.append(self._convert_field( field=field, work_order_key=data['work_order_key'], batch_key=data['_key'], step_key=step['_key'], phase_key=data['phase_key']))
  return batch_data

def convert_form_data(self, form_data):
  batch_data = []
  for field in form_data:
    if field.value!=None:
            batch_data.append(self._convert_form_field(field=field, work_order_key=self.event_data.work_order_key, batch_key=self.event_data.active_batch_key, step_key=self.event_data.step_key, phase_key=self.event_data.phase_key))
  return batch_data

