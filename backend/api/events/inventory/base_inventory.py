import json
import logging
from abc import ABC

from events.base_event import BaseEvent
from models.event import EventModel
from models.inventory import *
from models.product import ProductFull
from utils.exceptions import InventoryMovementException
from utils.inventory import Queries as InventoryQueries
from utils.nats_client import publish_sync, subtopic_to_subject

logger = logging.getLogger("base_inventory")


class BaseInventoryModel(EventModel):
  # Inventory fields
  movement: InventoryMovementNew | InventoryMovementUpdate | None = None
  movement_list: MovementListNew | None = None
  movement_key: str | None = None

class BaseInventoryEvent(BaseEvent, ABC):
  _notification_subtopic = "inventory"

  @classmethod
  def get_tx_collections(cls):
    return [
      'is_in_position',
      'Serial',
      'movement'
    ]

  def _ensure_inventory_management_enabled(self):
    warehouse_enabled = self.tx.collection('Config').get('enable_inventory_management')
    if warehouse_enabled is None or not warehouse_enabled.get('value', False):
      return False
    return True


  def _get_product_inventory_config(self, product_keys):
    products_inventory_config = self.tx.aql.execute(
      InventoryQueries.PRODUCTS_INVENTORY_CONFIG,
      bind_vars=dict(product_keys=product_keys)
    ).next()
    return products_inventory_config


  def _save_movement(self):
    movement_data = InventoryMovementNew(**self.info.model_dump()).model_dump(by_alias=True)
    movement_record = self.tx.collection('movement').insert(movement_data, return_new=True)['new']
    return InventoryMovement(**movement_record)


  def _ensure_position_id(self, position_string):
    if position_string.startswith('Position/'):
      return position_string
    else:
      return f"Position/{position_string}"

  def _ensure_position_not_deleted(self, position_key: str):
    """Validate that a position exists and is not deleted."""
    if position_key in ['NULL', 'OUT', 'IN']:
      return  # Special positions
    position = self.tx.collection('Position').get(position_key)
    if position is None:
      raise InventoryMovementException(f'Position {position_key} not found')
    if position.get('deleted', False):
      raise InventoryMovementException(f'Position {position["code"]} is deleted')

    return position

  def _get_production_position(self):
    wo = self.tx.collection('WorkOrder').get(self.info.references.work_order_key)
    return wo['output_position_key']

  def _get_product(self):
    if self.info.product_key is None:
      self.product = None
      return

    try:
      self.product = ProductFull(**self.tx.collection('Product').get(self.info.product_key))
    except StopIteration:
      raise InventoryMovementException('Product not found')

  def notify_error(self, notification):
    """Send an immediate error notification via NATS (bypasses auto-publish since tx will abort)."""
    notification['subtopic'] = "inventory"
    try:
      subject = subtopic_to_subject("inventory")
      publish_sync(subject, json.dumps(notification, default=str))
    except Exception:
      logger.exception("Failed to publish inventory error notification")




