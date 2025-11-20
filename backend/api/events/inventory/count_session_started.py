from events.base_event import BaseEvent
from models.event import EventInfoModel, EventType
from models.inventory.counting import InventoryCountSessionStatus


class CountSessionStartedEvent(BaseEvent):
  class InfoModel(EventInfoModel):
    count_session_key: str

  @classmethod
  def get_event_type(cls):
    return EventType.COUNT_SESSION_STARTED

  @classmethod
  def get_tx_collections(cls):
    return ['InventoryCountSession']

  def apply(self):
    # Update session status to 'started' and set the started timestamp
    self.tx.collection('InventoryCountSession').update(dict(
      _key=self.info.count_session_key,
      status=InventoryCountSessionStatus.STARTED,
      started=self.info.timestamp
    ))
