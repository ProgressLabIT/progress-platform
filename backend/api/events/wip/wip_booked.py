from events.wip.base_wip import BaseWIP, BaseWIPModel
from events.event_type import EventType
from events.event_model import EventModel
from utils.traceability import Queries as TraceabilityQueries
from models.traceability import WIP
from utils.exceptions import WipNotAvailableError
from typing import Set
from models.serial import Serial
from utils.serial import Queries as SerialQueries

from events.event_manager import EventManager

class WIPBookedModel(BaseWIPModel):
  event_type: str = EventType.WIP_BOOKED.name
  quantity: int


class WIPBooked(BaseWIP):
  event_data: WIPBookedModel

  def set_model(self, base_model: EventModel):
    self.event_data = WIPBookedModel(**base_model.model_dump())

  def apply(self):
    self._get_job_data()

    if self.event_data.quantity == 0:
      raise ValueError("Cannot book a quantity of zero")

    # Traceability Enabled -> Book specific serials in case of phases following the first
    if getattr(self.job, 'traceability_level', None) and self.event_data.batch_serials != None and not self.job.first_phase:
      if len(self.event_data.batch_serials) == self.event_data.quantity:
        self.book_wip_serials()
      else:
        raise ValueError("The number of serials provided does not match the requested quantity. Provided quantity: {quantity}. Provided serials: {self.batch_serials}")

    # Traceability
    else:
      free_wips_cursor = self.tx.aql.execute(
        TraceabilityQueries.RETRIEVE_AVAILABLE_WIP,
        bind_vars=dict(phase_key=self.event_data.phase_key, wo_key=self.event_data.work_order_key)
      )
      free_wips = [WIP(**wip) for wip in free_wips_cursor]
      free_wips = sorted(free_wips, key=lambda wip: wip.quantity)

      # TODO: change using while loop like in events/admin.py@override_progress
      for wip in free_wips:
        if self.event_data.quantity >= wip.quantity:
          # Book entire batch for job
          self.tx.collection('wip').update(dict(
            _key = wip.key,
            _to = f'Job/{self.event_data.job_key}',
            active = True
          ))
          self.event_data.quantity -= wip.quantity
          if self.event_data.quantity == 0:
            break

        else:
          # Partially book batch for job
          booking_percentage = self.event_data.quantity / wip.quantity
          self.tx.collection('wip').update(dict(
            _key=wip.key,
            quantity=wip.quantity - self.event_data.quantity,
            value=wip.value * (1 - booking_percentage)
          ))

          # Add wip record with partially booked batch
          new_wip = WIP(
            from_doc=wip.from_doc,
            to_doc=f'Job/{self.event_data.job_key}',
            wo_key=wip.wo_key,
            batch_key=wip.batch_key,
            product_key=wip.product_key,
            quantity=self.event_data.quantity,
            value=wip.quantity * booking_percentage,
            active=True
          )
          self.tx.collection('wip').insert(new_wip)
          self.event_data.quantity = 0
          break

      if self.event_data.quantity > 0:
        raise WipNotAvailableError(f"Not enough free wip available to book. Needed { self.event_data.quantity } more")

    # Update input availability for jobs in this phase
    # Execute both with and without traceability
    self.update_wip_availability_for_phases(phase_keys=[self.event_data.phase_key])

  def book_wip_serials(self):
    # Reset job/batch links in wip and batch_serial so that it works
    # when serials are changed or the quantity reduced
    reset_wip_match = dict(_to=f'Job/{self.event_data.job_key}')
    reset_wip_update = dict(_to=f'Phase/{self.event_data.phase_key}', active=False)
    self.tx.collection('wip').update_match(reset_wip_match, reset_wip_update)

    reset_batch_serial_match = dict(_from=f'Batch/{self.event_data.batch_key}')
    self.tx.collection('batch_serial').delete_match(reset_batch_serial_match)

    # Book and link to batch new serials, checking they are all available
    free_wip_cursor = self.tx.aql.execute(
      TraceabilityQueries.RETRIEVE_AVAILABLE_WIP,
      bind_vars=dict(phase_key=self.event_data.phase_key, wo_key=self.event_data.work_order_key)
    )
    free_wip_serials = [WIP(**wip).serial_key for wip in free_wip_cursor]

    serials_to_update = []
    unavailable_serials = []
    for serial_key in self.event_data.batch_serials:
      target = serials_to_update if serial_key in free_wip_serials else unavailable_serials
      target.append(serial_key)

    if len(unavailable_serials):
      raise WipNotAvailableError(f'Serials {unavailable_serials} are not available')
    else:
      self.tx.aql.execute(
        SerialQueries.BOOK_SERIAL_WIP,
        bind_vars=dict(
          serial_keys=serials_to_update,
          job_key=self.event_data.job_key
        )
      )

      EventManager.notify_event(self, SerialBatchLinkedModel(
          batch_key = self.event_data.batch_key,
          batch_serials=self.event_data.batch_serials,
          user_key = self.event_data.user_key
        ))

    self.update_wip_availability_for_phases(phase_keys=[self.event_data.phase_key])
