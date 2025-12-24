from events.base_event import BaseEvent
from events.inventory.count_discarded import CountDiscardedEvent
from models.event import EventInfoModel, EventType
from models.inventory.counting import InventoryCountRecord, InventoryCountStatus
from utils.inventory import Queries

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
    return ['inventory_count_record', 'is_in_position', 'inventory_count_position_complete']


  # ========================================================
  # MAIN LOGIC
  # ========================================================

  def apply(self):

    self._fetch_and_validate_count_record()
    self._update_count_record()
    self._discard_previous_counts_by_same_user()
    self._unlock_inventory_records()
    self._flag_position_as_counted_if_count_complete()

    self.response = dict(
      message=f"Count record completed",
      count_record_key=self.count_record.key
    )


  # ========================================================
  # PRIVATE METHODS
  # ========================================================

  def _fetch_and_validate_count_record(self):
    # Get the count record to verify it exists and is completable
    self.count_record = InventoryCountRecord(**self.tx.collection('inventory_count_record').get(self.info.count_key))

    if not self.count_record:
      raise ValueError(f"Count record with key {self.info.count_key} not found")

    # Only allow completing if status is STARTED
    if self.count_record.status != InventoryCountStatus.STARTED:
      raise ValueError(f"Cannot complete count record {self.info.count_key} with status {self.count_record.status}. Only STARTED counts can be completed.")


  # ========================================================

  def _update_count_record(self):
    update = dict(
      _key=self.info.count_key,
      counted_qt=self.info.count_qt,
      counted_serial_keys=self.info.count_serial_keys,
      status=InventoryCountStatus.COMPLETED,
      counted_at=self.info.timestamp,
      notes=self.info.notes
    )
    self.tx.collection('inventory_count_record').update(update)


  # ========================================================

  def _discard_previous_counts_by_same_user(self):
    # Find previous counts by the same user for the same product/position/session
    previous_counts = self.tx.aql.execute(
      """
      FOR r IN inventory_count_record
      FILTER r._from == @product_id
         AND r._to == @position_id
         AND r.inventory_count_session_key == @session_key
         AND r.user_key == @user_key
         AND r.status IN ['completed', 'submitted', 'confirmed']
         AND r._key != @current_key
      RETURN r._key
      """,
      bind_vars=dict(
        product_id=self.count_record.product_id,
        position_id=self.count_record.position_id,
        session_key=self.count_record.inventory_count_session_key,
        user_key=self.count_record.user_key,
        current_key=self.info.count_key
      )
    )

    for record_key in previous_counts:
      CountDiscardedEvent.create_as_child(self, dict(count_key=record_key))


  # ========================================================

  def _unlock_inventory_records(self):
    # Unlock all inventory records
    self.tx.aql.execute(
      """
      FOR i IN is_in_position
      FILTER i._from == @product_id AND i._to == @position_id
      UPDATE i WITH { counting: false, last_counted: @timestamp } IN is_in_position
      """,
      bind_vars=dict(
        product_id=self.count_record.product_id,
        position_id=self.count_record.position_id,
        timestamp=self.info.timestamp
      )
    )

  # ========================================================

  def _flag_position_as_counted_if_count_complete(self):
    current_position_key = self.count_record.position_id.split('/')[-1]

    # Get the path keys from the root to the current position
    path_keys = list(self.tx.aql.execute(
      Queries.GET_POSITION_PATH,
      bind_vars=dict(position_key=current_position_key)
    ))

    for key in reversed(path_keys): # Start from the current position and work up to the root
      result = self.tx.aql.execute(Queries.CHECK_POSITION_COMPLETION, bind_vars=dict(
        session_key=self.count_record.inventory_count_session_key,
        position_key=key
      )).next()

      if result:
        # Do not indicate user since it's the system that flagged the position as counted
        self.tx.collection('inventory_count_position_complete').insert(dict(
          _from=f'InventoryCountSession/{self.count_record.inventory_count_session_key}',
          _to=f'Position/{key}',
          status='counted',
          completed_at=self.info.timestamp,
          notes="Last position item checked"
        ))

      else:
        break # Stop checking parent positions if current position is not complete
