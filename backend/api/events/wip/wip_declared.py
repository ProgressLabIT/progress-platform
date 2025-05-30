from events.production.base_production import BaseProductionEvent
from models.event import EventInfoModel, EventType
from models.serial import Serial
from models.traceability import WIP
from utils.serial import Queries as SerialQueries
from utils.traceability import Queries as TraceabilityQueries


class WIPDeclaredEvent(BaseProductionEvent):
  class InfoModel(EventInfoModel):
    job_key: str
    quantity: int
    serial_keys: list[str] | None = None

  @classmethod
  def get_event_type(cls):
    return EventType.WIP_DECLARED


  def apply(self):
    self._get_job_data()

    self.next_phase_key = self.tx.aql.execute(
      TraceabilityQueries.GET_NEXT_PHASE_IN_WORK_ORDER,
      bind_vars=dict(wo_key=self.job.wo_key, phase_key=self.job.phase_key)
    ).next()

    # Prepare new wip data and make a single call to the database with insert_many
    # Insert many requires passing dicts (does not use default db serializer)
    if getattr(self.job, 'traceability_level', None):

      if not self.info.serial_keys or len(self.info.serial_keys) == 0:
        raise ValueError('Serial keys are required to declare wip when traceability is enabled')
      if self.info.serial_keys != list(set(self.info.serial_keys)):
        raise ValueError('Serial keys must be unique')
      if len(self.info.serial_keys) != self.info.quantity:
        raise ValueError('Serial keys must match quantity')

      new_wip_data = [dict(
        _from = f'Phase/{self.job.phase_key}',
        _to = f'Phase/{self.next_phase_key}',
        wo_key = self.job.wo_key,
        product_key = self.job.product_key,
        quantity = 1,
        serial_key = s,
        active = False
      ) for s in self.info.serial_keys]

    else:
      new_wip_data = [dict(
        _from=f'Phase/{self.job.phase_key}',
        _to=f'Phase/{self.next_phase_key}',
        wo_key=self.job.wo_key,
        product_key=self.job.product_key,
        quantity=self.info.quantity,
        active=False
      )]

    self.tx.collection('wip').insert_many(new_wip_data)

    self.update_wip_availability_for_phases(phase_keys=[self.next_phase_key])

