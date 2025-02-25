from datetime import datetime

from pydantic import Field

from events.serial.base_serial import BaseSerialEvent, BaseSerialModel
from models.form import SerialFormFieldValue
from models.serial import  SerialNotificationType, SerialNotificationErrorCode
import traceback
from models.event import EventType
from utils.exceptions import (
  SerialNotUpdatedError
)
from models.event import EventModel

class SerialUpdatedEvent(BaseSerialEvent):
  class InfoModel(BaseSerialModel):
    serial_key: str
    serial_code: str | None = None # Set code if provided
    serial_data: list[SerialFormFieldValue] | None = None # Set data if provided
    released: datetime | None = None # Set released date if provided

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
          new_field.update(field.model_dump())
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
      changing_existing_code = self.original.code is not None and self.original.code != self.info.serial_code
      if changing_existing_code:
        can_change_code = self.tx.collection('Config').get('allow_serial_code_edit')
        if not can_change_code:
          raise SerialNotUpdatedError(f'Changing serial code is not allowed')

        serial_update['code'] = self.info.serial_code

    # Update data if provided
    if self.info.serial_data:
      serial_update['data'] = self._merge_serial_data()

    # Update released date if provided
    if self.info.released:
      serial_update['released'] = self.info.released
      if self.original.released is None: # should always be None if released is set, but just in case...
        SerialReleasedEvent.create_as_child(self, dict(serial_key=self.info.serial_key))

    # ===================================================================
    # UPDATE SERIAL
    # ===================================================================
    if len(serial_update.keys()) > 1: # Only update if there are changes to be made
      self.tx.collection('Serial').update(serial_update)
      self.response = dict(
        message="Serial updated correctly",
        serial_key=self.info.serial_key
      )
    else:
      self.response = dict(
        message="No changes to be made to serial",
        serial_key=self.info.serial_key
      )

    self.notify_results(dict(
      serial_key = self.info.serial_key,
      notification = SerialNotificationType.UPDATED
    ))


