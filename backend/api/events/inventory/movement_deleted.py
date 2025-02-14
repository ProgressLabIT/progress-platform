from events.inventory.base_inventory import BaseInventoryEvent
from utils.dt import timestamp

class MovementDeleted(BaseInventoryEvent):

  def apply(self):
    ...
