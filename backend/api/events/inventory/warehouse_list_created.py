from events.inventory.base_inventory import BaseInventoryEvent
from utils.dt import timestamp

class WarehouseListCreated(BaseInventoryEvent):

  def apply(self):
    ...
