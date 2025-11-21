from uuid import uuid4

from pydantic import Field

from events.base_event import BaseEvent
from models.event import EventInfoModel, EventType
from models.inventory.counting import InventoryCountRecord, InventoryCountStatus
from models.inventory.inventory import Inventory
from utils.dt import timestamp



class CountStartedEvent(BaseEvent):
  class InfoModel(EventInfoModel):
    count_key: str = Field(default_factory=lambda: str(uuid4()))
    inventory_count_session_key: str
    assignment_key: str | None = None
    inventory_keys: list[str] | None = None # can be more if counting serials

  @classmethod
  def get_event_type(cls):
    return EventType.COUNT_STARTED

  @classmethod
  def get_tx_collections(cls):
    return ['is_in_position', 'inventory_count_record']

  def apply(self):
    # Validate inputs
    if not self.info.inventory_keys or len(self.info.inventory_keys) == 0:
      raise ValueError("inventory_keys list is required and cannot be empty")

    # Lock inventory records while checking they all exists
    inventory_cursor = self.tx.aql.execute(
      """
      FOR inventory IN is_in_position
      FILTER inventory._key IN @inventory_keys
      SORT inventory._from, inventory._to
      UPDATE inventory WITH { counting: true, count_by: @user_key } IN is_in_position
      RETURN OLD
      """,
      bind_vars=dict(
        inventory_keys=self.info.inventory_keys,
        user_key=self.info.user_key
      )
    )
    inventory_records = [Inventory(**record) for record in inventory_cursor]

    # Ensure all records are for the same product/position pair

    product_id = inventory_records[0].product_id
    position_id = inventory_records[0].position_id

    for inventory in inventory_records:
      if inventory.counting:
        raise ValueError(f"Inventory record {inventory.key} is already being counted")

      if inventory.product_id != product_id or inventory.position_id != position_id:
        raise ValueError("All inventory records must be for the same product/position pair")

    # Prepare count record data
    count_record = InventoryCountRecord(
      product_id=product_id,
      position_id=position_id,
      system_qt=sum(i.quantity for i in inventory_records),
      system_serial_keys=[i.serial_key for i in inventory_records if i.serial_key is not None],
      system_at=timestamp(),
      user_key=self.info.user_key,
      inventory_count_session_key=self.info.inventory_count_session_key,
      assignment_key=self.info.assignment_key,
      status=InventoryCountStatus.STARTED
    )

    # Insert the count record
    count_record_key = self.tx.collection('inventory_count_record').insert(count_record.model_dump(by_alias=True))['_key']

    self.response = dict(
      message=f"Created count record and locked inventory",
      count_record_key=count_record_key
    )
