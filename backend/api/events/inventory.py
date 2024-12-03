from events.base import BaseEvent
from events.shared import EventMeta
from managers.inventoy_event_manager import InventoryEventManager
from models.inventory import InventoryCommandType

class InventoryEvent(BaseEvent):
  inventory_collections = ['InventoryMovement', 'is_in_position']

  ADD_MOVEMENT = EventMeta(
    collections=inventory_collections,
    action="add_movement"
  )

  UPDATE_MOVEMENT = EventMeta(
    collections=inventory_collections,
    action="update_movement"
  )

  DELETE_MOVEMENT = EventMeta(
    collections=inventory_collections,
    action="delete_movement"
  )


  #===============================================================

  def add_movement(self):
    InventoryEventManager.getInstance().handle_event(self, InventoryCommandType.ADD_MOVEMENT)

  def update_movement(self):
    InventoryEventManager.getInstance().handle_event(self, InventoryCommandType.UPDATE_MOVEMENT)

  def delete_movement(self):
    InventoryEventManager.getInstance().handle_event(self, InventoryCommandType.DELETE_MOVEMENT)
