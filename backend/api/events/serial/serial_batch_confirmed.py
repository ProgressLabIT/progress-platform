from events.serial.base_serial import BaseSerialEvent, BaseSerialModel
from models.event import EventModel
from models.event import EventType
from models.serial import Serial, SerialNotificationType, SerialNotificationErrorCode

from typing import Any
from utils.db import model_to_db_dict
from utils.dt import timestamp
from utils.counter import _generate_counter
from utils.serial import Queries

class SerialBatchConfirmedModel(BaseSerialModel):
  event_type: str = EventType.SERIAL_BATCH_CONFIRMED.name
  batch_execution_data: Any | None = None
  batch_key: str
  job: Any

class SerialBatchConfirmed(BaseSerialEvent):
  event_data: SerialBatchConfirmedModel

  def set_model(self, base_model: EventModel):
    self.info = SerialBatchConfirmedModel(**base_model.model_dump())

  def apply(self):
    cursor = self.tx.aql.execute(
       Queries.GET_BATCH_SERIALS,
       bind_vars=dict(batch_key=self.info.batch_key
    ))
    # JUST IN CASE: Consider only serials to be confirmed to avoid reassigning a new code
    batch_serials = [Serial(**s) for s in cursor if s['code'] is None]
    # Counter key is the same for all serials in the batch
    counter_key = None
    if (batch_serials):
       counter_key = batch_serials[0].counter_key
    else:
       return
    if (counter_key!=None):
       last_phase = self.info.job['last_phase']
       now = timestamp()
       for serial in batch_serials:
          serial.code = _generate_counter(self.tx, 'Counter/' + counter_key)
          serial.released = now if last_phase else None
          for step in self.info.batch_execution_data:
            for data in serial.data:
               if step.form_field_key == data.form_field_key:
                  data.value = step.value
                  data.batch_key = step.batch_key
                  data.phase_key = step.phase_key
                  data.step_key = step.step_key
          confirm_serial_match = dict(_from=f'Batch/{self.info.batch_key}', from_serial=serial.key)
          confirm_serial_update = dict(_from=serial.id)
          self.tx.collection('contains').update_match(confirm_serial_match, confirm_serial_update)
       clean_serial_match = dict(_from=f'Batch/{self.info.batch_key}')
       self.tx.collection('contains').delete_match(clean_serial_match)
       new = self.tx.collection('Serial').update_many([model_to_db_dict(s) for s in batch_serials], return_new=True)
       #self.tx.commit_transaction()
       for serial in batch_serials:
          self.notify_results(dict(
             serial_key = serial.key,
             serial = serial.code,
             notification = SerialNotificationType.FINALIZED
          ))
    else:
       # Come gestire la notifica di errore?
       self.notify_results(dict(
          notification = SerialNotificationType.ERROR,
          error_code = SerialNotificationErrorCode.COUNTER_NOT_DEFINED,
          error = 'Counter not defined'
       ))
       raise ValueError(f"Counter not defined for batch {self.batch_key}")



