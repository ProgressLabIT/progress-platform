from events.base_event import BaseEvent
from events.inventory.movement_completed import MovementCompletedEvent
from models.event import EventInfoModel, EventType
from models.inventory.movement import InventoryMovementType


class CountAppliedEvent(BaseEvent):
  """
  Applies a single count record by creating adjustment movement(s).

  This event:
  1. Fetches the count record and validates it hasn't been processed yet
  2. Calculates delta and determines if serialized
  3. Creates adjustment movements via MovementCompletedEvent (if delta != 0)
  4. Marks count record as processed
  5. On error: stores error in count record and continues
  """

  class InfoModel(EventInfoModel):
    count_record_key: str
    movement_list_key: str
    inventory_count_session_key: str

  @classmethod
  def get_event_type(cls):
    return EventType.COUNT_APPLIED

  @classmethod
  def get_tx_collections(cls):
    return [
      'inventory_count_record',
      'Product',
      'MovementList',
      'movement',
      'Serial',
      'is_in_position',
    ]

  # ========================================================
  # HELPER METHODS
  # ========================================================

  def _fetch_count_record(self):
    """Fetch count record and validate it hasn't been processed yet."""
    self.record = self.tx.collection('inventory_count_record').get(self.info.count_record_key)
    if self.record is None:
      raise ValueError(f"Count record {self.info.count_record_key} not found")

    if self.record.get('processed', False):
      raise ValueError(f"Count record has already been processed")

    # Calculate delta
    self.delta = self.record['counted_qt'] - self.record['system_qt']
    self.product_key = self.record['_from'].split('/')[-1]
    self.position_key = self.record['_to'].split('/')[-1]

    return self.record


  # ========================================================

  def _unlock_inventory_records(self):
    """Unlock inventory records."""
    self.tx.collection('is_in_position').update_match(dict(
      _from=self.record['_from'],
      _to=self.record['_to'],
    ), dict(
      locked=False,
      locked_by=None
    ))

  # ========================================================

  def _create_quantity_adjustment(self):
    """Create single adjustment movement for non-serialized product."""

    movement =MovementCompletedEvent.create_as_child(self, dict(
      movement_type=InventoryMovementType.ADJUSTMENT,
      product_key=self.product_key,
      position_from=self.position_key,
      position_to=self.position_key,
      qt_planned=self.delta,
      qt_confirmed=self.delta,
      movement_list_key=self.info.movement_list_key,
      references=dict(
        inventory_count_session_key=self.info.inventory_count_session_key,
        inventory_count_record_key=self.info.count_record_key,
      ),
      reason=f"Stock count adjustment (delta: {self.delta})"
    ))

    self.movement_keys.append(movement.key)

  # ========================================================

  def _create_serial_adjustments(self) -> int:
    """Create individual movements for serialized product. Returns count of movements created."""
    system_serials = set(self.record.get('system_serial_keys') or [])
    counted_serials = set(self.record.get('counted_serial_keys') or [])

    added_serials = counted_serials - system_serials
    removed_serials = system_serials - counted_serials

    # Create +1 adjustments for added serials
    for serial_key in added_serials:
      movement = MovementCompletedEvent.create_as_child(self, dict(
        movement_type=InventoryMovementType.ADJUSTMENT,
        product_key=self.product_key,
        position_from=self.position_key,
        position_to=self.position_key,
        serial_key=serial_key,
        qt_planned=1,
        qt_confirmed=1,
        movement_list_key=self.info.movement_list_key,
        references=dict(
          inventory_count_session_key=self.info.inventory_count_session_key,
          inventory_count_record_key=self.info.count_record_key,
        ),
        reason="Stock count adjustment (serial found)"
      ))
      self.movement_keys.append(movement.key)

    # Create -1 adjustments for removed serials
    for serial_key in removed_serials:
      movement = MovementCompletedEvent.create_as_child(self, dict(
        movement_type=InventoryMovementType.ADJUSTMENT,
        product_key=self.product_key,
        position_from=self.position_key,
        position_to=self.position_key,
        serial_key=serial_key,
        qt_planned=-1,
        qt_confirmed=-1,
        movement_list_key=self.info.movement_list_key,
        references=dict(
          inventory_count_session_key=self.info.inventory_count_session_key,
          inventory_count_record_key=self.info.count_record_key,
        ),
        reason="Stock count adjustment (serial missing)"
      ))
      self.movement_keys.append(movement.key)


  # ========================================================

  def _mark_record_processed(self):
    """Mark count record as processed."""
    self.tx.collection('inventory_count_record').update(dict(
      _key=self.info.count_record_key,
      movement_keys=self.movement_keys,
      processed=True,
      error_details=None,  # Clear any previous errors
    ))


  # ========================================================
  # MAIN APPLY METHOD
  # ========================================================

  def apply(self):
    # Fetch and validate count record
    self._fetch_count_record()

    # Check if adjustment needed
    if self.delta == 0:
      # Mark as processed even for zero-delta
      self.tx.collection('inventory_count_record').update(dict(
        _key=self.info.count_record_key,
        processed=True,
        movement_keys=[],
      ))
      self.response = dict(
        record_key=self.info.count_record_key,
        movement_keys=[],
        success=True
      )
      return

    # Unlock inventory records
    self._unlock_inventory_records()

    # Fetch product to determine serialization
    product = self.tx.collection('Product').get(self.product_key)
    is_serialized = product.get('traceability_level', False)

    self.movement_keys = []
    # Create movements
    if is_serialized:
      self._create_serial_adjustments()
    else:
      self._create_quantity_adjustment()

    # Mark record as processed
    self._mark_record_processed()

    self.response = dict(
      record_key=self.info.count_record_key,
      movement_keys=self.movement_keys,
      success=True
    )
