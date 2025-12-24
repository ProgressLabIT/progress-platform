from events.base_event import BaseEvent
from models.event import EventInfoModel, EventType
from utils.inventory import Queries

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

    # Return if position is already flagged as empty
    if col.find(query, limit=1).has_more():
      # If already exists, flag as OK but with a message that position is already flagged
      self.response = dict(message="Position is already flagged as empty for this counting session.")
      return

    # Flag position as empty
    record = dict(
      _from=f'InventoryCountSession/{self.info.session_key}',
      _to=f'Position/{self.info.position_key}',
      status='empty',
      completed_at=self.info.timestamp,
      user_key=self.info.user_key,
      notes=self.info.notes
    )

    self.tx.collection('inventory_count_position_complete').insert(record)

    # Check if parent positions are complete

    # Get the path keys from the root to the current position
    path_keys = list(self.tx.aql.execute(
      Queries.GET_POSITION_PATH,
      bind_vars=dict(position_key=self.info.position_key)
    ))

    for key in reversed(path_keys[:-1]):  # Walk from second to last to beginning, excluding the last item
      result = self.tx.aql.execute(Queries.CHECK_POSITION_COMPLETION, bind_vars=dict(
        session_key=self.info.session_key,
        position_key=key
      )).next()

      if result:
        # Do not indicate user since it's the system that flagged the position as counted
        self.tx.collection('inventory_count_position_complete').insert(dict(
          _from=f'InventoryCountSession/{self.info.session_key}',
          _to=f'Position/{key}',
          status='counted',
          completed_at=self.info.timestamp,
          notes="Last position item checked"
        ))

      else:
        break # Stop checking parent positions if current position is not complete

      self.response = dict(message="Position flagged as empty")
