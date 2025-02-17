from events.production.base_production import BaseProductionEvent
from models.event import EventInfoModel, EventType
from models.serial import Serial
from models.traceability import WIP
from utils.serial import Queries as SerialQueries
from utils.traceability import Queries as TraceabilityQueries


class WIPDeclaredEvent(BaseProductionEvent):
  class InfoModel(EventInfoModel):
    job_key: str
    batch_key: str
    quantity: int

  @classmethod
  def get_event_type(cls):
    return EventType.WIP_DECLARED


  def apply(self):
    self._get_job_data()

    self.next_phase_key = self.tx.aql.execute(
      TraceabilityQueries.GET_NEXT_PHASE_IN_WORK_ORDER,
      bind_vars=dict(wo_key=self.info.work_order_key, phase_key=self.info.phase_key)
    ).next()

    # Prepare new wip data and make a single call to the database with insert_many
    # Insert many requires passing dicts (does not use default db serializer)
    if getattr(self.job, 'traceability_level', None):
      bind_vars = dict(batch_key = self.info.batch_key)
      serial_to_declare_cursor = self.tx.aql.execute(SerialQueries.GET_BATCH_SERIALS, bind_vars=bind_vars)
      serial_to_declare = [Serial(**serial) for serial in serial_to_declare_cursor]

      new_wip_data = [dict(
        _from = f'Phase/{self.info.phase_key}',
        _to = f'Phase/{self.next_phase_key}',
        batch_key = self.info.batch_key,
        wo_key = self.info.work_order_key,
        product_key = self.info.product_key,
        quantity = 1,
        serial_key = s.key
      ) for s in serial_to_declare]

    else:
      new_wip_data = [WIP(
        _from=f'Phase/{self.info.phase_key}',
        _to=f'Phase/{self.next_phase_key}',
        batch_key=self.info.active_batch_key,
        wo_key=self.info.work_order_key,
        product_key=self.info.product_key,
        quantity=self.info.quantity
      )]

    self.tx.collection('wip').insert_many(new_wip_data)

    self.update_wip_availability_for_phases(phase_keys=[self.next_phase_key])

