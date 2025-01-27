from events.batch.base_batch import BaseBatch, BaseBatchModel
from events.event_type import EventType
from events.event_model import EventModel

class BatchCanceledModel(BaseBatchModel):
  event_type: str = EventType.BATCH_CANCELED.name

class BatchCanceled(BaseBatch):
  event_data: BatchCanceledModel

  def set_model(self, base_model: EventModel):
    self.event_data = BatchCanceledModel(**base_model.model_dump())

  def apply(self):
    pass
