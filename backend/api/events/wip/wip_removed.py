from events.production.base_production import BaseProductionEvent
from models.event import EventInfoModel, EventType
from models.traceability import WIP
from utils.exceptions import WipNotAvailableError
from utils.float_precision import float_gte, round_float


class WIPRemovedEvent(BaseProductionEvent):
  class InfoModel(EventInfoModel):
    job_key: str
    quantity: int

  @classmethod
  def get_event_type(cls):
    return EventType.WIP_REMOVED


  def apply(self):
    """
    Remove the given quantity of wip records booked by the job (upstream)
    """
    booked_wips_cursor = self.tx.collection('wip').find(dict(
      _to=f'Job/{self.info.job_key}',
    ))
    booked_wips = [WIP(**wip) for wip in booked_wips_cursor]
    # Here we sort the wip by quantity in ascending order to remove as many full records as possible, starting from the smallest one.
    # NEXT: In the future, when serial number management will be implemented, this logic will have to be reviewed to account for specific wip selection.
    booked_wips = sorted(booked_wips, key=lambda wip: wip.quantity)

    # Remove/reduce wip, record by record up to declared quantity
    for wip in booked_wips:
      # Use tolerance comparison to handle epsilon precision noise
      if float_gte(self.info.quantity, wip.quantity):
        # Remove entire wip for job
        self.tx.collection('wip').delete(wip.key)
        self.info.quantity -= wip.quantity
        if self.info.quantity == 0:
          break
      else:
        # Partially remove wip by reducing the quantity
        unbooking_percentage = round_float(self.info.quantity / wip.quantity)
        self.tx.collection('wip').update(dict(
          _key=wip.key,
          quantity=wip.quantity - self.info.quantity,
          value=wip.value * (1 - unbooking_percentage)
        ))
        self.info.quantity = 0
        break

    if self.info.quantity > 0:
      raise WipNotAvailableError(f"Not enough booked wip to remove. Needed { self.info.quantity } more")
