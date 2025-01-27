from typing import Any, Set
from events.base_event import BaseEvent
from events.event_model import EventModel
from abc import ABC, abstractmethod
from managers.notification_manager import NotificationManager

from utils.serial import Queries
import copy
import json
from models.serial import Serial, SerialNotificationType

from utils.dt import timestamp

class BaseSerialModel(EventModel):
   # Traceability fields
   serial_key: Any | None = None
   serial_data: Any | None = None
   batch_serials: Set[str] | None = None # prevent duplicated entries from client


class BaseSerial(BaseEvent, ABC):
  event_data: BaseSerialModel

  def get_write_collections(self):
    return list(set(super().get_write_collections() + [
        'Batch',
        'batch_serial',
        'Event',
        'Job',
        'Queue',
        'Serial',
        'StepExecutionData',
        'wip',
        'WorkOrder',
        'WorkSession',
        'contains',
        'Config',
        'Counter'
      ]))

  @abstractmethod
  def apply(self):
    pass

  @abstractmethod
  def set_model(self, base_model: EventModel):
    pass

  def can_be_conflated(self, notification_type):
     return notification_type not in [SerialNotificationType.ERROR]

  def notify_results(self, notification):
    notification['subtopic'] = "serial-notification"
    serial_event = copy.deepcopy(self.event_data)
    if 'error' in notification:
      serial_event.event_type = "SERIAL_"+notification['notification']+" ("+notification['error']+")"
    else:
      serial_event.event_type = "SERIAL_"+notification['notification']
    serial_event.serial_key = notification.get('serial_key')
    self.tx.collection('Event').insert(serial_event)
    if self.can_be_conflated(notification.get('notification')):
       NotificationManager.getInstance().notifyConflated(subtopic="serial-notification", message=json.dumps(notification), delay=5)
    else:
       NotificationManager.getInstance().notify(key=notification.get('serial_key'), notification=json.dumps(notification))

  def verify_serial_code_free(self, serial_key, product_key, serial):
     cursor = self.tx.aql.execute(
        Queries.GET_SERIALS_FOR_SERIAL_CODE,
        bind_vars=dict(
          serial_key=serial_key,
          serial=serial,
          product_key=product_key
        )
      )
     try:
        return len([Serial(**t) for t in cursor])<=0
     except:
      return False
