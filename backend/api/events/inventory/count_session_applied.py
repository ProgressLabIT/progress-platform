from events.base_event import BaseEvent
from models.event import EventInfoModel, EventType
from models.inventory.counting import InventoryCountSessionStatus
from models.inventory.movement import MovementListNewStatus


class CountSessionAppliedEvent(BaseEvent):
  """
  Phase 3: Finalize count session after async processing completes.

  This event:
  1. Validates session is in PROCESSING status
  2. Unlocks all positions that were locked
  3. Counts movements created and failed records
  4. Updates MovementList status to COMPLETED
  5. Updates session status to APPLIED with stats
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
      'MovementList',
      'movement',
      'is_in_position',
    ]

  def apply(self):
    # 1. Validate session is in PROCESSING status
    self.session = self.tx.collection('InventoryCountSession').get(self.info.session_key)
    if self.session is None:
      raise ValueError(f"Session {self.info.session_key} not found")

    if self.session.get('status') != InventoryCountSessionStatus.PROCESSING.value:
      raise ValueError(f"Session must be in 'processing' status to finalize")

    # 2. Unlock positions
    self._unlock_positions()

    # 3. Count results
    movements_created, movements_failed = self._count_results()

    # 4. Update MovementList to COMPLETED
    list_key = self.session.get('adjustment_list_key')
    if list_key:
      self.tx.collection('MovementList').update({
        '_key': list_key,
        'status': MovementListNewStatus.COMPLETED.value,
        'end': self.info.timestamp
      })

    # 5. Update session to APPLIED
    self.tx.collection('InventoryCountSession').update({
      '_key': self.info.session_key,
      'status': InventoryCountSessionStatus.APPLIED.value,
      'movements_created': movements_created,
      'movements_failed': movements_failed,
      'processing_completed': self.info.timestamp
    })

    self.response = dict(
      movements_created=movements_created,
      movements_failed=movements_failed
    )

  def _unlock_positions(self):
    """Unlock all positions locked by this session."""
    query = """
      FOR inv IN is_in_position
      FILTER inv.locked == true AND inv.locked_by == @session_key
      UPDATE inv WITH { locked: false, locked_by: null } IN is_in_position
    """
    self.tx.aql.execute(query, bind_vars={'session_key': self.info.session_key})

  def _count_results(self):
    """Count successful and failed record applications."""
    query = """
      LET applied = (
        FOR r IN inventory_count_record
        FILTER r.inventory_count_session_key == @session_key
          AND r.processed == true
          AND LENGTH(r.movement_keys || []) > 0
        COLLECT WITH COUNT INTO c
        RETURN c
      )[0]

      LET failed = (
        FOR r IN inventory_count_record
        FILTER r.inventory_count_session_key == @session_key
          AND r.error_details != null
        COLLECT WITH COUNT INTO c
        RETURN c
      )[0]

      RETURN { applied, failed }
    """
    result = list(self.tx.aql.execute(query, bind_vars={'session_key': self.info.session_key}))[0]
    return result['applied'] or 0, result['failed'] or 0
