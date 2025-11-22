from events.base_event import BaseEvent
from models.event import EventInfoModel, EventType
from models.inventory.counting import InventoryCountRecord, InventoryCountStatus


class CountCompletedEvent(BaseEvent):
  class InfoModel(EventInfoModel):
    count_key: str
    count_qt: float
    count_serial_keys: list[str] | None = None
    notes: str | None = None

  @classmethod
  def get_event_type(cls):
    return EventType.COUNT_COMPLETED

  @classmethod
  def get_tx_collections(cls):
    return ['inventory_count_record', 'is_in_position']

  def apply(self):
    # Get the count record to verify it exists and is completable
    count_record = InventoryCountRecord(**self.tx.collection('inventory_count_record').get(self.info.count_key))

    if not count_record:
      raise ValueError(f"Count record with key {self.info.count_key} not found")

    # Only allow completing if status is STARTED
    if count_record.status != InventoryCountStatus.STARTED:
      raise ValueError(f"Cannot complete count record {self.info.count_key} with status {count_record.status}. Only STARTED counts can be completed.")

    # Update the count record
    update = dict(
      _key=self.info.count_key,
      counted_qt=self.info.count_qt,
      counted_serial_keys=self.info.count_serial_keys,
      status=InventoryCountStatus.COMPLETED,
      counted_at=self.info.timestamp,
      notes=self.info.notes
    )
    self.tx.collection('inventory_count_record').update(update)

    # Unlock all inventory records
    self.tx.aql.execute(
      """
      FOR i IN is_in_position
      FILTER i._from == @product_id AND i._to == @position_id
      UPDATE i WITH { counting: false, last_counted: @timestamp } IN is_in_position
      """,
      bind_vars=dict(
        product_id=count_record.product_id,
        position_id=count_record.position_id,
        timestamp=self.info.timestamp
      )
    )

    self.response = dict(
      message=f"Count record completed",
      count_record_key=count_record.key
    )

    # Unlock all inventory records
