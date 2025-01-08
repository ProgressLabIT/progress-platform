from fastapi import HTTPException

from events.base import BaseEvent
from events.shared import EventMeta
from managers.inventory_event_manager import InventoryEventManager
from models.inventory import *
from models.event import EventModel, InventoryEventModel

class InventoryEvent(BaseEvent):

  def __init__(self, event: InventoryEventModel, database=None, tx=None):
    super().__init__(database, tx)
    self.info = event
    self.define_action(event.event_type.value)

  def can_handle(self):
    return self.action != None

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


  #===============================================================

  def add_movement(self):
    InventoryEventManager.getInstance().handle_event(self, InventoryCommandType.ADD_MOVEMENT)

  def update_movement(self):
    InventoryEventManager.getInstance().handle_event(self, InventoryCommandType.UPDATE_MOVEMENT)

  def delete_movement(self):
    InventoryEventManager.getInstance().handle_event(self, InventoryCommandType.DELETE_MOVEMENT)

  # def create_list(self):
  #   """Must include data about all the related movements"""
  #   # Fetch product keys if by code
  #   new_list = self.info.movement_list

  #   # Create the movement list
  #   new_list_key = self.tx.collection('MovementList').insert(new_list)['_key']

  #   if new_list.by_code:
  #     product_codes = [m.product_code for m in new_list.movements]
  #     try:
  #       products_key_map = self.tx.aql.execute("""
  #         RETURN MERGE(
  #           FOR p IN Product
  #           FILTER p.code IN @codes
  #           RETURN {[p.code]: p._key}
  #         )""",
  #         bind_vars=dict(codes=product_codes)
  #       ).next()
  #     except StopIteration:
  #       raise HTTPException(status_code=404, detail="Could not find products with the codes provided")

  #     for movement in new_list.movements:
  #       product_key = products_key_map.get(movement.product_code, None)
  #       if product_key is None:
  #         raise HTTPException(status_code=404, detail=f"Could not find product with code {movement.product_code}")
  #       movement.product_key = product_key


  #   # Create the movements
  #   for m in new_list.movements:
  #     movement_info = InventoryMovementNew(
  #       type = new_list.type,
  #       serial_code = m.serial_code,
  #       serial_key = m.serial_key,
  #       quantity = m.quantity,
  #       product_key = m.product_key,
  #       status = MovementStatus.PLANNED,
  #       source = getattr(m, 'source', new_list.source),
  #       movement_list_key = new_list_key,
  #       extra = getattr(m, 'extra', new_list.extra)
  #     )
  #     event = Event(
  #       event_type = 'ADD_MOVEMENT',
  #       movement = movement_info,
  #       event_group = self.info.event_group
  #     )
  #     event.save()


  #   self.response = APIResponse(message="Movement list created successfully")
