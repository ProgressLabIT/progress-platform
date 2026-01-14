from datetime import datetime

from pydantic import Field

from events.serial.base_serial import BaseSerialEvent, BaseSerialModel
from models.event import EventModel, EventType
from models.form import SerialFormFieldValue
from models.serial import ProcessedSerialCode, SerialNotificationType, SerialNotificationErrorCode
from utils.serial import Queries as SerialQueries
from utils.exceptions import (SerialNotUpdatedError, SerialCodeAlreadyPresent)

class SerialUpdatedEvent(BaseSerialEvent):
  class InfoModel(BaseSerialModel):
    serial_key: str
    serial_code: ProcessedSerialCode | None = None # Set code if provided
    serial_data: list[SerialFormFieldValue] | None = None # Set data if provided
    remove_data_from_phases: list[str] | None = None # Set phase keys to remove data from if provided
    unrelease: bool | None = False # Set to True to unrelease the serial

  @classmethod
  def get_event_type(cls):
    return EventType.SERIAL_UPDATED

  def _merge_serial_data(self):
    # Merge data from the original serial with the new data
    # Start with a dict for efficient lookup (handle empty/None data)
    original_data = self.original.get('data') or []
    merged_data_map = {
      field['form_field_key']: field
      for field in original_data
    }

    # Process new data - update existing or add new fields
    for field in self.info.serial_data:
      if field.form_field_key in merged_data_map:
        # Update existing field if value changed
        existing = merged_data_map[field.form_field_key]
        if field.value != existing['value']:
          existing['value'] = field.value
          existing['last_updated'] = self.event_key
      else:
        # Add new field
        new_field = field.model_dump()
        new_field['last_updated'] = self.event_key
        merged_data_map[field.form_field_key] = new_field

    return list(merged_data_map.values())


  def apply(self):
    self.original = self.tx.collection('Serial').get(self.info.serial_key)

    if self.original is None:
      raise SerialNotUpdatedError(f'Serial with key {self.info.serial_key} not found')


    # Init serial update dict
    serial_update = dict(_key=self.info.serial_key)

    # ===================================================================
    # UPDATE SCENARIOS
    # ===================================================================

    # Set code if provided, allow clearing code if empty string is provided (if None nothing happens)
    if self.info.serial_code is not None:
      # Prevent code change if it's protected. Not applicable if serial hasn't been assigned a code yet
      if (
        self.original['code'] is not None and
        self.original['code'] != self.info.serial_code and
        not self.tx.collection('Config').get('allow_serial_code_edit').get('value', True)
      ):
        raise SerialNotUpdatedError(f'Changing serial code is not allowed')

      # Ensure serial code is unique for this product, unless it's empty string (to allow clearing code)
      if len(self.info.serial_code) > 0 and not self.verify_serial_code_free(self.info.serial_key, self.original['product_key'], self.info.serial_code):
        raise SerialCodeAlreadyPresent(f'Cannot update serial, serial code {self.info.serial_code} already in use for this product')

      serial_update['code'] = self.info.serial_code if len(self.info.serial_code) > 0 else None

    # Update data if provided
    if self.info.serial_data:
      serial_update['data'] = self._merge_serial_data()

    # Unrelease serial if provided
    if self.info.unrelease:
      serial_update['released'] = None


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


