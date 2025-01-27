import traceback

from events.inventory.base_inventory import BaseInventory
from models.inventory import *

from utils.exceptions import (
  InventoryMovementException
)


class MovementCreated(BaseInventory):

  def apply(self):
    try:
      movement_data=self.movement
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
