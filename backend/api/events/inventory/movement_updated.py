import traceback

from events.inventory.base_inventory import BaseInventory

from models.inventory import *
from utils.inventory import Queries
from utils.exceptions import (
  InventoryMovementException
)


class MovementUpdated(BaseInventory):

  def apply(self):
    # TODO: WORKS ONLY FOR RECEIPT MOVEMENTS
    try:
      movement_data=self.movement
      if len(movement_data.split_into) > 0:
        # TODO: use multiple events to confirm the initial movement
        # and automatically generate transfers for the splits
        # If the split is for the whole movement, delete the original movement
        # TODO: confirm whole quantity and generate transfers
        if movement_data.qt_confirmed >= movement_data.qt_planned:
          self.tx.collection('movement').delete(movement_data.key)
        else:
          # If the split is for a partial movement, subtract the quantity from the original movement
          # TODO: confirm partial quantity and generate transfers
          movement_data.qt_planned = movement_data.qt_planned - movement_data.qt_confirmed
          movement_data.qt_confirmed = 0
          self.tx.collection('movement').update(movement_data.model_dump(by_alias=True))
        # Create new completed movements for the splits
        # TODO: transform into related transfer movements with linked events
        new_movements = []
        for split in movement_data.split_into:
          data = movement_data.model_dump()
          data.update(split.model_dump(), status=MovementStatus.COMPLETED)
          new_movements.append(InventoryMovementNew(**data))
        test = self.tx.collection('movement').insert_many([m.model_dump(by_alias=True) for m in new_movements])
      else:
        self.tx.collection('movement').update(InventoryMovement(**movement_data.model_dump()).model_dump(by_alias=True))
        new_movements = [movement_data]
      if movement_data.type == InventoryMovementType.RECEIPT:
        new_inventory_records = [Inventory(
          owned=True,
          product_id="Product/" + m.product_key,
          position_id=m.position_to,
          serial_key=m.serial_key,
          quantity=m.qt_confirmed
        ).model_dump(by_alias=True) for m in new_movements]
        self.tx.collection('is_in_position').insert_many(new_inventory_records)
      # Update list status
      if movement_data.movement_list_key is not None:
        self.tx.aql.execute(
          Queries.UPDATE_MOVEMENT_LIST,
          bind_vars=dict(list_key=movement_data.movement_list_key)
        )
      # ADD OTHER TYPES OF MOVEMENTS
      self.notify_results(dict(
         movement_key = movement_data.key,
         notification = InventoryNotificationType.MOVEMENT_UPDATED,
         message="Movement confirmed correctly",
      ))
    except Exception as e:
      print(traceback.format_exc())
      self.notify_results(dict(
        notification = InventoryNotificationErrorCode.EXCEPTION,
        error_code = InventoryNotificationType.ERROR,
        error = traceback.format_exc()
      ))
      raise InventoryMovementException(f'Cannot update movements', e, traceback.format_exc())
