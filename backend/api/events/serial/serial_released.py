from events.serial.base_serial import BaseSerialEvent, BaseSerialModel
from typing import Any
from utils.db import db, model_to_db_dict
from utils.dt import timestamp
from models.event import EventType

from models.serial import  SerialNotificationType, Serial
import traceback
from utils.serial import Queries


class SerialReleasedEvent(BaseSerialEvent):
  class InfoModel(BaseSerialModel):
    pass

  @classmethod
  def get_event_type(cls):
    return EventType.SERIAL_RELEASED

  def apply(self):
    # Update released date
    self.tx.collection('Serial').update(dict(
      _key=self.info.serial_key,
      released=timestamp()
    ))
