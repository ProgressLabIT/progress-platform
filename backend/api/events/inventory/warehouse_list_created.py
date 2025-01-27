from events.inventory.base_inventory import BaseInventory
from utils.dt import timestamp

class WarehouseListCreated(BaseInventory):

  def apply(self):
    ...
