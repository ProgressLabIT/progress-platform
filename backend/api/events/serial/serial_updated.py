from events.serial.base_serial import BaseSerialEvent, BaseSerialModel
from models.serial import  SerialNotificationType, SerialNotificationErrorCode
import traceback
from models.event import EventType
from utils.exceptions import (
  SerialNotUpdatedError
)
from models.event import EventModel

class SerialUpdatedEvent(BaseSerialEvent):
  class InfoModel(BaseSerialModel):
    ...

  @classmethod
  def get_event_type(cls):
    return EventType.SERIAL_UPDATED

  def apply(self):
    try:
      serial = self.tx.collection('Serial').get(self.info.serial_data.get("_key"))
      if (self.info.serial_data.get('code') != None and serial.get('code') != self.info.serial_data.get('code')):
        ignore_code_protection = False

        try:
          # TODO: Remove need of `ignore_code_protection`, find a better way to handle this
          if (self.info.serial_data):
            ignore_code_protection = self.info.serial_data.get('ignore_code_protection');
        except:
          ignore_code_protection = False

        code_edit_config = self.tx.collection('Config').get('allow_serial_code_edit')
        can_edit_code = False

        if (code_edit_config != None):
          can_edit_code = code_edit_config['value']

        if not can_edit_code and not ignore_code_protection:
          self.notify_results(dict(
            serial = self.info.serial_data.get('code'),
            serial_key = self.info.serial_data.get("_key"),
            notification = SerialNotificationType.ERROR,
            error_code = SerialNotificationErrorCode.SERIAL_CODE_EDIT_NOT_ALLOWED,
            error = 'Serial code edit not allowed'
          ))
          return

        if (self.info.serial_data.get('code') != None and not self.verify_serial_code_free(serial_key=serial.get("_key"), product_key=serial.get("product_key"), serial=self.info.serial_data.get('code'))):
          self.notify_results(dict(
            serial = self.info.serial_data.get('code'),
            serial_key = self.info.serial_data.get("_key"),
            notification = SerialNotificationType.ERROR,
            error_code = SerialNotificationErrorCode.SERIAL_ALREADY_PRESENT,
            error = 'Serial already present'
            ))
          return

        serial['code'] = self.info.serial_data.get('code').upper()

      if (self.info.serial_data.get('data') != None):
          serial['data'] = self.info.serial_data.get('data')

      self.tx.update_document(serial)

    except:
      print(traceback.format_exc())
      self.notify_results(dict(
        serial_key = self.info.serial_data.get("_key"),
        notification = SerialNotificationType.ERROR,
        error_code = SerialNotificationErrorCode.EXCEPTION,
        error = traceback.format_exc()
      ))
      raise SerialNotUpdatedError(f'Cannot update serial {self.info.serial_data.get("_key")}')

    self.notify_results(dict(
      serial_key = self.info.serial_data.get("_key"),
      serial = self.info.serial_data.get("code"),
      notification = SerialNotificationType.UPDATED
    ))

    self.response = dict(
      message="Serial updated correctly",
      serial_key=self.info.serial_data.get("_key")
    )
