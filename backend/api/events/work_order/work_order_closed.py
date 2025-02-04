from events.work_order.base_work_order import BaseWorkOrder, BaseWorkOrderModel
from models.event import EventType
from models.event import EventModel

class WorkOrderClosedModel(BaseWorkOrderModel):
  event_type: str = EventType.WORK_ORDER_CLOSED.name

class WorkOrderClosed(BaseWorkOrder):
  event_data: WorkOrderClosedModel

  def set_model(self, base_model: EventModel):
    self.event_data = WorkOrderClosedModel(**base_model.model_dump())

  def apply(self):
    pass
