from events.batch.base_batch import BaseBatch, BaseBatchModel
from events.event_type import EventType
from events.event_manager import EventManager
from events.event_model import EventModel
from events.production.commons.job import Job
from models.traceability import Batch, StepStatus
from events.wip.wip_booked import WIPBookedModel
from typing import Set


class BatchCreatedModel(BaseBatchModel):
  event_type: str = EventType.BATCH_CREATED.name
  new_batch_key: str | None = None

class BatchCreated(BaseBatch):
  event_data: BatchCreatedModel


  def set_model(self, base_model: EventModel):
    self.event_data = BatchCreatedModel(**base_model.model_dump())

  def apply(self):
    self._get_job_data()

    use_serials = getattr(self.job, 'traceability_level', None)

    if use_serials and not self.job.first_phase:
      if len(self.event_data.batch_serials):
        batch_qt = len(self.event_data.batch_serials)
      else:
        raise ValueError("You must provide serials to be linked to this new batch")
    else:
      default_batch_qt = self.job.parameters.production_batch_qt
      # qt_completed must include any update from the current event being recorded
      remaining_qt = self.job.qt_planned - self.job.qt_completed
      # if production_batch_qt is zero, use total remaining quantity
      if default_batch_qt == 0:
        batch_qt = remaining_qt
      # Do not consider production batch if remaining quantity is lower
      else:
        batch_qt = min([default_batch_qt, remaining_qt])

    if batch_qt == 0:
      raise ValueError("Quantity cannot be zero or negative")

    new_batch_in = Batch(
      job_key = self.event_data.job_key,
      phase_key = self.event_data.phase_key,
      work_order_key = self.event_data.work_order_key,
      qt_total = batch_qt,
      start = self.event_data.timestamp,
      active = True
    )

    new_batch_out = self.tx.collection('Batch').insert(new_batch_in, return_new=True)['new']

    self.batch = Batch(**new_batch_out)
    self.event_data.new_batch_key = self.batch.key

    # Book wip from buffer
    if not self.job.first_phase:
      #self.book_wip(batch_qt)
      EventManager.trigger_event(self, WIPBookedModel(
        job_key=self.event_data.job_key,
        phase_key=self.event_data.phase_key,
        work_order_key=self.event_data.work_order_key,
        quantity=batch_qt,
        batch_key=self.event_data.new_batch_key
      ))
    elif use_serials:
      self._create_batch_serial_records(quantity=batch_qt)

    self.set_response(dict(new_batch_out=self.batch))

