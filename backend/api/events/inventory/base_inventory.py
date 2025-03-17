import copy
import json
from abc import ABC

from events.base_event import BaseEvent
from managers.notification_manager import NotificationManager
from models.event import EventModel
from models.inventory import *
from models.product import ProductFull
from utils.exceptions import InventoryMovementException
from utils.inventory import Queries as InventoryQueries


class BaseInventoryModel(EventModel):
    # Inventory fields
    movement: InventoryMovementNew | InventoryMovementUpdate | None = None
    movement_list: MovementListNew | None = None
    movement_key: str | None = None

class BaseInventoryEvent(BaseEvent, ABC):

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

  def _get_production_position(self):
    wo = self.tx.collection('WorkOrder').get(self.info.references.work_order_key)
    return wo['output_position_key']

  def post_processing(self):
    self.notify_results(dict(
      notification = InventoryNotificationType.MOVEMENT_ADDED
    ))

  def _get_product(self):
    try:
      self.product = ProductFull(**self.tx.collection('Product').get(self.info.product_key))
    except StopIteration:
      raise InventoryMovementException('Product not found')

  def can_be_conflated(self, notification_type):
    return notification_type not in [InventoryNotificationType.ERROR]

  def notify_results(self, notification):
    notification['subtopic'] = "inventory-notification"
    inventory_event = copy.deepcopy(self.info)
    if 'error' in notification:
      inventory_event.event_type = "INVENTORY_"+notification['notification']+" ("+notification['error']+")"
    else:
      inventory_event.event_type = "INVENTORY_"+notification['notification']
    inventory_event.movement_key = notification.get('movement_key')
    #self.tx.collection('Event').insert(inventory_event.model_dump())
    if self.can_be_conflated(notification.get('notification')):
      NotificationManager.getInstance().notifyConflated(subtopic="inventory-notification", message=json.dumps(notification), delay=5)
    else:
      NotificationManager.getInstance().notify(key=notification.get('movement_key'), notification=json.dumps(notification))




