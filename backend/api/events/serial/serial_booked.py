from events.serial.base_serial import BaseSerial, BaseSerialModel
from models.serial import Serial, SerialNotificationType, SerialNotificationErrorCode
import traceback
from models.event import EventModel
from typing import Any
from utils.db import model_to_db_dict
from utils.dt import timestamp
from utils.counter import _generate_counter
from utils.serial import Queries
from models.event import EventType
from utils.exceptions import (
  SerialNotLinkedError
)

class SerialBookedModel(BaseSerialModel):
  event_type: str = EventType.SERIAL_BOOKED.name
  batch_serials: Any
  batch_key: str
  job: Any

class SerialBooked(BaseSerial):
  event_data: SerialBookedModel

  def set_model(self, base_model: EventModel):
    self.info = SerialBookedModel(**base_model.model_dump())

  def apply(self):
    batch_key = self.info.batch_key
    batch_serials = self.info.batch_serials
    new_batch_serial_records = [dict(
       _from=f'Batch/{batch_key}',
       _to=f'Serial/{serial_key}'
    ) for serial_key in batch_serials]
    try:
       self.tx.collection('batch_serial').insert_many(new_batch_serial_records)
       for serial_key in batch_serials:
          self.notify_results(dict(
             serial_key = serial_key,
             notification = SerialNotificationType.UPDATED
          ))
    except:
       print(traceback.format_exc())
       self.notify_results(dict(
          notification = SerialNotificationType.ERROR,
          error_code = SerialNotificationErrorCode.EXCEPTION,
          error = traceback.format_exc()
       ))
       raise SerialNotLinkedError(f'Cannot link serials')



