from events.base_event import BaseEvent
from models.event import EventInfoModel, EventType

class BatchReleasedEvent(BaseEvent):
  class InfoModel(EventInfoModel):
    batch_key: str
    product_key: str
    work_order_key: str
    qt_released: float
    serial_keys: list[str] | None = None

  @classmethod
  def get_event_type(cls):
    return EventType.BATCH_RELEASED

  @classmethod
  def get_tx_collections(cls):
    return []

  def apply(self):
    pass
