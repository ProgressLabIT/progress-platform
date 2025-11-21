from events.base_event import BaseEvent
from models.event import EventInfoModel, EventType
from models.inventory.counting import InventoryCountRecord, InventoryCountStatus


class CountCanceledEvent(BaseEvent):
  class InfoModel(EventInfoModel):
    count_key: str
    inventory_keys: list[str]

  @classmethod
  def get_event_type(cls):
    return EventType.COUNT_CANCELED

  @classmethod
  def get_tx_collections(cls):
    return ['is_in_position', 'inventory_count_record']

  def apply(self):
    # Validate inputs
    if not self.info.inventory_keys or len(self.info.inventory_keys) == 0:
      raise ValueError("inventory_keys list is required and cannot be empty")

    # Get the count record to verify it exists and is cancellable
    count_record = self.tx.collection('inventory_count_record').get(self.info.count_key)

    if not count_record:
      raise ValueError(f"Count record with key {self.info.count_key} not found")

    # Only allow canceling if status is STARTED
    if count_record.get('status') != InventoryCountStatus.STARTED:
      raise ValueError(
        f"Cannot cancel count record {self.info.count_key} with status {count_record.get('status')}. "
        "Only STARTED counts can be canceled."
      )

    # Verify inventory keys match the count record's product/position
    # Get all inventory records to verify they match
    inventory_records = []
    for inventory_key in self.info.inventory_keys:
      inventory = self.tx.collection('is_in_position').get(inventory_key)
      if not inventory:
        raise ValueError(f"Inventory record with key {inventory_key} not found")

      # Verify the inventory matches the count record's product/position
      if inventory['_from'] != count_record['_from'] or inventory['_to'] != count_record['_to']:
        raise ValueError(
          f"Inventory record {inventory_key} does not match count record's product/position"
        )

      # Verify the inventory is locked by this count
      if not inventory.get('counting', False) or inventory.get('count_by') != self.info.user_key:
        raise ValueError(
          f"Inventory record {inventory_key} is not locked by count {self.info.count_key}"
        )

      inventory_records.append(inventory)

    # Delete the count record
    self.tx.collection('inventory_count_record').delete(self.info.count_key)

    # Unlock all inventory records
    self.tx.aql.execute(
      """
      FOR inventory IN is_in_position
      FILTER inventory._key IN @inventory_keys
      UPDATE inventory WITH { counting: false, count_by: null } IN is_in_position
      """,
      bind_vars=dict(inventory_keys=self.info.inventory_keys)
    )

    self.response = dict(
      message=f"Count record canceled and {len(inventory_records)} inventory records unlocked",
      count_record_key=self.info.count_key,
      inventory_keys_unlocked=self.info.inventory_keys
    )
