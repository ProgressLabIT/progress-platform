from datetime import datetime, date

from events.base_event import BaseEvent
from models.bom import WOBomLine
from models.event import EventInfoModel, EventType


class WorkOrderStartedEvent(BaseEvent):
  _notification_subtopic = "production"

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
  _notification_subtopic = "production"

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
  _notification_subtopic = "production"

  class InfoModel(EventInfoModel):
    work_order_key: str
    new_due_date: datetime | date | None = None
    new_from_date: datetime | date | None = None
    new_project_code: str | None = None
    new_bom: list[WOBomLine] | None = None
    new_output_position_key: str | None = None
    notes: str | None = None

  @classmethod
  def get_event_type(cls):
    return EventType.WORK_ORDER_UPDATED

  @classmethod
  def get_tx_collections(cls):
    return ['WorkOrder', 'Job']

  def apply(self):
    entity = self.tx.collection('WorkOrder').get(self.info.work_order_key)
    if not entity:
      raise ValueError(f"WorkOrder with key {self.info.work_order_key} not found")

    wo_update = dict(_key=self.info.work_order_key)
    job_match = dict(wo_key=self.info.work_order_key)
    job_update = dict()

    if self.info.new_due_date is not None:
      wo_update['due_by'] = self.info.new_due_date

    if self.info.notes is not None:
      wo_update['notes'] = self.info.notes

    if self.info.new_from_date is not None:
      wo_update['start_from'] = self.info.new_from_date
      job_update.update({'start_from': self.info.new_from_date})

    if self.info.new_project_code is not None:
      wo_update['project_code'] = self.info.new_project_code
      job_update.update({'project_code': self.info.new_project_code})

    if self.info.new_project_code or self.info.new_from_date:
      self.tx.collection('Job').update_match(job_match, job_update)

    if self.info.new_bom:
      wo_update['wo_bom'] = self.info.new_bom

    if self.info.new_output_position_key:
      wo_update['output_position_key'] = self.info.new_output_position_key

    updated_wo_data = self.tx.collection('WorkOrder').update(wo_update, return_new=True)['new']
    self.response = updated_wo_data


class WorkOrderCreatedEvent(BaseEvent):
  _notification_subtopic = "production"

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
