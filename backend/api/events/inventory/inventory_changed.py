from typing import Any

from pydantic import Field

from events.inventory.base_inventory import BaseInventoryEvent
from models.event import EventInfoModel, EventType
from models.inventory import Inventory
from utils.exceptions import InventoryMovementException

class InventoryChangedEvent(BaseInventoryEvent):

  class InfoModel(EventInfoModel):
    position_id: str
    product_key: str
    serial_key: str | None = None
    quantity_change: float

  @classmethod
  def get_event_type(cls):
    return EventType.INVENTORY_CHANGED

  def apply(self):
    match_criteria = dict(
      _from=f'Product/{self.info.product_key}',
      _to=self.info.position_id,
      serial_key=self.info.serial_key
    )
    try:
      current_record = self.tx.collection('is_in_position').find(match_criteria).next()
      final_qty = current_record['quantity'] + self.info.quantity_change

      if final_qty < 0:
        raise InventoryMovementException('Cannot reduce inventory: insufficient quantity')

      elif final_qty == 0:
        self.tx.collection('is_in_position').delete(current_record['_key'])
        return True
    # supplier_key: Any | None = None
      else:
        self.tx.collection('is_in_position').update({
          '_key': current_record['_key'],
          'quantity': final_qty
        })

    except StopIteration:
      # No matching inventory record found
      if self.info.quantity_change > 0:
        # Create new inventory record
        self.tx.collection('is_in_position').insert(Inventory(
          **match_criteria,
          quantity = self.info.quantity_change,
          owned = True
        ))
        return False
      else:
        raise InventoryMovementException # Enrich with more information from the caller
