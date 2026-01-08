from events.base_event import BaseEvent
from models.event import EventInfoModel, EventType
from models.inventory.counting import InventoryCountSessionStatus


class CountSessionResumedEvent(BaseEvent):
  """
  Transitions a count session from COMPLETED back to STARTED status.
  This allows warehouse admins to resume counting if further counts/adjustments are needed
  before applying the final adjustments.
  """

  class InfoModel(EventInfoModel):
    session_key: str

  @classmethod
  def get_event_type(cls):
    return EventType.COUNT_SESSION_RESUMED

  @classmethod
  def get_tx_collections(cls):
    return ['InventoryCountSession']

  def apply(self):
    # Fetch and validate session
    session = self.tx.collection('InventoryCountSession').get(self.info.session_key)
    if session is None:
      raise ValueError(f"Session {self.info.session_key} not found")

    current_status = session.get('status')
    if current_status != InventoryCountSessionStatus.COMPLETED.value:
      raise ValueError(
        f"Session must be in 'completed' status to resume. "
        f"Current status: {current_status}"
      )

    # Update session status back to STARTED and clear completed timestamp
    self.tx.collection('InventoryCountSession').update(dict(
      _key=self.info.session_key,
      status=InventoryCountSessionStatus.STARTED,
      completed=None
    ))

    self.response = dict(
      message=f"Count session {self.info.session_key} resumed successfully",
      session_key=self.info.session_key
    )
