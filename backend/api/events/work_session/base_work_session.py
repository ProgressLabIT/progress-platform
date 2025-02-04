from typing import Any, Set
from events.base_event import BaseEvent
from models.event import EventInfoModel
from abc import ABC, abstractmethod
from managers.notification_manager import NotificationManager

from utils.serial import Queries
import copy
import json
from models.serial import Serial, SerialNotificationType
from models.production import Job


from utils.dt import timestamp

class WorkSessionEventModel(EventInfoModel):
   # Work Session Fields
   job_key: str | None = None
   work_order_key: str | None = None
   phase_key: str | None = None
   batch_key: str | None = None
   product_key: str | None = None



class BaseWorkSession(BaseEvent, ABC):

  from events.production.commons.job import (
    _get_job_data,
  )

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

