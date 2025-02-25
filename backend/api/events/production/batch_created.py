from events.production.base_production import BaseProductionEvent
from events.wip.wip_booked import WIPBookedEvent
from models.event import EventInfoModel, EventType
from models.traceability import Batch


class BatchCreatedEvent(BaseProductionEvent):
  class InfoModel(EventInfoModel):
    job_key: str
    phase_key: str
    work_order_key: str
    product_key: str
    batch_serials: list[str] | None = None # Can be list of serial keys or serial codes

  @staticmethod
  def get_event_type() -> EventType:
    return EventType.BATCH_CREATED


  def apply(self):
    self._get_job_data()

    use_serials = getattr(self.job, 'traceability_level', None)

    if use_serials and not self.job.first_phase:
      if len(self.info.batch_serials):
        batch_qt = len(self.info.batch_serials)
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
      job_key = self.info.job_key,
      phase_key = self.info.phase_key,
      product_key = self.info.product_key,
      work_order_key = self.info.work_order_key,
      qt_total = batch_qt,
      start = self.info.timestamp,
      active = True
    )

    new_batch_out = self.tx.collection('Batch').insert(new_batch_in, return_new=True)['new']

    self.batch = Batch(**new_batch_out)
    self.info.new_batch_key = self.batch.key

    # Book wip from buffer
    if not self.job.first_phase:
      #self.book_wip(batch_qt)
      WIPBookedEvent.create_as_child(self, dict(
        job_key=self.info.job_key,
        phase_key=self.info.phase_key,
        work_order_key=self.info.work_order_key,
        quantity=batch_qt,
        batch_key=self.info.new_batch_key,
        batch_serials=self.info.batch_serials
      ))
    elif use_serials:
      product = self.tx.collection('Product').get(self.info.product_key)
      start_with_code = product.get('serialcode_on_batchstart', False)
      counter_key = product.get('counter_key', None)
      if start_with_code and not len(self.info.batch_serials) and counter_key is None:
        raise ValueError("You must provide serial codes or define counter to start a new batch for this product")

      self._create_serial_records(
        quantity=batch_qt,
        counter_key=counter_key,
        batch_key=self.info.new_batch_key,
        wo_key=self.info.work_order_key,
        product_key=self.info.product_key,
        serial_codes=self.info.batch_serials,
        released=None
      )

    self.response = self.batch

