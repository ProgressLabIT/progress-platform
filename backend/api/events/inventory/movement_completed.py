from typing import Any

from pydantic import Field, model_validator

from events.inventory.base_inventory import BaseInventoryEvent
from events.inventory.inventory_changed import InventoryChangedEvent
from events.serial.serial_created import SerialCreatedEvent
from models.event import EventInfoModel, EventType
from models.inventory import InventoryMovementType, InventoryMovementReferences, MovementStatus
from utils.dt import timestamp
from utils.exceptions import InventoryMovementException

class MovementCompletedEvent(BaseInventoryEvent):

  class InfoModel(EventInfoModel):
    movement_key: str | None = None
    movement_type: InventoryMovementType
    product_key: str
    qt_planned: float
    qt_confirmed: float
    serial_key: str | None = None
    serial_code: str | None = Field(None, exclude=True) # Necessary for receipts not planned in advance
    position_from: str | None = None
    position_to: str | None = None
    movement_list_key: str | None = None
    movement_list_item: float | None = None
    references: InventoryMovementReferences | None = Field(default_factory=InventoryMovementReferences)
    reason: str | None = None
    extra: Any = None

    @model_validator(mode='before')
    def set_implicit_values(cls, values):
      match values.get('movement_type', None):
        case InventoryMovementType.PRODUCTION.value:
          values['position_from'] = 'NULL'
        case InventoryMovementType.CONSUMPTION.value:
          values['position_to'] = 'NULL'
        case InventoryMovementType.SHIPMENT.value:
          values['position_to'] = 'OUT'
        case InventoryMovementType.RECEIPT.value:
          values['position_from'] = 'OUT'
        case _:
          pass

      if values.get('status') in [MovementStatus.STARTED.value, MovementStatus.COMPLETED.value] and values.get('start', None) is None:
        values['start'] = values.get('timestamp')
      if values.get('status') == MovementStatus.COMPLETED.value and values.get('end', None) is None:
        values['end'] = values.get('timestamp')
      return values



  @classmethod
  def get_event_type(cls):
    return EventType.MOVEMENT_COMPLETED

  @property
  def handlers(self):
    return {
      InventoryMovementType.RECEIPT: self._handle_receipt,
      InventoryMovementType.SHIPMENT: self._handle_shipment,
      InventoryMovementType.PRODUCTION: self._handle_production,
      InventoryMovementType.CONSUMPTION: self._handle_consumption,
      InventoryMovementType.ADJUSTMENT: self._handle_adjustment,
      InventoryMovementType.TRANSFER: self._handle_transfer,
    }


  @property
  def event_first(self):
    return True


  def apply(self):
    self.info.end = self.info.timestamp
    if self.info.movement_key is None:
      self.info.created = self.info.start = self.info.timestamp
      self.movement = self._save_movement()
    else:
      self.movement = self._update_movement()

    self.info.movement_key = self.movement.key
    self.handlers[self.info.movement_type]()

  def _update_movement(self):
    pass


  def _handle_production(self):
    InventoryChangedEvent.create_as_child(self, dict(
      position_key = self.info.position_to,
      product_key = self.info.product_key,
      serial_key = self.info.serial_key,
      quantity_change = self.info.qt_confirmed
    ))

  def _handle_consumption(self):
    InventoryChangedEvent.create_as_child(self, dict(
      position_key = self.info.position_from,
      product_key = self. info.product_key,
      serial_key = self.info.serial_key,
      quantity_change = -self.info.qt_confirmed
    ))

  def _handle_receipt(self):
    """
    # SCENARIO 1: Receipt of product with traceability
    - Ensure serial code is provided
    - Create serial if movement is planned, serial is released, but not available
    - Create new inventory record

    # SCENARIO 2: Receipt of product with no traceability
    - Identify if inventory record (product/position) exists
    - Update quantity if it exists
    - Create new inventory record if it doesn't exist
    - Ignore serial code if provided
    """
    # TODO: handle serial creation if product requires it

    self._get_product()

    product_requires_serial = getattr(self.product, 'traceability_level', False)

    # SCENARIO 1: Receipt of product with traceability
    if product_requires_serial:
      self._handle_receipt_with_traceability()
      return

    # SCENARIO 2: Receipt of product without traceability.
    InventoryChangedEvent.create_as_child(self, dict(
      position_key = self.info.position_to,
      product_key = self.info.product_key,
      serial_key = self.info.serial_key,
      quantity_change = self.info.qt_confirmed
    ))


  def _handle_receipt_with_traceability(self):
    serial_code = self.info.serial_code or ''
    serial_code_provided = len(serial_code) > 0

    if not serial_code_provided:
      raise InventoryMovementException(f'Serial code is required for receipts of products with traceability')

    product_key = self.info.product_key

    # First try to find an existing serial
    serial_cursor = self.tx.collection('Serial').find(dict(
      code=serial_code,
      product_key=product_key,
      deleted=False
    ))
    if serial_cursor.count() == 0:
      # Serial does not exist, create new serial
      new_serial_key = SerialCreatedEvent.create_as_child(self, dict(
        product_key = self.info.product_key,
        code = serial_code,
        user_key = self.info.user_key,
      ))['serial_key']
      self.info.serial_key = new_serial_key

    else:
      # Serial exists, check if it's in inventory
      existing_serial = serial_cursor.next()
      self.info.serial_key = existing_serial['_key']

      inventory_exists = self.tx.collection('is_in_position').find(dict(
        serial_key=existing_serial['_key']
      )).count() > 0

      if inventory_exists:
        raise InventoryMovementException(f'Serial is already in inventory')

    # Serial exists and is not in inventory, add to inventory
    InventoryChangedEvent.create_as_child(self, dict(
      position_key = self.info.position_to,
      product_key = self.info.product_key,
      serial_key = self.info.serial_key,
      quantity_change = 1
    ))


  def _handle_shipment(self):
    self._get_product()
    product_requires_serial = getattr(self.product, 'traceability_level', False)

    # SCENARIO 1: Receipt of product with traceability
    if product_requires_serial:
      # INVENTORY_CHANGED is for confirmed movements only so serial_key must be provided
      if self.info.serial_key is None:
        raise InventoryMovementException(f'Serial key is required to confirm shipment of products with traceability')

      serial_exists = self.tx.collection('Serial').has(self.info.serial_key)
      if not serial_exists:
        raise InventoryMovementException(f'Serial {self.info.serial_key} not found')

    try:
      InventoryChangedEvent.create_as_child(self, dict(
        position_key = self.info.position_from,
        product_key = self.info.product_key,
        serial_key = self.info.serial_key,
        quantity_change = -self.info.qt_confirmed
      ))
    except InventoryMovementException as e:
      raise InventoryMovementException(f'Cannot ship product {self.product.code} from provided position, not enough inventory available') from e


  def _handle_adjustment(self):
    self._get_product()
    try:
      InventoryChangedEvent.create_as_child(self, dict(
        position_key = self.info.position_to,
        product_key = self.info.product_key,
        serial_key = self.info.serial_key,
        quantity_change = self.info.qt_confirmed
      ))
    except InventoryMovementException as e:
      raise InventoryMovementException(f'Cannot adjust inventory for product {self.product.code} in the provided position.') from e


  def _handle_transfer(self):
    # CONTAINER TRANSFER ======================================================
    # the product is not moved, only the position hierarchy is changed
    if self.info.product_key is None and self.info.serial_key is None and self.info.position_from is not None:
      position = self.tx.collection('Position').get(self.info.position_from)
      if position['fixed']:
        raise InventoryMovementException(f'Cannot transfer fixed position')
      match = dict(_from=self.info.position_from)
      update = dict(_to=self.info.position_to)
      self.tx.collection('is_in_position').update_match(match, update)
      return

    # PRODUCT TRANSFER ======================================================
    # the product is moved, and the inventory record (is_in_position) is updated

    # Update start position inventory
    try:
      InventoryChangedEvent.create_as_child(self, dict(
        position_key = self.info.position_from,
        product_key = self.info.product_key,
        serial_key = self.info.serial_key,
        quantity_change = -self.info.qt_confirmed
      ))
    except InventoryMovementException as e:
      self._get_product()
      raise InventoryMovementException(f'Cannot transfer product {self.product.code} from desired position: not enough inventory available') from e

    # Update destination position inventory
    InventoryChangedEvent.create_as_child(self, dict(
      position_key = self.info.position_to,
      product_key = self.info.product_key,
      serial_key = self.info.serial_key,
      quantity_change = self.info.qt_confirmed
    ))

