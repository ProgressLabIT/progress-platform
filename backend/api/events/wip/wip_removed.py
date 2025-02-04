from events.wip.base_wip import BaseWIP, BaseWIPModel
from models.event import EventType
from models.event import EventModel
from models.traceability import WIP
from utils.exceptions import WipNotAvailableError

class WIPRemovedModel(BaseWIPModel):
  event_type: str = EventType.WIP_REMOVED.name
  quantity: int


class WIPRemoved(BaseWIP):
  event_data: WIPRemovedModel

  def set_model(self, base_model: EventModel):
    self.event_data = WIPRemovedModel(**base_model.model_dump())

  def apply(self):
    """
    Remove upstream wip records related to the completed batch
    """
    booked_wips_cursor = self.tx.collection('wip').find(dict(
      _to=f'Job/{self.event_data.job_key}',
    ))
    booked_wips = [WIP(**wip) for wip in booked_wips_cursor]
    # Here we sort the wip by quantity in ascending order to remove as many full records as possible, starting from the smallest one.
    # NEXT: In the future, when serial number management will be implemented, this logic will have to be reviewed to account for specific wip selection.
    booked_wips = sorted(booked_wips, key=lambda wip: wip.quantity)

    # Remove/reduce wip, record by record up to declared quantity
    for wip in booked_wips:
      if self.event_data.quantity >= wip.quantity:
        # Remove entire wip for job
        self.tx.collection('wip').delete(wip.key)
        self.event_data.quantity -= wip.quantity
        if self.event_data.quantity == 0:
          break
      else:
        # Partially remove wip by reducing the quantity
        unbooking_percentage = self.event_data.quantity / wip.quantity
        self.tx.collection('wip').update(dict(
          _key=wip.key,
          quantity=wip.quantity - self.event_data.quantity,
          value=wip.value * (1 - unbooking_percentage)
        ))
        self.event_data.quantity = 0
        break

    if self.event_data.quantity > 0:
      raise WipNotAvailableError(f"Not enough booked wip to remove. Needed { self.event_data.quantity } more")
