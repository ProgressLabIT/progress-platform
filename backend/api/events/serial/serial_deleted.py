from events.serial.base_serial import BaseSerialEvent, BaseSerialModel
from models.serial import SerialNotificationType, SerialNotificationErrorCode
from utils.serial import Queries
import traceback
from models.event import EventInfoModel, EventType

from utils.exceptions import (
  SerialNotDeletedError
)


class SerialDeleted(BaseSerialEvent):
  class InfoModel(BaseSerialModel):
    soft: bool = True
    delete_children: bool | None = False

  @classmethod
  def get_event_type(cls):
    return EventType.SERIAL_DELETED

  def apply(self):
    delete_children = False
    try:
      if (self.info.delete_children):
         delete_children = self.info.delete_children
    except:
       delete_children = False
    serial_key = self.info.serial_key
    allow_serial_delete = self.tx.collection('Config').get('allow_serial_delete')
    if (allow_serial_delete == None or allow_serial_delete['value'] == False):
       self.notify_results(dict(
          serial_key = serial_key,
          notification = SerialNotificationType.ERROR,
          error_code = SerialNotificationErrorCode.EXCEPTION,
          error = 'Cannot delete serial because it is not allowed by configuration'
       ))
       raise SerialNotDeletedError(f'Serial {serial_key} cannot be deleted because it is not allowed by configuration')
    try:
       if delete_children:
          children = [i for i in self.tx.aql.execute(Queries.GET_SERIAL_CHILDREN, bind_vars=dict(
             serial_id = f'Serial/{serial_key}',
             level = 15))]
          for child in children:
             self.do_delete(serial_key=child.get("serial_key"))
       self.do_delete(serial_key=serial_key)
       self.notify_results(dict(
          serial_key = serial_key,
          notification = SerialNotificationType.DELETED
       ))
       self.response = dict(
           message="Serial deleted correctly",
           serial_key=serial_key
         )
    except:
       print(traceback.format_exc())
       self.notify_results(dict(
          serial_key = serial_key,
          notification = SerialNotificationType.ERROR,
          error_code = SerialNotificationErrorCode.EXCEPTION,
          error = traceback.format_exc()
       ))
       raise SerialNotDeletedError(f'Serial {serial_key} got exception while deleting')

  def do_delete(self, serial_key):
    if self.info.soft:
       self.tx.collection('Serial').update(dict(_key=serial_key, deleted=True))
    else:
       self.tx.collection('Serial').delete(serial_key)
    self.tx.collection('contains').delete_match(filters=dict(_from=f'Serial/{serial_key}'))
