from events.work_order.base_work_order import BaseWorkOrder, BaseWorkOrderModel
from events.event_type import EventType
from events.event_model import EventModel

class WorkOrderClosedModel(BaseWorkOrderModel):
  event_type: str = EventType.WORK_ORDER_CLOSED.name

class WorkOrderClosed(BaseWorkOrder):
  event_data: WorkOrderClosedModel

  def set_model(self, base_model: EventModel):
    self.event_data = WorkOrderClosedModel(**base_model.model_dump())

  def apply(self):
    pass
