from enum import Enum

from models.base_models import ArangoDocument
from models.inventory.counting import *
from models.inventory.inventory import *
from models.inventory.movement import *
from models.inventory.position import *



class InventoryNotificationType(str, Enum):
  ERROR = 'ERROR'
  MOVEMENT_ADDED = 'MOVEMENT_ADDED'
  MOVEMENT_UPDATED = 'MOVEMENT_UPDATED'


class InventoryNotificationErrorCode(str, Enum):
  EXCEPTION = 'EXCEPTION'



class InventoryGlobalConfig(ArangoDocument):
  allow_placement_different_from_planned: bool = True
  allow_mission_closing_with_unstarted_movements: bool = False # started movements must be completed


class InventoryUsagePolicy(str, Enum):
  FIFO = 'fifo',
  LIFO = 'lifo',
  CLOSEST_TO_EXPIRATION = 'closest_to_expiration' # may be different than FIFO due to different expiration times since receipt
