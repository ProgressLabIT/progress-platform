from events.inventory.base_inventory import BaseInventory
from utils.dt import timestamp
from models.inventory import *
from events.inventory.base_inventory import BaseInventory, BaseInventoryModel
from models.event import EventType
from models.event import EventModel

class WarehouseListClosedModel(BaseInventoryModel):
    event_type: str = EventType.WAREHOUSE_LIST_CLOSED.name

class WarehouseListClosed(BaseInventory):
  event_data: WarehouseListClosedModel

  def set_model(self, base_model: EventModel):
    self.event_data = WarehouseListClosedModel(**base_model.model_dump())

  def apply(self):
    self.tx.collection('MovementList').update(dict(
      _key = self.event_data.movement_list_key,
      status = MovementStatus.COMPLETED,
      end = self.event_data.timestamp
    ))
    # Update all movements in the list
    self.tx.aql.execute("""
      FOR m IN movement
        FILTER
          m.movement_list_key == @movement_list_key
          AND m.status != "completed"
        UPDATE m WITH {
          status: m.qt_confirmed == 0 ? "canceled" : "completed",
          start: m.qt_confirmed == 0 ? null : @timestamp,
          end: m.qt_confirmed == 0 ? null : @timestamp
        } IN movement
    """, bind_vars=dict(
      movement_list_key=self.event_data.movement_list_key,
      timestamp=self.event_data.timestamp
    ))
