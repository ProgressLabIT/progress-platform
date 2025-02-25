from events.base_event import BaseEvent
from models.event import EventInfoModel, EventType


class WorkOrderStartedEvent(BaseEvent):
  class InfoModel(EventInfoModel):
    work_order_key: str

  @classmethod
  def get_event_type(cls):
    return EventType.WORK_ORDER_STARTED

  @classmethod
  def get_tx_collections(cls):
    return []

  def apply(self):
    pass


class WorkOrderClosedEvent(BaseEvent):
  class InfoModel(EventInfoModel):
    work_order_key: str

  @classmethod
  def get_event_type(cls):
    return EventType.WORK_ORDER_CLOSED

  @classmethod
  def get_tx_collections(cls):
    return []

  def apply(self):
    pass



class WorkOrderUpdatedEvent(BaseEvent):
  class InfoModel(EventInfoModel):
    work_order_key: str

  @classmethod
  def get_event_type(cls):
    return EventType.WORK_ORDER_UPDATED

  @classmethod
  def get_tx_collections(cls):
    return []

  def apply(self):
    pass


class WorkOrderCreatedEvent(BaseEvent):
  class InfoModel(EventInfoModel):
    work_order_key: str

  @classmethod
  def get_event_type(cls):
    return EventType.WORK_ORDER_CREATED

  @classmethod
  def get_tx_collections(cls):
    return []

  def apply(self):
    pass

