import json
import traceback

from events.serial.serial_created import SerialCreatedEvent
from fastapi import HTTPException
from models.form import SerialFormFieldValue
from models.serial import Serial, SerialNotificationErrorCode, SerialNotificationType
from utils.kafka.kafka_producer import KafkaProducer
from utils.process import Queries as ProcessQueries

# ===================================================================
# Serial
# ===================================================================

class BaseSerialEvent:
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
