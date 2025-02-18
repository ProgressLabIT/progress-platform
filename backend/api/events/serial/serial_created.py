import traceback
from datetime import datetime

from events.serial.base_serial import BaseSerialEvent, BaseSerialModel
from models.event import EventType
from models.form import FormFieldValue
from models.serial import Serial, SerialNotificationErrorCode, SerialNotificationType
from utils.counter import _generate_counter
from utils.exceptions import SerialCodeAlreadyPresent, SerialNotCreatedError


class SerialCreatedEvent(BaseSerialEvent):

  class InfoModel(BaseSerialModel):
    batch_key: str | None = None
    data: list[FormFieldValue] | None = None
    wo_key: str | None = None
    product_key: str | None = None
    counter_key: str | None = None
    released: datetime | None = None

  @classmethod
  def get_event_type(cls) -> EventType:
    return EventType.SERIAL_CREATED

  def apply(self):
    #tx = self.tx.begin_transaction(write=['Serial', 'Counter', 'batch_serial'], read=[])
    if self.info.code != None and not self.verify_serial_code_free(None, self.info.product_key, self.info.code):
      self.notify_results(dict(
        serial = self.info.code,
        notification = SerialNotificationType.ERROR,
        error_code = SerialNotificationErrorCode.SERIAL_ALREADY_PRESENT,
        error = 'Serial already present'
      ))
      raise SerialCodeAlreadyPresent('Cannot create serial, serial code already used')

    if self.info.released and self.info.counter_key is None and self.info.code is None:
      raise ValueError('Cannot release serial without code or counter')

    try:
      if self.info.counter_key and self.info.code is None:
        # Generate serial code from counter
        self.info.code = _generate_counter(self.tx, self.info.counter_key)

      if self.info.released and self.info.code is None:
        raise ValueError('Cannot release serial without code')

      new_serial = Serial(**self.info.model_dump())
      serial_key = self.tx.collection('Serial').insert(new_serial.model_dump(), return_new=True)['_key']

      if self.info.batch_key:
        self.tx.collection('batch_serial').insert(dict(
          _from=f'Batch/{self.info.batch_key}',
          _to=f'Serial/{serial_key}'
        ))

      self.notify_results(dict(
        serial_key = serial_key,
        serial = self.info.code,
        notification = SerialNotificationType.CREATED
      ))

      self.response = dict(
        message="Serial created correctly",
        serial_key=serial_key
      )

    except:
      print(traceback.format_exc())
      self.notify_results(dict(
        serial_key = serial_key or None,
        notification = SerialNotificationType.ERROR,
        error_code = SerialNotificationErrorCode.EXCEPTION,
        error = traceback.format_exc()
      ))
      raise SerialNotCreatedError('Cannot create serial')
