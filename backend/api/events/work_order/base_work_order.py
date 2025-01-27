from typing import Any, Set
from events.base_event import BaseEvent
from events.event_model import EventModel
from abc import ABC, abstractmethod
from managers.notification_manager import NotificationManager
from models.production import WorkOrderFull

from utils.serial import Queries
import copy
import json
from models.serial import Serial, SerialNotificationType

from utils.dt import timestamp

class BaseWorkOrderModel(EventModel):
   # Work Order Fields
   work_order_key: str | None = None



class BaseWorkOrder(BaseEvent, ABC):
  event_data: BaseWorkOrderModel

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

  def _get_work_order_data(self):
    wo_data = self.tx.collection('WorkOrder').get(self.event_data.work_order_key)
    wo_data_out = WorkOrderFull(**wo_data)
    return wo_data_out

