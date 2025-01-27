from events.work_order.base_work_order import BaseWorkOrder, BaseWorkOrderModel
from events.event_type import EventType
from events.event_model import EventModel
from models.production import WorkStatus
from utils.db import model_to_db_dict

class WorkOrderStartedModel(BaseWorkOrderModel):
  event_type: str = EventType.WORK_ORDER_STARTED.name

class WorkOrderStarted(BaseWorkOrder):
  event_data: WorkOrderStartedModel

  def set_model(self, base_model: EventModel):
    self.event_data = WorkOrderStartedModel(**base_model.model_dump())

  def apply(self):
    wo = self._get_work_order_data()

    stage = WorkStatus.STARTED

    if wo.status == WorkStatus.CREATED:
      wo.status = stage
      wo.start = self.event_data.timestamp
      wo_update = model_to_db_dict(wo)
      self.tx.collection('WorkOrder').update(wo_update)

    self.set_response(dict(
      stage = stage
    ))

