from models.serial import Serial
from events.serial.base_serial import BaseSerial, BaseSerialModel
from models.event import EventType
from models.event import EventModel
from models.serial import Serial, SerialNotificationType, SerialNotificationErrorCode
from utils.counter import _generate_counter
import traceback


from utils.dt import timestamp

from utils.exceptions import (
  SerialNotCreatedError,
  SerialCodeAlreadyPresent
)

class SerialCreatedModel(BaseSerialModel):
   event_type: str = EventType.SERIAL_CREATED.name
   batch_key: str | None = None
   counter: bool = True
   finalize: bool = True

class SerialCreated(BaseSerial):
  event_data: SerialCreatedModel

  def __init__(self, **data):
    super().__init__(**data)
    self.serial_key = None

  def set_model(self, base_model: EventModel):
    self.event_data = SerialCreatedModel(**base_model.model_dump())

  def apply(self):
      new_serial_record = Serial(
         **self.event_data.serial_data
      ).dict(by_alias=True)

      #tx = self.tx.begin_transaction(write=['Serial', 'Counter', 'batch_serial'], read=[])
      if new_serial_record['code'] != None and not self.verify_serial_code_free(None, new_serial_record['product_key'], new_serial_record['code']):
         self.notify_results(dict(
            serial = new_serial_record['code'],
            notification = SerialNotificationType.ERROR,
            error_code = SerialNotificationErrorCode.SERIAL_ALREADY_PRESENT,
            error = 'Serial already present'
         ))
         raise SerialCodeAlreadyPresent(f'Cannot create serial, serial code already used')
      try:
         serial_no = "MISSING-COUNTER"
         if self.event_data.counter and new_serial_record['code'] == None:
            if ('counter_key' in self.event_data.serial_data):
               serial_no = _generate_counter(self.tx, 'Counter/' + self.event_data.serial_data['counter_key'])
               new_serial_record['code'] = serial_no
            else:
               self.notify_results(dict(
                  notification = SerialNotificationType.ERROR,
                  error_code = SerialNotificationErrorCode.COUNTER_NOT_DEFINED,
                  error = 'Counter not defined'
                ))

         if self.event_data.finalize:
            new_serial_record['released'] = timestamp()
         serial_key = self.tx.collection('Serial').insert(new_serial_record, return_new=True)['_key']

         self.serial_key = serial_key

         if self.event_data.batch_key:
            self.tx.collection('batch_serial').insert(dict(
               _from=f'Batch/{self.event_data.batch_key}',
               _to=f'Serial/{serial_key}'))

         #tx.commit_transaction()
         self.notify_results(dict(
            serial_key = self.serial_key,
            serial = serial_no,
            notification = SerialNotificationType.CREATED
         ))

         self.set_response(dict(
           message="Serial created correctly",
           serial_key=serial_key
         ))
      except:
         print(traceback.format_exc())
         self.notify_results(dict(
            serial_key = self.serial_key,
            notification = SerialNotificationType.ERROR,
            error_code = SerialNotificationErrorCode.EXCEPTION,
            error = traceback.format_exc()
         ))
         raise SerialNotCreatedError(f'Cannot create serial')
