from events.inventory.base_inventory import BaseInventoryEvent
from events.inventory.inventory_changed import InventoryChangedEvent
from models.event import EventType, EventInfoModel
from models.inventory import InventoryMovement, InventoryMovementReferences, InventoryMovementNew, InventoryMovementType
from utils.exceptions import InventoryMovementException

class MovementReversedEvent(BaseInventoryEvent):
  """
  Reverts movements by:
  - Marking the original movement as reverted
  - Creating a new movement in the opposite direction
  - Updating inventory levels accordingly by reversing the original movement's effects
  """

  class InfoModel(EventInfoModel):
    original_movement_key: str
    inverse_movement_key: str | None = None
    quantity_to_revert: float | None = None
    reason: str | None = None

  @classmethod
  def get_event_type(cls):
    return EventType.MOVEMENT_REVERSED

  @property
  def event_first(self):
    return True


  # =====================================================================
  # MAIN LOGIC
  # =====================================================================

  def apply(self):
    # Get and validate original movement
    movement_to_revert = InventoryMovement(**self.tx.collection('movement').get(self.info.original_movement_key))
    self._validate_movement(movement_to_revert)

    # Calculate movement quantity
    movement_qt = self._calculate_movement_quantity(movement_to_revert)

    # Store reversal movement and get new movement key
    new_movement_key, new_movement = self._store_reversal_movement(movement_to_revert, movement_qt)
    self.info.inverse_movement_key = new_movement_key

    # Adjust inventory levels
    self._adjust_inventory(movement_to_revert, movement_qt)



    self.response = dict(
      message=f'Movement {self.info.original_movement_key} has been reverted',
      inverse_movement=new_movement
    )



  # =====================================================================
  # HELPER METHODS
  # =====================================================================

  def _store_reversal_movement(self, movement_to_revert: InventoryMovement, movement_qt: float) -> str:
    """
    Creates and stores the reversal movement record

    Args:
        movement_to_revert: Original movement being reverted
        movement_qt: Quantity for the reversal movement

    Returns:
        str: Key of the new reversal movement
    """
    references = movement_to_revert.references.copy() if movement_to_revert.references is not None else InventoryMovementReferences()
    references.origin_movement_key = self.info.original_movement_key

    inverse = InventoryMovementNew(
      position_from=movement_to_revert.position_to,
      position_to=movement_to_revert.position_from,
      product_key=movement_to_revert.product_key,
      movement_type=InventoryMovementType.REVERSAL,
      serial_key=movement_to_revert.serial_key,
      qt_planned=0,
      qt_confirmed=movement_qt,
      references=references,
      reason=self.info.reason,
      created=self.info.timestamp,
      start=self.info.timestamp,
      end=self.info.timestamp,
      user_key=self.info.user_key
    )

    new_movement = self.tx.collection('movement').insert(inverse.model_dump(by_alias=True), return_new=True)['new']
    new_movement_key = new_movement['_key']

    # Update original movement
    self.tx.collection('movement').update(dict(
      _key=self.info.original_movement_key,
      inverse_movement_key=new_movement_key
    ))

    return new_movement_key, new_movement

  # =====================================================================

  def _adjust_inventory(self, movement_to_revert: InventoryMovement, movement_qt: float):
    """
    Adjusts inventory levels based on movement type

    Args:
        movement_to_revert: Original movement being reverted
        movement_qt: Quantity for the inventory adjustment
    """
    match movement_to_revert.type:
      case InventoryMovementType.PRODUCTION | InventoryMovementType.RECEIPT:
        # Original added inventory, so we remove it
        InventoryChangedEvent.create_as_child(self, dict(
          position_key=movement_to_revert.position_to.split('/')[-1],
          product_key=movement_to_revert.product_key,
          serial_key=movement_to_revert.serial_key,
          quantity_change=-movement_qt
        ))

      case InventoryMovementType.CONSUMPTION | InventoryMovementType.SHIPMENT:
        # Original removed inventory, so we add it back
        InventoryChangedEvent.create_as_child(self, dict(
          position_key=movement_to_revert.position_from.split('/')[-1],
          product_key=movement_to_revert.product_key,
          serial_key=movement_to_revert.serial_key,
          quantity_change=movement_qt
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
          quantity_change=-movement_qt
        ))
        # Then add back to original position
        InventoryChangedEvent.create_as_child(self, dict(
          position_key=movement_to_revert.position_from.split('/')[-1],
          product_key=movement_to_revert.product_key,
          serial_key=movement_to_revert.serial_key,
          quantity_change=movement_qt
        ))

      case InventoryMovementType.ADJUSTMENT:
        # Simply do the opposite of the original adjustment
        InventoryChangedEvent.create_as_child(self, dict(
          position_key=movement_to_revert.position_to.split('/')[-1], # position_to/position_from is the same for adjustments
          product_key=movement_to_revert.product_key,
          serial_key=movement_to_revert.serial_key,
          quantity_change=-movement_qt
        ))

      case _:
        raise InventoryMovementException(f"Cannot revert movement of type {movement_to_revert.type}")

  # =====================================================================

  def _validate_movement(self, movement_to_revert: InventoryMovement):
    """
    Validates that the movement can be reverted

    Args:
        movement_to_revert: Movement to validate

    Raises:
        ValueError: If the movement cannot be reverted
    """
    if not movement_to_revert:
      raise ValueError(f'Movement {self.info.original_movement_key} not found')

    if movement_to_revert.inverse_movement_key:
      raise ValueError(f'Movement {self.info.original_movement_key} has already been reverted')

    if movement_to_revert.qt_confirmed == 0:
      raise ValueError(f'Movement {self.info.original_movement_key} has no confirmed quantity to revert')

    if self.info.quantity_to_revert and self.info.quantity_to_revert > movement_to_revert.qt_confirmed:
      raise ValueError(f"Can't revert partial quantity {self.info.quantity_to_revert} for movement {self.info.original_movement_key}, it's greater than the movement quantity {movement_to_revert.qt_confirmed}")

  # =====================================================================

  def _calculate_movement_quantity(self, movement_to_revert: InventoryMovement):
    """
    Calculates the movement quantity to revert
    """
    # Calculate movement quantity
    movement_sign = -1 if movement_to_revert.type == InventoryMovementType.ADJUSTMENT else 1
    movement_abs_qt = self.info.quantity_to_revert if self.info.quantity_to_revert is not None else movement_to_revert.qt_confirmed
    movement_qt = movement_abs_qt * movement_sign

    return movement_qt

  # =====================================================================

  def _handle_movement_list(self):
    """
    Reopens reverted movement list item if necessary
    """
    pass