

from events.inventory.base_inventory import BaseInventoryEvent
from models.event import EventInfoModel, EventType
from models.inventory import Inventory
from utils.exceptions import InventoryMovementException


class InventoryChangedEvent(BaseInventoryEvent):

  class InfoModel(EventInfoModel):
    position_key: str
    product_key: str
    serial_key: str | None = None
    quantity_change: float

  @classmethod
  def get_event_type(cls):
    return EventType.INVENTORY_CHANGED

  def apply(self):
    match_criteria = dict(
      _from=f'Product/{self.info.product_key}',
      _to=f'Position/{self.info.position_key}',
      serial_key=self.info.serial_key
    )
    try:
      current_record = self.tx.collection('is_in_position').find(match_criteria).next()
      final_qty = current_record['quantity'] + self.info.quantity_change

      if final_qty < 0:
        self._get_product()
        position = self.tx.collection('Position').get(self.info.position_key)
        raise InventoryMovementException(f'Cannot reduce inventory for product {self.product.code} in position {position["code"]} of quantity {self.info.quantity_change}: only {current_record["quantity"]} left.')

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
        self._get_product()
        position = self.tx.collection('Position').get(self.info.position_key)
        raise InventoryMovementException(f"Cannot reduce inventory for product {self.product.code} in position {position['code']}. No inventory found.")
