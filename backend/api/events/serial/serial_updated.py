from datetime import datetime

from pydantic import Field

from events.serial.base_serial import BaseSerialEvent, BaseSerialModel
from models.event import EventModel, EventType
from models.form import SerialFormFieldValue
from models.serial import  SerialNotificationType, SerialNotificationErrorCode
from utils.serial import Queries as SerialQueries
from utils.exceptions import (SerialNotUpdatedError)

class SerialUpdatedEvent(BaseSerialEvent):
  class InfoModel(BaseSerialModel):
    serial_key: str
    serial_code: str | None = None # Set code if provided
    serial_data: list[SerialFormFieldValue] | None = None # Set data if provided
    remove_data_from_phases: list[str] | None = None # Set phase keys to remove data from if provided

  @classmethod
  def get_event_type(cls):
    return EventType.SERIAL_UPDATED


  def _merge_serial_data(self):
    # Merge data from the original serial with the new data
    merged_data = []
    for existing_field in self.original['data']:
      new_field = existing_field
      for field in self.info.serial_data:
        if field.form_field_key == existing_field['form_field_key']:
          new_field['value'] = field.value
          break
      merged_data.append(new_field)
    return merged_data


  def apply(self):
    self.original = self.tx.collection('Serial').get(self.info.serial_key)

    if self.original is None:
      raise SerialNotUpdatedError(f'Serial with key {self.info.serial_key} not found')


    # Init serial update dict
    serial_update = dict(_key=self.info.serial_key)

    # ===================================================================
    # UPDATE SCENARIOS
    # ===================================================================

    # Update code if provided
    if self.info.serial_code:
      # Prevent code change if it's protected. Not applicable if serial hasn't been assigned a code yet
      if (
        self.original['code'] is not None and
        self.original['code'] != self.info.serial_code and
        not self.tx.collection('Config').get('allow_serial_code_edit').get('value', True)
      ):
        raise SerialNotUpdatedError(f'Changing serial code is not allowed')

      serial_update['code'] = self.info.serial_code

    # Update data if provided
    if self.info.serial_data:
      serial_update['data'] = self._merge_serial_data()


    # ===================================================================
    # UPDATE SERIAL
    # ===================================================================

    self.response = dict(
      message="No changes to be made to serial",
      serial_key=self.info.serial_key
    )

    # Remove data from phases if provided
    if self.info.remove_data_from_phases:
      self.tx.aql.execute(
        SerialQueries.REMOVE_PHASE_DATA_FROM_SERIAL,
        bind_vars = dict(
          serial_key = self.info.serial_key,
          phase_keys = self.info.remove_data_from_phases
        )
      )
      self.response = dict(
        message="Serial updated correctly",
        serial_key=self.info.serial_key
      )

    if len(serial_update.keys()) > 1: # Only update if there are other changes to be made
      self.tx.collection('Serial').update(serial_update)
      self.response = dict(
        message="Serial updated correctly",
        serial_key=self.info.serial_key
      )

    self.notify_results(dict(
      serial_key = self.info.serial_key,
      notification = SerialNotificationType.UPDATED
    ))


