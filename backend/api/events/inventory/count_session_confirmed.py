from events.base_event import BaseEvent
from models.event import EventInfoModel, EventType
from models.inventory.counting import InventoryCountSessionStatus, InventoryCountStatus
from models.inventory.movement import (
  InventoryMovementType,
  MovementListNewStatus,
)
from utils.counter import _generate_counter


class CountSessionConfirmedEvent(BaseEvent):
  """
  Initiates async count session application process.

  This event:
  1. Validates session is in COMPLETED status
  2. Checks for unresolved conflicts
  3. Creates an EMPTY MovementList (status=PLANNED)
  4. Transitions count records: completed/submitted → confirmed
  5. Updates session status to PROCESSING
  6. Triggers async workflow to process records
  """

  class InfoModel(EventInfoModel):
    session_key: str

  @classmethod
  def get_event_type(cls):
    return EventType.COUNT_SESSION_CONFIRMED

  @classmethod
  def get_tx_collections(cls):
    return [
      'InventoryCountSession',
      'inventory_count_record',
      'Counter',
      'Config',
      'MovementList',
      'is_in_position',
    ]

  def apply(self):
    # 1. Validate session
    self._fetch_and_validate_session()

    # 2. Check for unresolved conflicts (reuse logic from current implementation)
    self._check_for_conflicts()

    # 3. Count records that will be confirmed
    confirmed_count = self._count_confirmable_records()

    if confirmed_count == 0:
      # No records to process - transition directly to APPLIED
      self._update_session_status_no_adjustments()
      self.response = dict(
        message=f"Count session {self.info.session_key} has no adjustments to apply",
        session_key=self.info.session_key,
        adjustment_list_key=None,
        records_to_process=0
      )
      return

    # 4. Create EMPTY movement list
    list_key = self._create_empty_movement_list()

    # 5. Transition count records to CONFIRMED status
    self._confirm_count_records()

    # 6. Lock positions
    self._lock_positions()

    # 7. Update session to PROCESSING status
    self._update_session_to_processing(list_key, confirmed_count)

    # 8. Store workflow trigger data in response and record count for post_processing
    self._records_to_process = confirmed_count
    self.response = dict(
      message=f"Count session {self.info.session_key} confirmed - async processing initiated",
      session_key=self.info.session_key,
      adjustment_list_key=list_key,
      records_to_process=confirmed_count,
      trigger_workflow=True  # Signal to endpoint to trigger workflow
    )

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
    """Check for unresolved conflicts (copy from CountSessionAppliedEvent)."""
    conflict_query = """
      FOR r IN inventory_count_record
      FILTER r.inventory_count_session_key == @session_key
        AND r.status IN ['completed', 'submitted']
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
        for c in conflicts[:5]
      ])
      more_msg = f" and {len(conflicts) - 5} more" if len(conflicts) > 5 else ""
      raise ValueError(
        f"Cannot apply session: {len(conflicts)} unresolved conflict(s) found. "
        f"Conflicts: {conflict_details}{more_msg}. "
        f"Please resolve all conflicts before applying adjustments."
      )

  def _count_confirmable_records(self):
    """Count records that need confirmation and have delta != 0."""
    query = """
      FOR r IN inventory_count_record
      FILTER r.inventory_count_session_key == @session_key
        AND r.status IN ['completed', 'submitted']
      COLLECT product_id = r._from, position_id = r._to
      INTO records
      LET winning_record = FIRST(
        FOR rec IN records[*].r
        SORT rec.counted_at DESC
        LIMIT 1
        RETURN rec
      )
      LET delta = winning_record.counted_qt - winning_record.system_qt
      FILTER delta != 0
      COLLECT WITH COUNT INTO total
      RETURN total
    """
    result = list(self.tx.aql.execute(
      query,
      bind_vars={'session_key': self.info.session_key}
    ))
    return result[0] if result else 0

  def _create_empty_movement_list(self) -> str:
    """Create an empty MovementList to be populated asynchronously."""
    # Generate list code using counter
    try:
      counter_key = self.tx.collection('Config').get('system_counters').get('movement_lists', 'default')
      list_code = _generate_counter(self.tx, counter_key)
    except Exception:
      session_code = self.session.get('code', self.info.session_key)
      list_code = f"ADJ-{session_code}"

    # Create EMPTY list
    list_record = dict(
      code=list_code,
      type=InventoryMovementType.ADJUSTMENT.value,
      status=MovementListNewStatus.PLANNED.value,
      notes=f"Adjustments from count session {self.session.get('code', self.info.session_key)}",
      references=dict(inventory_count_session_key=self.info.session_key),
      created=self.info.timestamp,
      start=self.info.timestamp,
    )

    return self.tx.collection('MovementList').insert(list_record)['_key']

  def _confirm_count_records(self):
    """Transition count records from completed/submitted to confirmed."""
    query = """
      FOR r IN inventory_count_record
      FILTER r.inventory_count_session_key == @session_key
        AND r.status IN ['completed', 'submitted']
      UPDATE r WITH {
        status: 'confirmed',
        reviewed_at: @timestamp
      } IN inventory_count_record
    """
    self.tx.aql.execute(
      query,
      bind_vars={
        'session_key': self.info.session_key,
        'timestamp': self.info.timestamp
      }
    )

  def _lock_positions(self):
    """Lock all positions involved in this count session."""
    query = """
      FOR r IN inventory_count_record
      FILTER r.inventory_count_session_key == @session_key
        AND r.status == 'confirmed'
      FOR inv IN is_in_position
      FILTER inv._to == r._to AND inv._from == r._from
      UPDATE inv WITH { locked: true, locked_by: @session_key } IN is_in_position
    """
    self.tx.aql.execute(query, bind_vars={'session_key': self.info.session_key})

  def _update_session_to_processing(self, list_key: str, record_count: int):
    """Update session to PROCESSING status."""
    self.tx.collection('InventoryCountSession').update(dict(
      _key=self.info.session_key,
      status=InventoryCountSessionStatus.PROCESSING.value,
      adjustment_list_key=list_key,
      movements_processed_count=0,
      processing_started=self.info.timestamp,
    ))

  def _update_session_status_no_adjustments(self):
    """Update session directly to APPLIED when no adjustments needed."""
    self.tx.collection('InventoryCountSession').update(dict(
      _key=self.info.session_key,
      status=InventoryCountSessionStatus.APPLIED.value,
      adjustment_list_key=None,
      movements_created=0,
      movements_failed=0,
    ))

  def post_processing(self):
    """Trigger Prefect workflow after transaction commits."""
    if hasattr(self, '_records_to_process') and self._records_to_process > 0:
      self._trigger_prefect_workflow()

  def _trigger_prefect_workflow(self):
    """Trigger Prefect workflow via HTTP API."""
    import httpx
    import os

    prefect_url = os.getenv('PREFECT_API_URL', 'http://wf-server:4200/api')

    try:
      # 1. Find deployment by name
      filter_resp = httpx.post(
        f"{prefect_url}/deployments/filter",
        json={"deployments": {"name": {"like_": "apply_inventory_counts"}}, "limit": 1},
        timeout=10.0
      )
      filter_resp.raise_for_status()
      deployments = filter_resp.json()

      if not deployments:
        raise ValueError("Deployment 'Apply Inventory Counts/main' not found")

      deployment_id = deployments[0]['id']

      # 2. Create flow run
      run_resp = httpx.post(
        f"{prefect_url}/deployments/{deployment_id}/create_flow_run",
        json={
          "state": {"type": "SCHEDULED"},
          "parameters": {"session_key": self.info.session_key}
        },
        timeout=10.0
      )
      run_resp.raise_for_status()

    except Exception as e:
      # If workflow trigger fails, the transaction has already committed
      # Log the error but don't raise - this needs manual intervention
      print(f"ERROR: Failed to trigger Prefect workflow for session {self.info.session_key}: {e}")
      raise
