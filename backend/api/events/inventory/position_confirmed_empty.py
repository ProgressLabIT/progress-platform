from events.base_event import BaseEvent
from models.event import EventInfoModel, EventType


class PositionConfirmedEmptyEvent(BaseEvent):
  class InfoModel(EventInfoModel):
    session_key: str
    position_key: str
    notes: str | None = None

  @classmethod
  def get_event_type(cls):
    return EventType.POSITION_CONFIRMED_EMPTY

  @classmethod
  def get_tx_collections(cls):
    return ['inventory_count_position_complete']


  # ========================================================
  # MAIN LOGIC
  # ========================================================

  def apply(self):

    # Check if a record with this _from and _to already exists (i.e., position already flagged empty)
    col = self.tx.collection('inventory_count_position_complete')
    query = dict(
      _from=f'InventoryCountSession/{self.info.session_key}',
      _to=f'Position/{self.info.position_key}'
    )

    if col.find(query, limit=1).has_more():
      # If already exists, flag as OK but with a message that position is already flagged
      self.response = dict(message="Position is already flagged as empty for this counting session.")
      return

    else:
      record = dict(
        _from=f'InventoryCountSession/{self.info.session_key}',
        _to=f'Position/{self.info.position_key}',
        status='empty',
        completed_at=self.info.timestamp,
        user_key=self.info.user_key,
        notes=self.info.notes
      )

      self.tx.collection('inventory_count_position_complete').insert(record)

      self.response = dict(message="Position flagged as empty")
