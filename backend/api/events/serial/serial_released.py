from events.serial.base_serial import BaseSerial, BaseSerialModel
from typing import Any
from utils.db import db, model_to_db_dict
from utils.dt import timestamp
from events.event_type import EventType

from models.serial import  SerialNotificationType, Serial
import traceback
from utils.serial import Queries
from utils.exceptions import (
  SerialNotUpdatedError
)
from events.event_model import EventModel
class SerialReleasedModel(BaseSerialModel):
  event_type: str = EventType.SERIAL_RELEASED.name
  batch_execution_data: Any | None = None
  batch_key: str


class SerialReleased(BaseSerial):
  event_data: SerialReleasedModel

  def set_model(self, base_model: EventModel):
    self.event_data = SerialReleasedModel(**base_model.model_dump())

  def apply(self):
    cursor = self.tx.aql.execute(
       Queries.GET_BATCH_SERIALS,
       bind_vars=dict(batch_key=self.event_data.batch_key
    ))
    # JUST IN CASE: Consider only serials to be released to avoid reassigning a new release date
    batch_serials = [Serial(**s) for s in cursor if s['released'] is None]
    now = timestamp()
    for serial in batch_serials:
       serial.released = now
       for step in self.event_data.batch_execution_data:
            for data in serial.data:
               if step['form_field_key'] == data.form_field_key:
                  data.value = step['value']
                  data.batch_key = step['batch_key']
                  data.phase_key = step['phase_key']
                  data.step_key = step['step_key']
       confirm_serial_match = dict(_from=f'Batch/{self.event_data.batch_key}', from_serial=serial.key)
       confirm_serial_update = dict(_from=serial.id)
       self.tx.collection('contains').update_match(confirm_serial_match, confirm_serial_update)
    clean_serial_match = dict(_from=f'Batch/{self.event_data.batch_key}')
    self.tx.collection('contains').delete_match(clean_serial_match)
    self.tx.collection('Serial').update_many([model_to_db_dict(s) for s in batch_serials])
    for serial in batch_serials:
       self.notify_results(dict(
          serial_key = serial.key,
          serial = serial.code,
          notification = SerialNotificationType.FINALIZED
       ))

