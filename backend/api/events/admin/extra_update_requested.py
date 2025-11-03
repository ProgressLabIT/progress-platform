from typing import Any, Literal

from events.base_event import BaseEvent
from models.event import EventType, EventInfoModel


class ExtraUpdateRequestedEvent(BaseEvent):

  class InfoModel(EventInfoModel):
    entity_type: Literal['job', 'work_order']
    entity_key: str
    extra_data: Any
    job_key: str | None = None
    work_order_key: str | None = None

  @classmethod
  def get_tx_collections(cls):
    return ['Job', 'WorkOrder']

  @classmethod
  def get_event_type(cls):
    return EventType.EXTRA_UPDATE_REQUESTED

  @property
  def collection_name(self):
    collection_name_map = {
      'job': 'Job',
      'work_order': 'WorkOrder',
    }
    return collection_name_map[self.info.entity_type]


  def apply(self):
    """
    Updates the extra field for Job or WorkOrder entities.
    """
    # Get the entity to validate it exists
    entity = self.tx.collection(self.collection_name).get(self.info.entity_key)

    if not entity:
      raise ValueError(f"{self.collection_name} with key {self.info.entity_key} not found")

    # Update the extra field
    update_data = {
      '_key': self.info.entity_key,
      'extra': self.info.extra_data
    }

    self.tx.collection(self.collection_name).update(update_data, merge=False)

    # Store job info for post_processing if needed
    if self.info.entity_type == 'job':
      self.info.job_key = self.info.entity_key

    if self.info.entity_type == 'work_order':
      self.info.work_order_key = self.info.entity_key

