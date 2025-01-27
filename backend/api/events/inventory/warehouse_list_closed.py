from events.inventory.base_inventory import BaseInventory
from utils.dt import timestamp
from models.inventory import *

class WarehouseListClosed(BaseInventory):
  movement_list_key: str | None = None

  def apply(self):
    self.tx.collection('MovementList').update(dict(
      _key = self.movement_list_key,
      status = MovementStatus.COMPLETED
    ))
    self.tx.collection('movement').update_match(
      dict(movement_list_key=self.movement_list_key),
      dict(status=MovementStatus.COMPLETED)
    )
