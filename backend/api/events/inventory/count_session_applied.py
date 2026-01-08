from events.base_event import BaseEvent
from events.inventory.warehouse_list_created import WarehouseListCreatedEvent
from models.event import EventInfoModel, EventType
from models.inventory.counting import InventoryCountSessionStatus
from models.inventory.movement import (
  InventoryMovementType,
  InventoryMovementReferences,
  InventoryMovementNew,
  MovementListNew,
  MovementListNewStatus,
)
from utils.counter import _generate_counter


class CountSessionAppliedEvent(BaseEvent):
  """
  Applies count session adjustments by generating adjustment movements.

  This event:
  1. Validates the session is in COMPLETED status
  2. Checks for unresolved conflicts (multiple records with different counted_qt for same product/position)
  3. Creates a MovementList of type ADJUSTMENT
  4. Generates individual adjustment movements for each count record with delta != 0
  5. Updates the session status to APPLIED and stores the adjustment_list_key

  For serialized products, individual movements are created for each added/removed serial.
  For non-serialized products, a single movement is created with the delta quantity.
  """

  class InfoModel(EventInfoModel):
    session_key: str

  @classmethod
  def get_event_type(cls):
    return EventType.COUNT_SESSION_APPLIED

  @classmethod
  def get_tx_collections(cls):
    return [
      'InventoryCountSession',
      'inventory_count_record',
      'Counter',
      'Config',
      'Product',
      # Collections used by WarehouseListCreatedEvent:
      'MovementList',
      'movement',
      'Serial',
      'is_in_position',
    ]

  # ========================================================
  # MAIN APPLY METHOD
  # ========================================================

  def apply(self):
    # 1. Validate session
    self._fetch_and_validate_session()

    # 2. Check for unresolved conflicts
    self._check_for_conflicts()

    # 3. Fetch adjustable records
    adjustable_records = self._fetch_adjustable_records()

    if len(adjustable_records) == 0:
      # No adjustments needed - just update session status
      self._update_session_status(adjustment_list_key=None)
      self.response = dict(
        message=f"Count session {self.info.session_key} applied successfully (no adjustments needed)",
        session_key=self.info.session_key,
        adjustment_list_key=None,
        adjustments_count=0
      )
      return

    # 4. Build adjustment movements
    movements = self._build_adjustment_movements(adjustable_records)

    # 5. Create movement list via WarehouseListCreatedEvent
    list_key = self._create_warehouse_list(movements)

    # 6. Update session status
    self._update_session_status(adjustment_list_key=list_key)

    self.response = dict(
      message=f"Count session {self.info.session_key} applied successfully",
      session_key=self.info.session_key,
      adjustment_list_key=list_key,
      adjustments_count=len(movements)
    )

  # ========================================================
  # PRIVATE METHODS
  # ========================================================

  def _fetch_and_validate_session(self):
    """Fetch session and validate it's in COMPLETED status."""
    self.session = self.tx.collection('InventoryCountSession').get(self.info.session_key)
    if self.session is None:
      raise ValueError(f"Session {self.info.session_key} not found")

    current_status = self.session.get('status')
    if current_status != InventoryCountSessionStatus.COMPLETED.value:
      raise ValueError(
        f"Session must be in 'completed' status to apply adjustments. "
        f"Current status: {current_status}"
      )

  def _check_for_conflicts(self):
    """
    Check for unresolved conflicts: multiple non-discarded records for the same
    product/position with different counted quantities.
    """
    conflict_query = """
      FOR r IN inventory_count_record
      FILTER r.inventory_count_session_key == @session_key
        AND r.status IN ['completed', 'submitted', 'confirmed']
      COLLECT product_id = r._from, position_id = r._to
      INTO records
      LET counted_values = UNIQUE(records[*].r.counted_qt)
      FILTER LENGTH(records) > 1 AND LENGTH(counted_values) > 1
      RETURN {
        product_id: product_id,
        position_id: position_id,
        conflict_count: LENGTH(records),
        counted_values: counted_values
      }
    """
    conflicts = list(self.tx.aql.execute(
      conflict_query,
      bind_vars={'session_key': self.info.session_key}
    ))

    if len(conflicts) > 0:
      conflict_details = ', '.join([
        f"{c['product_id']}/{c['position_id']} ({c['conflict_count']} records)"
        for c in conflicts[:5]  # Show max 5 conflicts
      ])
      more_msg = f" and {len(conflicts) - 5} more" if len(conflicts) > 5 else ""
      raise ValueError(
        f"Cannot apply session: {len(conflicts)} unresolved conflict(s) found. "
        f"Conflicts: {conflict_details}{more_msg}. "
        f"Please resolve all conflicts before applying adjustments."
      )

  def _fetch_adjustable_records(self):
    """
    Fetch count records that need adjustments (delta != 0).
    For each product/position pair with multiple records, use the most recent one.
    """
    # First, get the winning record for each product/position pair
    # (most recent non-discarded record)
    query = """
      FOR r IN inventory_count_record
      FILTER r.inventory_count_session_key == @session_key
        AND r.status IN ['completed', 'submitted', 'confirmed']
      COLLECT product_id = r._from, position_id = r._to
      INTO records
      LET sorted_records = (
        FOR rec IN records[*].r
        SORT rec.counted_at DESC
        LIMIT 1
        RETURN rec
      )
      LET winning_record = FIRST(sorted_records)
      LET delta = winning_record.counted_qt - winning_record.system_qt
      FILTER delta != 0
      LET product = DOCUMENT(winning_record._from)
      RETURN MERGE(winning_record, {
        delta: delta,
        product_key: PARSE_IDENTIFIER(winning_record._from).key,
        position_key: PARSE_IDENTIFIER(winning_record._to).key,
        traceability_level: product.traceability_level
      })
    """
    return list(self.tx.aql.execute(
      query,
      bind_vars={'session_key': self.info.session_key}
    ))

  def _build_adjustment_movements(self, records) -> list[InventoryMovementNew]:
    """
    Build adjustment movements for all records.
    Returns a list of InventoryMovementNew objects.
    """
    movements = []
    movement_item = 1

    for record in records:
      is_serialized = record.get('traceability_level', False)

      if is_serialized:
        # Serialized product: create individual movements for each serial
        serial_movements = self._build_serial_adjustments(record, movement_item)
        movements.extend(serial_movements)
      else:
        # Non-serialized product: create single movement with delta
        movements.append(self._build_quantity_adjustment(record, movement_item))

      movement_item += 1

    return movements

  def _build_quantity_adjustment(self, record, movement_item) -> InventoryMovementNew:
    """Build a single adjustment movement for a non-serialized product."""
    return InventoryMovementNew(
      movement_type=InventoryMovementType.ADJUSTMENT,
      product_key=record['product_key'],
      position_to=record['position_key'],
      qt_planned=record['delta'],
      qt_confirmed=record['delta'],
      movement_list_item=movement_item,
      references=InventoryMovementReferences(
        inventory_count_session_key=self.info.session_key
      ),
      reason=f"Stock count adjustment (delta: {record['delta']})"
    )

  def _build_serial_adjustments(self, record, movement_item) -> list[InventoryMovementNew]:
    """
    Build adjustment movements for a serialized product.
    Returns a list of InventoryMovementNew objects.
    """
    system_serials = set(record.get('system_serial_keys') or [])
    counted_serials = set(record.get('counted_serial_keys') or [])

    added_serials = counted_serials - system_serials
    removed_serials = system_serials - counted_serials

    movements = []

    # Create +1 adjustments for added serials
    for serial_key in added_serials:
      movements.append(InventoryMovementNew(
        movement_type=InventoryMovementType.ADJUSTMENT,
        product_key=record['product_key'],
        position_to=record['position_key'],
        serial_key=serial_key,
        qt_planned=1,
        qt_confirmed=1,
        movement_list_item=movement_item,
        references=InventoryMovementReferences(
          inventory_count_session_key=self.info.session_key
        ),
        reason="Stock count adjustment (serial found)"
      ))

    # Create -1 adjustments for removed serials
    for serial_key in removed_serials:
      movements.append(InventoryMovementNew(
        movement_type=InventoryMovementType.ADJUSTMENT,
        product_key=record['product_key'],
        position_to=record['position_key'],
        serial_key=serial_key,
        qt_planned=-1,
        qt_confirmed=-1,
        movement_list_item=movement_item,
        references=InventoryMovementReferences(
          inventory_count_session_key=self.info.session_key
        ),
        reason="Stock count adjustment (serial missing)"
      ))

    return movements

  def _create_warehouse_list(self, movements: list[InventoryMovementNew]) -> str:
    """Create the adjustment MovementList via WarehouseListCreatedEvent."""
    # Generate list code using counter
    try:
      counter_key = self.tx.collection('Config').get('system_counters').get('movement_lists', 'default')
      list_code = _generate_counter(self.tx, counter_key)
    except Exception:
      # Fallback to session-based code if counter not configured
      session_code = self.session.get('code', self.info.session_key)
      list_code = f"ADJ-{session_code}"

    movement_list = MovementListNew(
      code=list_code,
      type=InventoryMovementType.ADJUSTMENT,
      status=MovementListNewStatus.COMPLETED,
      notes=f"Adjustments from count session {self.session.get('code', self.info.session_key)}",
      references=InventoryMovementReferences(
        inventory_count_session_key=self.info.session_key
      ),
      created=self.info.timestamp,
      start=self.info.timestamp,
      end=self.info.timestamp,
      movements=movements,
    )

    # WarehouseListCreatedEvent.create_as_child returns the list key directly
    return WarehouseListCreatedEvent.create_as_child(self, dict(
      new_movement_list=movement_list
    ))

  def _update_session_status(self, adjustment_list_key):
    """Update session status to APPLIED and store the adjustment list key."""
    self.tx.collection('InventoryCountSession').update(dict(
      _key=self.info.session_key,
      status=InventoryCountSessionStatus.APPLIED,
      adjustment_list_key=adjustment_list_key
    ))

