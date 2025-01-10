from fastapi import HTTPException

from events.base import BaseEvent
from events.shared import EventMeta
from managers.inventory_event_manager import InventoryEventManager
from models.inventory import *

class InventoryEvent(BaseEvent):
  inventory_collections = ['movement', 'is_in_position']

  ADD_MOVEMENT = EventMeta(
    collections=inventory_collections + ['Serial'],
    action="add_movement"
  )

  MOVEMENT_UPDATED = EventMeta(
    collections=inventory_collections + ['Serial', 'MovementList'],
    action="update_movement"
  )

  DELETE_MOVEMENT = EventMeta(
    collections=inventory_collections,
    action="delete_movement"
  )

  # WAREHOUSE_LIST_CREATED = EventMeta(
  #   collections=inventory_collections + ['Serial', 'MovementList'],
  #   action="create_list"
  # )
  # Can't be implemented yet because it requires recursive events, which would create circular imports
  # (the Event class inherits from InventoryEvent). Needs refactoring according to #623

  WAREHOUSE_LIST_CLOSED = EventMeta(
    collections=['movement', 'MovementList'],
    action="close_list"
  )

  #===============================================================

  def add_movement(self):
    InventoryEventManager.getInstance().handle_event(self, InventoryCommandType.ADD_MOVEMENT)

  def update_movement(self):
    InventoryEventManager.getInstance().handle_event(self, InventoryCommandType.UPDATE_MOVEMENT)

  def delete_movement(self):
    InventoryEventManager.getInstance().handle_event(self, InventoryCommandType.DELETE_MOVEMENT)

  def close_list(self):
    InventoryEventManager.getInstance().handle_event(self, InventoryCommandType.CLOSE_LIST)
