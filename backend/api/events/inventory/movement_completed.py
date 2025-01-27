from events.inventory.base_inventory import BaseInventory
from utils.dt import timestamp

class MovementCompleted(BaseInventory):

  def apply(self):
    ...
