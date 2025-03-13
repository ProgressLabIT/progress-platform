from events.inventory.base_inventory import BaseInventoryEvent
from events.inventory.inventory_changed import InventoryChangedEvent
from models.event import EventType, EventInfoModel
from models.inventory import InventoryMovement, InventoryMovementReferences, InventoryMovementNew, InventoryMovementType
from utils.exceptions import InventoryMovementException

class MovementRevertedEvent(BaseInventoryEvent):
  """
  Reverts movements by:
  - Marking the original movement as reverted
  - Creating a new movement in the opposite direction
  - Updating inventory levels accordingly by reversing the original movement's effects
  """

  class InfoModel(EventInfoModel):
    original_movement_key: str
    inverse_movement_key: str | None = None
    reason: str | None = None

  @classmethod
  def get_event_type(cls):
    return EventType.MOVEMENT_REVERTED

  @property
  def event_first(self):
    return True

  def apply(self):
    # Get original movement
    movement_to_revert = InventoryMovement(**self.tx.collection('movement').get(self.info.original_movement_key))
    if not movement_to_revert:
      raise ValueError(f'Movement {self.info.original_movement_key} not found')

    if movement_to_revert.reverted:
      raise ValueError(f'Movement {self.info.original_movement_key} has already been reverted')

    if movement_to_revert.qt_confirmed == 0:
      raise ValueError(f'Movement {self.info.original_movement_key} has no confirmed quantity to revert')

    # Mark original movement as reverted
    self.tx.collection('movement').update({
      '_key': self.info.original_movement_key,
      'reverted': self.event_key
    })

    references = movement_to_revert.references.copy() if movement_to_revert.references is not None else InventoryMovementReferences()
    references.origin_movement_key = self.info.original_movement_key

    # All movement except adjustment are reverted by inverting positions.
    # Adjustments must be handled inverting the quantity
    movement_sign = -1 if movement_to_revert.type == InventoryMovementType.ADJUSTMENT else 1

    # Create inverse movement
    inverse = InventoryMovementNew(
      position_from=movement_to_revert.position_to,
      position_to=movement_to_revert.position_from,
      product_key=movement_to_revert.product_key,
      movement_type=InventoryMovementType.REVERSAL,
      serial_key=movement_to_revert.serial_key,
      qt_planned=0,
      qt_confirmed=movement_to_revert.qt_confirmed * movement_sign,
      references=references,
      reason=self.info.reason,
      created=self.info.timestamp,
      start=self.info.timestamp,
      end=self.info.timestamp,
      user_key=self.info.user_key
    )

    new_movement = self.tx.collection('movement').insert(inverse.model_dump(by_alias=True), return_new=True)['new']
    new_movement_key = new_movement['_key']
    self.info.inverse_movement_key = new_movement_key

    # Handle inventory changes based on original movement type
    # Will raise an InventoryMovementException if the inventory is not available when trying to reduce quantity
    match movement_to_revert.type:
      case InventoryMovementType.PRODUCTION:
        # Original added inventory, so we remove it
        InventoryChangedEvent.create_as_child(self, dict(
          position_key=movement_to_revert.position_to.split('/')[-1],
          product_key=movement_to_revert.product_key,
          serial_key=movement_to_revert.serial_key,
          quantity_change=-movement_to_revert.qt_confirmed
        ))

      case InventoryMovementType.CONSUMPTION:
        # Original removed inventory, so we add it back
        InventoryChangedEvent.create_as_child(self, dict(
          position_key=movement_to_revert.position_from.split('/')[-1],
          product_key=movement_to_revert.product_key,
          serial_key=movement_to_revert.serial_key,
          quantity_change=movement_to_revert.qt_confirmed
        ))

      case InventoryMovementType.RECEIPT:
        # Original added inventory, so we remove it
        InventoryChangedEvent.create_as_child(self, dict(
          position_key=movement_to_revert.position_to.split('/')[-1],
          product_key=movement_to_revert.product_key,
          serial_key=movement_to_revert.serial_key,
          quantity_change=-movement_to_revert.qt_confirmed
        ))

      case InventoryMovementType.SHIPMENT:
        # Original removed inventory, so we add it back
        InventoryChangedEvent.create_as_child(self, dict(
          position_key=movement_to_revert.position_from.split('/')[-1],
          product_key=movement_to_revert.product_key,
          serial_key=movement_to_revert.serial_key,
          quantity_change=movement_to_revert.qt_confirmed
        ))

      case InventoryMovementType.TRANSFER:
        # Can't revert container transfers, we don't have the original position of the container
        if movement_to_revert.product_key is None and movement_to_revert.serial_key is None:
          raise NotImplementedError('Reverting container transfers is not supported')

        # Product transfers
        # First remove from current position
        InventoryChangedEvent.create_as_child(self, dict(
          position_key=movement_to_revert.position_to.split('/')[-1],
          product_key=movement_to_revert.product_key,
          serial_key=movement_to_revert.serial_key,
          quantity_change=-movement_to_revert.qt_confirmed
        ))
        # Then add back to original position
        InventoryChangedEvent.create_as_child(self, dict(
          position_key=movement_to_revert.position_from.split('/')[-1],
          product_key=movement_to_revert.product_key,
          serial_key=movement_to_revert.serial_key,
          quantity_change=movement_to_revert.qt_confirmed
        ))


      case InventoryMovementType.ADJUSTMENT:
        # Simply do the opposite of the original adjustment
        InventoryChangedEvent.create_as_child(self, dict(
          position_key=movement_to_revert.position_to.split('/')[-1], # position_to/position_from is the same for adjustments
          product_key=movement_to_revert.product_key,
          serial_key=movement_to_revert.serial_key,
          quantity_change=-movement_to_revert.qt_confirmed
        ))

      case _:
        raise InventoryMovementException(f"Cannot revert movement of type {movement_to_revert.type}")

    self.response = dict(
      message=f'Movement {self.info.original_movement_key} has been reverted',
      inverse_movement=new_movement
    )