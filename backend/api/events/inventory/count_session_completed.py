from events.base_event import BaseEvent
from models.event import EventInfoModel, EventType
from models.inventory.counting import InventoryCountSessionStatus


class CountSessionCompletedEvent(BaseEvent):
  """
  Transitions a count session from STARTED to COMPLETED status.
  COMPLETED means counting is finished and the session is ready for review/application.
  """

  class InfoModel(EventInfoModel):
    session_key: str

  @classmethod
  def get_event_type(cls):
    return EventType.COUNT_SESSION_COMPLETED

  @classmethod
  def get_tx_collections(cls):
    return ['InventoryCountSession', 'inventory_count_record']

  def _validate_can_complete(self):
    """
    Validates that the session can be completed.
    Raises ValueError if validation fails, otherwise returns the session document.
    """
    # Fetch and validate session exists
    session = self.tx.collection('InventoryCountSession').get(self.info.session_key)
    if session is None:
      raise ValueError(f"Session {self.info.session_key} not found")

    # Validate session status
    current_status = session.get('status')
    if current_status != InventoryCountSessionStatus.STARTED.value:
      raise ValueError(
        f"Session must be in 'started' status to complete. "
        f"Current status: {current_status}"
      )

    # Check for active counts (users currently counting)
    active_counts = list(self.tx.aql.execute(
      """
      FOR r IN inventory_count_record
      FILTER r.inventory_count_session_key == @session_key
        AND r.status == 'started'
      RETURN { key: r._key, user_key: r.user_key }
      """,
      bind_vars={'session_key': self.info.session_key}
    ))

    if len(active_counts) > 0:
      user_keys = list(set(c['user_key'] for c in active_counts))
      raise ValueError(
        f"Cannot complete session: {len(active_counts)} count(s) are still in progress. "
        f"Users with active counts: {', '.join(user_keys)}. "
        f"Please wait for all counts to be completed or canceled."
      )

    return session

  def apply(self):
    # Validate session can be completed
    self._validate_can_complete()

    # Update session status to COMPLETED
    self.tx.collection('InventoryCountSession').update(dict(
      _key=self.info.session_key,
      status=InventoryCountSessionStatus.COMPLETED,
      completed=self.info.timestamp
    ))

    self.response = dict(
      message=f"Count session {self.info.session_key} completed successfully",
      session_key=self.info.session_key
    )

