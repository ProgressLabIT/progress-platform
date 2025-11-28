from events.base_event import BaseEvent
from models.event import EventInfoModel, EventType
from models.inventory.counting import InventoryCountRecord, InventoryCountStatus


class CountDiscardedEvent(BaseEvent):
  class InfoModel(EventInfoModel):
    count_key: str

  @classmethod
  def get_event_type(cls):
    return EventType.COUNT_DISCARDED

  @classmethod
  def get_tx_collections(cls):
    return ['inventory_count_record']

  def apply(self):
    # Get the count record to verify it exists and is discardable
    count_record = InventoryCountRecord(**self.tx.collection('inventory_count_record').get(self.info.count_key))

    if not count_record:
      raise ValueError(f"Count record with key {self.info.count_key} not found")

    # Only allow discarding if status is COMPLETED or SUBMITTED
    if count_record.status != InventoryCountStatus.COMPLETED:
      raise ValueError(
        f"Cannot discard count record {self.info.count_key} with status {count_record.status}. "
        f"Only completed counts can be discarded."
      )

    # Update the count record status to DISCARDED
    update = dict(
      _key=self.info.count_key,
      status=InventoryCountStatus.DISCARDED,
      reviewed_at=self.info.timestamp
    )
    self.tx.collection('inventory_count_record').update(update)

    self.response = dict(
      message=f"Count record discarded",
      count_record_key=count_record.key
    )

