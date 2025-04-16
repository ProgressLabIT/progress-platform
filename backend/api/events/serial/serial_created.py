import traceback
from datetime import datetime
from pydantic import Field

from events.serial.base_serial import BaseSerialEvent, BaseSerialModel
from models.event import EventType
from models.form import SerialFormFieldValue
from models.serial import Serial, SerialNotificationErrorCode, SerialNotificationType
from utils.counter import _generate_counter
from utils.dt import timestamp
from utils.exceptions import SerialCodeAlreadyPresent, SerialNotCreatedError


class SerialCreatedEvent(BaseSerialEvent):

  class InfoModel(BaseSerialModel):
    data: list[SerialFormFieldValue] | None = None
    code: str | None = None
    wo_key: str | None = None
    product_key: str | None = None
    counter_key: str | None = Field(None, exclude=True)
    released: datetime | None = Field(default_factory=timestamp)


  @classmethod
  def get_event_type(cls) -> EventType:
    return EventType.SERIAL_CREATED

  def apply(self):
    # Ensure serial code is available if provided
    if self.info.code != None and not self.verify_serial_code_free(None, self.info.product_key, self.info.code):
      self.notify_results(dict(
        serial = self.info.code,
        notification = SerialNotificationType.ERROR,
        error_code = SerialNotificationErrorCode.SERIAL_ALREADY_PRESENT,
        error = 'Serial already present'
      ))
      raise SerialCodeAlreadyPresent('Cannot create serial, serial code already used')

    # Handle code if serial is released or must be generated at creation
    product = self.tx.collection('Product').get(self.info.product_key)

    if not product.get('traceability_level', False):
      raise ValueError(f"Cannot create serial for product {product['code']}. Traceability is not enabled.")

    needs_code = self.info.released or product.get('serial_code_on_creation', False)

    if needs_code:
      if self.info.code is None:
        self.info.counter_key = product.get('counter_key', None)
        if self.info.counter_key is None:
          raise ValueError('Cannot create/release serial. No code or counter provided.')

        self.info.code = _generate_counter(self.tx, self.info.counter_key)

    try:
      new_serial = Serial(**self.info.model_dump())
      serial_key = self.tx.collection('Serial').insert(new_serial.model_dump(by_alias=True))['_key']

      self.notify_results(dict(
        serial_key = serial_key,
        serial = self.info.code,
        notification = SerialNotificationType.CREATED
      ))

      self.response = dict(
        message="Serial created correctly",
        serial_key=serial_key
      )

    except Exception as e:
      print(traceback.format_exc())
      self.notify_results(dict(
        notification = SerialNotificationType.ERROR,
        error_code = SerialNotificationErrorCode.EXCEPTION,
        error = traceback.format_exc()
      ))
      raise SerialNotCreatedError('Cannot create serial') from e
