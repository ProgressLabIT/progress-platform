from datetime import datetime

from pydantic import Field

from events.serial.base_serial import BaseSerialEvent, BaseSerialModel
from models.event import EventType
from utils.dt import timestamp


class SerialReleasedEvent(BaseSerialEvent):
  class InfoModel(BaseSerialModel):
    released: datetime | None = None

    @field_validator('released', mode='after')
    def validate_released(self, v):
      # Use timestamp if released is explicitly set to None
      if v is None:
        return timestamp()
      return v

  @classmethod
  def get_event_type(cls):
    return EventType.SERIAL_RELEASED

  def apply(self):
    # Update released date
    self.tx.collection('Serial').update(dict(
      _key=self.info.serial_key,
      released=self.info.released
    ))

    self.response = dict(
      message="Serial released correctly",
      serial_key=self.info.serial_key
    )
