from pydantic import Field

from events.inventory.base_inventory import BaseInventoryEvent
from events.serial.serial_created import SerialCreatedEvent
from models.inventory import InventoryMovementNew, MovementStatus, InventoryMovementType
from models.event import EventInfoModel, EventType
from utils.exceptions import InventoryMovementException


class MovementPlannedEvent(BaseInventoryEvent):
  class InfoModel(InventoryMovementNew, EventInfoModel):
    new_movement_key: str | None = None

  @classmethod
  def get_event_type(cls):
    return EventType.MOVEMENT_PLANNED

  @classmethod
  def get_tx_collections(cls):
    return [
      'movement',
      'Serial',
    ]

  def _handle_serial(self):

    serial_collection = self.tx.collection('Serial')

    # ===============================================
    # Handle serial key
    # ===============================================
    # In case of serial key provided, do not attempt to create a new serial as it's assumed to already exist and it's active
    # Raise an error if it's not the case
    if self.info.serial_key is not None:
      # Ensure key exists and serial is not deleted
      try:
        serial = serial_collection.find(dict(_key=self.info.serial_key)).next()
      except StopIteration:
        raise InventoryMovementException(f"Serial {self.info.serial_key} for product {self.product['code']} does not exist")
      if serial.get('deleted', False):
        raise InventoryMovementException(f"Serial {self.info.serial_key} for product {self.product['code']} is deleted")

    # ===============================================
    # Handle serial code
    # ===============================================
    # In case of receipt by code, create serial if it doesn't exist or raise an error if it's already in inventory
    # In other types of movements, accept the movement regardless of whether it is in inventory or not,
    # but raise an error if it doesn't exist.
    try:
      serial = serial_collection.find(dict(
        code=self.info.serial_code,
        product_key=self.info.product_key,
        deleted=False
      )).next()
      self.info.serial_key = serial['_key']
    except StopIteration: # Serial does not exist
      # If the movement is a receipt, create a new serial
      if self.info.movement_type == InventoryMovementType.RECEIPT:
        self.info.serial_key = SerialCreatedEvent.create_as_child(self, dict(
          code=self.info.serial_code,
          product_key=self.info.product_key,
          released=self.info.timestamp
        ))['serial_key']
      else: # In other types of movements, raise an error if the serial does not exist
        raise InventoryMovementException(f"Serial {self.info.serial_code} for product {self.product['code']} does not exist")

    # Check inventory
    try:
      inventory = self.tx.collection('is_in_position').find(dict(serial_key=self.info.serial_key)).next()
    except StopIteration: # Serial is not in inventory
      return
    else: # Serial is already in inventory
      if self.info.movement_type == InventoryMovementType.RECEIPT:
        raise InventoryMovementException(f"Can't plan receipt of serial {self.info.serial_code} for product {self.product['code']} as it's already in inventory")



  def apply(self):
    if self.info.status != MovementStatus.PLANNED:
      raise ValueError("Movement status can only be `planned`.")

    # Check if product has traceability enabled
    self.product = self.tx.collection('Product').get(self.info.product_key)
    if self.product.get('traceability_level', False):
      # TEMPORARY: Prevent planning receipts for products with traceability enabled without serial code or key
      if self.info.serial_code is None and self.info.serial_key is None:
        raise InventoryMovementException(f"Can't plan receipt for product {self.product['code']}. Traceability is enabled but no serial code or key provided")

      self._handle_serial()

    else:
      # Handle serial creation if product requires it
      if self.info.serial_code is not None or self.info.serial_key is not None:
        raise InventoryMovementException(f"Can't handle serial for product {self.product['code']}. Traceability is not enabled.")

    # Save movement
    new_movement = self._save_movement()
    self.info.new_movement_key = new_movement.key
    self.response = new_movement
