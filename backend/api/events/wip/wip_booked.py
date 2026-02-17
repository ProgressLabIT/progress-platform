from events.production.base_production import BaseProductionEvent
from models.event import EventInfoModel, EventType
from models.traceability import WIP
from utils.exceptions import WipNotAvailableError
from utils.float_precision import float_gte, round_float
from utils.serial import Queries as SerialQueries
from utils.traceability import Queries as TraceabilityQueries


class WIPBookedEvent(BaseProductionEvent):
  class InfoModel(EventInfoModel):
    job_key: str
    phase_key: str
    work_order_key: str
    quantity: int
    batch_key: str
    batch_serials: list[str] | None = None

  @classmethod
  def get_event_type(cls) -> EventType:
    return EventType.WIP_BOOKED

  def apply(self):
    self._get_job_data()

    if self.info.quantity == 0:
      raise ValueError("Cannot book a quantity of zero")

    # Traceability Enabled -> Book specific serials in case of phases following the first
    if getattr(self.job, 'traceability_level', None) and self.info.batch_serials != None and not self.job.first_phase:
      if len(self.info.batch_serials) == self.info.quantity:
        self.book_wip_serials()
      else:
        raise ValueError(f"The number of serials provided does not match the requested quantity. Provided quantity: {self.info.quantity}. Provided serials: {self.info.batch_serials}")

    # Traceability
    else:
      free_wips_cursor = self.tx.aql.execute(
        TraceabilityQueries.RETRIEVE_AVAILABLE_WIP,
        bind_vars=dict(phase_key=self.info.phase_key, wo_key=self.info.work_order_key)
      )
      free_wips = [WIP(**wip) for wip in free_wips_cursor]
      free_wips = sorted(free_wips, key=lambda wip: wip.quantity)

      # TODO: change using while loop like in events/admin.py@override_progress
      for wip in free_wips:
        # Use tolerance comparison to handle epsilon precision noise
        if float_gte(self.info.quantity, wip.quantity):
          # Book entire batch for job
          self.tx.collection('wip').update(dict(
            _key = wip.key,
            _to = f'Job/{self.info.job_key}',
            active = True
          ))
          self.info.quantity -= wip.quantity
          if self.info.quantity == 0:
            break

        else:
          # Partially book batch for job
          booking_percentage = round_float(self.info.quantity / wip.quantity)
          self.tx.collection('wip').update(dict(
            _key=wip.key,
            quantity=wip.quantity - self.info.quantity,
            value=wip.value * (1 - booking_percentage)
          ))

          # Add wip record with partially booked batch
          new_wip = WIP(
            from_doc=wip.from_doc,
            to_doc=f'Job/{self.info.job_key}',
            wo_key=wip.wo_key,
            product_key=wip.product_key,
            quantity=self.info.quantity,
            value=wip.quantity * booking_percentage,
            active=True
          )
          self.tx.collection('wip').insert(new_wip)
          self.info.quantity = 0
          break

      if self.info.quantity > 0:
        raise WipNotAvailableError(f"Not enough free wip available to book. Needed { self.info.quantity } more")

    # Update input availability for jobs in this phase
    # Execute both with and without traceability
    self.update_wip_availability_for_phases(phase_keys=[self.info.phase_key])

  def book_wip_serials(self):
    # Reset job/batch links in wip and batch_serial so that it works
    # when serials are changed or the quantity reduced
    reset_wip_match = dict(_to=f'Job/{self.info.job_key}')
    reset_wip_update = dict(_to=f'Phase/{self.info.phase_key}', active=False)
    self.tx.collection('wip').update_match(reset_wip_match, reset_wip_update)

    reset_batch_serial_match = dict(_from=f'Batch/{self.info.batch_key}')
    self.tx.collection('batch_serial').delete_match(reset_batch_serial_match)

    # Book and link to batch new serials, checking they are all available
    free_wip_cursor = self.tx.aql.execute(
      TraceabilityQueries.RETRIEVE_AVAILABLE_WIP,
      bind_vars=dict(phase_key=self.info.phase_key, wo_key=self.info.work_order_key)
    )
    free_wip_serials = [WIP(**wip).serial_key for wip in free_wip_cursor]

    serials_to_update = []
    unavailable_serials = []
    for serial_key in self.info.batch_serials:
      target = serials_to_update if serial_key in free_wip_serials else unavailable_serials
      target.append(serial_key)

    if len(unavailable_serials):
      raise WipNotAvailableError(f'Serials {unavailable_serials} are not available')
    else:
      # Book serials in wip
      self.tx.aql.execute(
        SerialQueries.BOOK_SERIAL_WIP,
        bind_vars=dict(
          serial_keys=serials_to_update,
          job_key=self.info.job_key
        )
      )

      # Link serials to batch
      self._create_batch_serial_records(
        batch_key=self.info.batch_key,
        serial_keys=serials_to_update
      )


    self.update_wip_availability_for_phases(phase_keys=[self.info.phase_key])
