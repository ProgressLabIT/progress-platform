from uuid import uuid4

from pydantic import Field

from events.base_event import BaseEvent
from models.event import EventInfoModel, EventType
from models.inventory.counting import InventoryCountRecord, InventoryCountStatus, InventoryCountSessionStatus
from models.inventory.inventory import Inventory
from utils.dt import timestamp



class CountStartedEvent(BaseEvent):
  class InfoModel(EventInfoModel):
    count_key: str = Field(default_factory=lambda: str(uuid4()))
    inventory_count_session_key: str
    assignment_key: str | None = None
    inventory_keys: list[str] | None = None # can be more if counting serials
    product_key: str | None = None # optional, for new inventory
    position_key: str | None = None # optional, for new inventory

  @classmethod
  def get_event_type(cls):
    return EventType.COUNT_STARTED

  @classmethod
  def get_tx_collections(cls):
    return ['is_in_position', 'inventory_count_record', 'Product', 'InventoryCountSession']

  def apply(self):
    # Validate session is in STARTED status (not completed/applied/canceled)
    session = self.tx.collection('InventoryCountSession').get(self.info.inventory_count_session_key)
    if session is None:
      raise ValueError(f"Count session {self.info.inventory_count_session_key} not found")

    session_status = session.get('status')
    if session_status != InventoryCountSessionStatus.STARTED.value:
      raise ValueError(
        f"Cannot start count: session is in '{session_status}' status. "
        f"Counting is only allowed when session is in 'started' status."
      )

    # Validate inputs
    has_inventory_keys = self.info.inventory_keys and len(self.info.inventory_keys) > 0
    has_product_position = self.info.product_key and self.info.position_key

    if not has_inventory_keys and not has_product_position:
      raise ValueError("Either inventory_keys must be provided, or both product_key and position_key must be provided")

    if has_inventory_keys:
      # Existing inventory flow
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
    else:
      # New inventory flow - no existing inventory records
      # Fetch product to check traceability
      product = self.tx.collection('Product').get(self.info.product_key)
      if not product:
        raise ValueError(f"Product with key {self.info.product_key} not found")

      # Skip inventory locking step (no inventory records to lock)

      # Prepare count record data for new inventory
      product_id = f'Product/{self.info.product_key}'
      position_id = f'Position/{self.info.position_key}'

      count_record = InventoryCountRecord(
        product_id=product_id,
        position_id=position_id,
        system_qt=0,
        system_serial_keys=[],
        system_at=timestamp(),
        user_key=self.info.user_key,
        inventory_count_session_key=self.info.inventory_count_session_key,
        assignment_key=self.info.assignment_key,
        status=InventoryCountStatus.STARTED
      )

    # Insert the count record
    count_record_key = self.tx.collection('inventory_count_record').insert(count_record.model_dump(by_alias=True))['_key']

    self.response = dict(
      message=f"Created count record and locked inventory" if has_inventory_keys else f"Created count record for new inventory",
      count_record_key=count_record_key
    )
