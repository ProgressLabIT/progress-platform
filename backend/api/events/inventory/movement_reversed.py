from events.inventory.base_inventory import BaseInventoryEvent
from events.inventory.inventory_changed import InventoryChangedEvent
from events.inventory.movement_planned import MovementPlannedEvent
from models.event import EventType, EventInfoModel
from models.inventory import InventoryMovement, InventoryMovementReferences, InventoryMovementNew, InventoryMovementType, MovementStatus
from utils.exceptions import InventoryMovementException
from utils.float_precision import float_greater_than

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

  # =====================================================================
  # MAIN LOGIC
  # =====================================================================

  def apply(self):
    # Get and validate original movement
    movement_to_revert = InventoryMovement(**self.tx.collection('movement').get(self.info.original_movement_key))
    self._validate_movement(movement_to_revert)

    # Handle movement list: to be done first to more easily calculate list item quantities
    # distinguishing between movements already reversed and the one being reverted
    self._handle_movement_list(movement_to_revert)

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
      movement_list_key=movement_to_revert.movement_list_key,
      movement_list_item=movement_to_revert.movement_list_item,
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
          quantity_change=movement_qt
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

    # Use tolerance comparison for reversal validation
    if self.info.quantity_to_revert and float_greater_than(self.info.quantity_to_revert, movement_to_revert.qt_confirmed):
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

  def _handle_movement_list(self, movement_to_revert: InventoryMovement):
    """
    Restore the original movement planned quantity in case of partial movement reversal or create a new one in case of fully completed movement.
    """
    if movement_to_revert.movement_list_key is None:
      return

    # Get movement list item - only those that haven't been reversed yet and are not reversals themselves
    list_item_movements_query = """
      FOR m IN movement
      FILTER
        m.movement_list_key == @movement_list_key
        AND m.movement_list_item == @movement_list_item
        AND m.type != 'reversal'
        AND m.inverse_movement_key == null
      RETURN m
    """
    list_item_movements = [
      InventoryMovement(**m)
      for m in self.tx.aql.execute(
        list_item_movements_query,
        bind_vars=dict(
          movement_list_key=movement_to_revert.movement_list_key,
          movement_list_item=movement_to_revert.movement_list_item
        )
      )
    ]

    # Calculate planned/completed quantity: (original movement hasn't been reversed yet)
    list_item_planned_quantity = sum(m.qt_planned for m in list_item_movements)
    list_item_completed_quantity = sum(m.qt_confirmed for m in list_item_movements)

    remaining_partial = next((m for m in list_item_movements if m.qt_confirmed == 0), None)

    if remaining_partial is not None and movement_to_revert.serial_key is None:
      self.tx.collection('movement').update(dict(
        _key=remaining_partial.key,
        qt_planned=remaining_partial.qt_planned + movement_to_revert.qt_confirmed
      ))

    else:
      # Create new movement
      MovementPlannedEvent.create_as_child(self, dict(
        position_from=movement_to_revert.position_from,
        position_to=movement_to_revert.position_to,
        product_key=movement_to_revert.product_key,
        movement_list_key=movement_to_revert.movement_list_key,
        movement_list_item=movement_to_revert.movement_list_item,
        serial_key=movement_to_revert.serial_key,
        qt_planned=movement_to_revert.qt_planned,
        movement_type=movement_to_revert.type,
        status=MovementStatus.PLANNED,
        references=movement_to_revert.references,
        reason=f"Movement {movement_to_revert.key} has been reverted"
      ))
