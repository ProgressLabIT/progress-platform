from events.wip.base_wip import BaseWIP, BaseWIPModel
from events.event_type import EventType
from events.event_model import EventModel
from models.traceability import WIP
from utils.exceptions import WipNotAvailableError


class WIPUnbookedModel(BaseWIPModel):
  event_type: str = EventType.WIP_UNBOOKED.name
  quantity: int


class WIPUnbooked(BaseWIP):
  event_data: WIPUnbookedModel

  def set_model(self, base_model: EventModel):
    self.event_data = WIPUnbookedModel(**base_model.model_dump())

  def apply(self):
    if not hasattr(self, 'job'):
      self._get_job_data()

    if self.event_data.quantity == 0:
        return

    booked_wips_cursor = self.tx.collection('wip').find(dict(
      _to=f'Job/{self.job_key}',
    ))
    booked_wips = [WIP(**wip) for wip in booked_wips_cursor]
    booked_wips = sorted(booked_wips, key=lambda wip: wip.quantity)

    for wip in booked_wips:
      if self.event_data.quantity >= wip.quantity:
        # Unbook entire batch for job
        self.tx.collection('wip').update(dict(
          _key = wip.key,
          _to = f'Phase/{self.phase_key}'
        ))
        self.event_data.quantity -= wip.quantity
        if self.event_data.quantity == 0:
          break
      else:
        # Partially unbook batch for job
        unbooking_percentage = self.event_data.quantity / wip.quantity
        self.tx.collection('wip').update(dict(
          _key=wip.key,
          quantity=wip.quantity - self.event_data.quantity,
          value=wip.value * (1 - unbooking_percentage)
        ))

        # Add free wip record with partially unbooked batch
        new_wip = WIP(
          from_doc=wip.from_doc,
          to_doc=f'Phase/{self.phase_key}',
          wo_key=wip.wo_key,
          batch_key=wip.batch_key,
          product_key=wip.product_key,
          quantity=self.event_data.quantity,
          value=wip.quantity * unbooking_percentage,
          active=True
        )
        self.tx.collection('wip').insert(new_wip)
        self.event_data.quantity = 0
        break

    if self.event_data.quantity > 0:
        raise WipNotAvailableError(f"Not enough booked wip available to unbook. Needed { self.event_data.quantity } more")

    # Update input availability for jobs in this phase
    self.update_wip_availability_for_phases(phase_keys=[self.phase_key])

