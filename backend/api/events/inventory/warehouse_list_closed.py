from events.inventory.base_inventory import BaseInventoryEvent
from utils.dt import timestamp
from models.inventory import *
from events.inventory.base_inventory import BaseInventoryEvent, BaseInventoryModel
from models.event import EventInfoModel, EventType

class WarehouseListClosed(BaseInventoryEvent):

  class InfoModel(EventInfoModel):
    movement_list_key: str

  @classmethod
  def get_event_type(cls):
    return EventType.WAREHOUSE_LIST_CLOSED

  @classmethod
  def get_tx_collections(cls):
    return ['MovementList', 'movement']


  def apply(self):
    self.tx.collection('MovementList').update(dict(
      _key = self.info.movement_list_key,
      status = MovementStatus.COMPLETED,
      end = self.info.timestamp
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
      movement_list_key=self.info.movement_list_key,
      timestamp=self.info.timestamp
    ))
