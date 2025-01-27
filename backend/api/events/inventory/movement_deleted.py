from events.inventory.base_inventory import BaseInventory
from utils.dt import timestamp

class MovementDeleted(BaseInventory):

  def apply(self):
    ...
