from events.serial.base_serial import BaseSerial, BaseSerialModel
from models.serial import SerialLink
import traceback
from models.serial import SerialNotificationType, SerialNotificationErrorCode
from events.event_type import EventType
from utils.exceptions import (
  SerialNotLinkedError,
)
from events.event_model import EventModel
class SerialLinkedModel(BaseSerialModel):
  event_type: str = EventType.SERIAL_LINKED.name
  serial_link_data: list[SerialLink] | None = None

class SerialLinked(BaseSerial):
  event_data: SerialLinkedModel

  def set_model(self, base_model: EventModel):
    self.event_data = SerialLinkedModel(**base_model.model_dump())

  def apply(self):
    serial_link_data = self.event_data.serial_link_data
    booked_serial = []
    for serial_links in serial_link_data:
       if serial_links.to_serial in booked_serial:
          raise SerialNotLinkedError(f'Cannot link serials: multiple usage of the same component')
       booked_serial.append(serial_links.to_serial)

    for serial_links in serial_link_data:
      from_serial = serial_links.from_serial
      to_serial = serial_links.to_serial
      reason = serial_links.reason
      wo_key = serial_links.wo_key
      component_key = serial_links.component_key
      batch_key = serial_links.batch_key
      batch_link_match = dict(_from=f'Batch/{batch_key}', _to=f'Serial/{to_serial}')
      serial_link_match = dict(_from=f'Serial/{from_serial}', _to=f'Serial/{to_serial}')
      try:
         batch_link_cursor = self.tx.collection('contains').find(batch_link_match)
         serial_link_cursor = self.tx.collection('contains').find(serial_link_match)
         if batch_link_cursor.count()>0:
            self.tx.collection('contains').update(dict(
               _key = batch_link_cursor.next()['_key'],
               _from=f'Batch/{batch_key}',
               _to=f'Serial/{to_serial}',
               replaced=serial_links.replaced,
               wo_key = wo_key,
               component_key=component_key,
               from_serial=from_serial,
               batch_key=batch_key,
               reason=reason
            ))
         elif serial_link_cursor.count()>0:
            self.tx.collection('contains').update(dict(
               _key = serial_link_cursor.next()['_key'],
               _from=f'Serial/{from_serial}',
               _to=f'Serial/{to_serial}',
               replaced=serial_links.replaced,
               wo_key = wo_key,
               component_key=component_key,
               from_serial=from_serial,
               batch_key=batch_key,
               reason=reason
            ))
         elif serial_links.link_serial_directly:
            self.tx.collection('contains').insert(dict(
               _from=f'Serial/{from_serial}',
               _to=f'Serial/{to_serial}',
               replaced=False,
               wo_key = wo_key,
               component_key=component_key,
               from_serial=from_serial,
               batch_key=batch_key,
               reason=''
            ))
         else:
            self.tx.collection('contains').insert(dict(
               _from=f'Batch/{batch_key}',
               _to=f'Serial/{to_serial}',
               replaced=False,
               wo_key = wo_key,
               component_key=component_key,
               from_serial=from_serial,
               batch_key=batch_key,
               reason=''
            ))
      except:
         print(traceback.format_exc())
         self.notify_results(dict(
            notification = SerialNotificationType.ERROR,
            error_code = SerialNotificationErrorCode.EXCEPTION,
            error = traceback.format_exc()
         ))
         raise SerialNotLinkedError(f'Cannot link serials')
    self.notify_results(dict(
        notification = SerialNotificationType.UPDATED
    ))
    self.set_response(dict(
           message="Serial linked correctly"
    ))

