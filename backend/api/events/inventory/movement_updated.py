import traceback

from events.inventory.base_inventory import BaseInventory, BaseInventoryModel
from models.event import EventType
from models.event import EventModel
from models.inventory import *
from utils.inventory import Queries

from utils.exceptions import (
  InventoryMovementException
)

class MovementUpdatedModel(BaseInventoryModel):
    event_type: str = EventType.MOVEMENT_UPDATED.name

class MovementUpdated(BaseInventory):
  event_data: MovementUpdatedModel

  def set_model(self, base_model: EventModel):
    self.info = MovementUpdatedModel(**base_model.model_dump())

  def apply(self):
    """Used for updating planned movement"""
    try:
      movement_data=self.info.movement
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
          new_records = [m.model_dump(by_alias=True) for m in new_movements]
        test = self.tx.collection('movement').insert_many(new_records)
      else:
        self.tx.collection('movement').update(movement_data.model_dump(by_alias=True))
        new_movements = [movement_data]
      if movement_data.type == InventoryMovementType.RECEIPT:
        for movement in new_movements:
          if movement.serial_key is not None:
            # For serialized items, always create new inventory record if not already present
            existing_inventory = self.tx.collection('is_in_position').find(dict(
              _from=f'Product/{movement.product_key}',
              serial_key=movement.serial_key
            )).count() > 0
            if existing_inventory:
                raise InventoryMovementException("Serial already in inventory")
            else:
              self.tx.collection('is_in_position').insert(Inventory(
                owned=True,
                product_id="Product/" + movement.product_key,
                position_id=movement.position_to,
                serial_key=movement.serial_key,
                quantity=1
              ).model_dump(by_alias=True))
          else:
            # For non-serialized items, check if inventory exists and update quantity
            try:
              existing_inventory = self.tx.collection('is_in_position').find(dict(
                _from=f'Product/{movement.product_key}',
                _to=movement.position_to,
                serial_key=None
              )).next()
              final_qty = existing_inventory['quantity'] + movement.qt_confirmed
              self.tx.collection('is_in_position').update(dict(
                _key=existing_inventory['_key'],
                quantity=final_qty
              ))
            except StopIteration:
              # No existing inventory found, create new record
              self.tx.collection('is_in_position').insert(Inventory(
                owned=True,
                product_id="Product/" + movement.product_key,
                position_id=movement.position_to,
                quantity=movement.qt_confirmed
              ).model_dump(by_alias=True))
      if movement_data.type == InventoryMovementType.SHIPMENT:
        for movement in new_movements:
          if movement.serial_key is not None:
            self.tx.collection('is_in_position').delete_match(dict(
              _from=f'Product/{movement.product_key}',
              _to=movement.position_from, # the position from is the one where the product is shipped, _to in the inventory record
              serial_key=movement.serial_key
            ))
          else:
            try:
              existing_inventory = self.tx.collection('is_in_position').find(dict(
                _from=f'Product/{movement.product_key}',
                _to=movement.position_from,
                serial_key=None
              )).next()
              final_qty = existing_inventory['quantity'] - movement.qt_confirmed
              if final_qty == 0:
                self.tx.collection('is_in_position').delete(existing_inventory['_key'])
              else:
                self.tx.collection('is_in_position').update(dict(
                  _key=existing_inventory['_key'],
                  quantity=final_qty
                ))
            except StopIteration:
              # No existing inventory found, create new record
              raise InventoryMovementException(f'Cannot find product inventory to ship')
      # Update list status
      #if movement_data.movement_list_key is not None:
      #  self.tx.aql.execute(
      #    Queries.UPDATE_MOVEMENT_LIST,
      #    bind_vars=dict(list_key=movement_data.movement_list_key)
      #  )
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
