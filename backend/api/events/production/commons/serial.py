import json
import traceback
from datetime import datetime

from events.serial.serial_created import SerialCreatedEvent
from fastapi import HTTPException
from models.form import SerialFormFieldValue
from models.serial import SerialNotificationErrorCode, SerialNotificationType
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

  def _get_production_process(self, product_key):
    cursor = self.tx.aql.execute(ProcessQueries.GET_PRODUCTION_PROCESS,
      bind_vars=dict(
        product_key = product_key,
      )
    )
    return [e for e in cursor]

  def _convert_form_field(self, field, work_order_key, batch_key, step_key, phase_key):
    field_value = field['value']

    try:
      for sub_key in field_value:
        if 'size' in sub_key:
          sub_key['bucket'] = 'traceability'
          # TODO: OBJECT STORAGE MIGRATION - Replace file path with object storage URL
          # Generate signed URL or public URL for the object in object storage
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
        batch_data.append(self._convert_form_field(
          field=field.model_dump(),
          work_order_key=self.info.work_order_key,
          batch_key=self.info.active_batch_key,
          step_key=self.info.step_key,
          phase_key=self.info.phase_key
        ))
    return batch_data


  def _get_serial_fields_from_wo(self):
    work_order = self.tx.collection('WorkOrder').get(self.info.work_order_key)
    try:
      return work_order['serial_fields']
    except KeyError:
      raise ValueError("Serial fields not found in work order")


  def _create_serial_records(
    self,
    quantity: float,
    product_key: str,
    batch_key: str | None = None,
    wo_key: str | None = None,
    serial_codes: list[str] | None = [],
    counter_key: str | None = None,
    released: datetime | None = None
    ):
    # Get product counter key
    if serial_codes and len(serial_codes) != quantity:
      raise ValueError("Serial codes must be provided for each serial, if provided")

    # Create the serial records
    new_serials = []
    for i in range(int(quantity)):
      new_serial_key = SerialCreatedEvent.create_as_child(self, dict(
        data = self._get_serial_fields_from_wo(),
        code = serial_codes[i] if serial_codes else None,
        batch_key = batch_key,
        wo_key = wo_key,
        product_key = product_key,
        counter_key = counter_key,
        released = released
      ))['serial_key']
      new_serials.append(new_serial_key)

    # Link to batch if provided
    if batch_key:
      self._create_batch_serial_records(batch_key=batch_key, serial_keys=new_serials)

    return new_serials


  def _create_batch_serial_records(self, batch_key, serial_keys):
    records = []
    for serial_key in serial_keys:
      records.append(dict(
        _from=f'Batch/{batch_key}',
        _to=f'Serial/{serial_key}'
      ))

    self.tx.collection('batch_serial').insert_many(records)

