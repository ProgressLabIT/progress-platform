from events.production.base_production import BaseProductionEvent
from models.event import EventInfoModel, EventType
from models.traceability import WIP
from utils.exceptions import WipNotAvailableError


class WIPUnbookedEvent(BaseProductionEvent):
  class InfoModel(EventInfoModel):
    job_key: str
    quantity: int

  @classmethod
  def get_event_type(cls):
    return EventType.WIP_UNBOOKED


  def apply(self):
    if not hasattr(self, 'job'):
      self._get_job_data()

    if self.info.quantity == 0:
        return

    booked_wips_cursor = self.tx.collection('wip').find(dict(
      _to=f'Job/{self.info.job_key}',
    ))
    booked_wips = sorted([WIP(**wip) for wip in booked_wips_cursor], key=lambda wip: wip.quantity)

    for wip in booked_wips:
      if self.info.quantity >= wip.quantity:
        # Unbook entire batch for job
        self.tx.collection('wip').update(dict(
          _key = wip.key,
          _to = f'Phase/{self.info.phase_key}',
          active = False
        ))
        self.info.quantity -= wip.quantity
        if self.info.quantity == 0:
          break
      else:
        # Partially unbook batch for job
        unbooking_percentage = self.info.quantity / wip.quantity
        self.tx.collection('wip').update(dict(
          _key=wip.key,
          quantity=wip.quantity - self.info.quantity,
          value=wip.value * (1 - unbooking_percentage)
        ))

        # Add free wip record with partially unbooked batch
        new_wip = WIP(
          from_doc=wip.from_doc,
          to_doc=f'Phase/{self.info.phase_key}',
          wo_key=wip.wo_key,
          product_key=wip.product_key,
          quantity=self.info.quantity,
          value=wip.quantity * unbooking_percentage,
          active=False
        )
        self.tx.collection('wip').insert(new_wip)
        self.info.quantity = 0
        break

    if self.info.quantity > 0:
        raise WipNotAvailableError(f"Not enough booked wip available to unbook. Needed { self.info.quantity } more")

    # Update input availability for jobs in this phase
    self.update_wip_availability_for_phases(phase_keys=[self.info.phase_key])

