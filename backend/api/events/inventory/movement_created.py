import traceback

from events.inventory.base_inventory import BaseInventory, BaseInventoryModel
from models.inventory import *
from events.event_type import EventType
from events.event_model import EventModel
from typing import List

from utils.exceptions import (
  InventoryMovementException
)

class MovementCreatedModel(BaseInventoryModel):
    event_type: str = EventType.MOVEMENT_CREATED.name
    batch_key: str | None = None

class MovementCreated(BaseInventory):
  event_data: MovementCreatedModel

  def __init__(self, **data):
    super().__init__(**data)

  def set_model(self, base_model: EventModel):
   self.event_data = MovementCreatedModel(**base_model.model_dump())


  def validate_event(self):
    return super().validate_event()

  def apply(self):
    try:
      # TODO: allow inserting movements by product/serial code
      movement_data=self.event_data.movement
      self.adjust_inventory()
      new_movement_record = InventoryMovement(**movement_data.model_dump())
      movement_key = self.tx.collection('movement').insert(new_movement_record)['_key']
      self.notify_results(dict(
         movement_key = movement_key,
         notification = InventoryNotificationType.MOVEMENT_ADDED,
         message="Movement created correctly",
      ))
    except Exception as e:
      print(traceback.format_exc())
      self.notify_results(dict(
         notification = InventoryNotificationErrorCode.EXCEPTION,
         error_code = InventoryNotificationType.ERROR,
         error = traceback.format_exc()
      ))
      raise InventoryMovementException(f'Cannot add movements', e, traceback.format_exc())
