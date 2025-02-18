import copy
import json
import traceback
from abc import ABC, abstractmethod
from typing import Any, Set

from fastapi import HTTPException

from events.base_event import BaseEvent
from managers.notification_manager import NotificationManager
from models.event import EventInfoModel
from models.serial import Serial, SerialNotificationType
from utils.dt import timestamp
from utils.kafka.kafka_producer import KafkaProducer
from utils.process import Queries as ProcessQueries
from utils.serial import Queries


class BaseSerialModel(EventInfoModel):
   # Traceability fields
   serial_key: Any | None = None
   serial_data: Any | None = None
   batch_serials: Set[str] | None = None # prevent duplicated entries from client


class BaseSerialEvent(BaseEvent, ABC):

  @classmethod
  def get_tx_collections(cls):
    return [
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
    ]


  def can_be_conflated(self, notification_type):
     return notification_type not in [SerialNotificationType.ERROR]

  def notify_results(self, notification):
    notification['subtopic'] = "serial-notification"
    serial_event = copy.deepcopy(self.info)
    if 'error' in notification:
      serial_event.event_type = "SERIAL_"+notification['notification']+" ("+notification['error']+")"
    else:
      serial_event.event_type = "SERIAL_"+notification['notification']
    serial_event.serial_key = notification.get('serial_key')
    #self.tx.collection('Event').insert(serial_event)
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


