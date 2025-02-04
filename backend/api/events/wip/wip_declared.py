from events.wip.base_wip import BaseWIP, BaseWIPModel
from models.event import EventType
from models.event import EventModel
from utils.exceptions import WipNotAvailableError
from utils.traceability import Queries as TraceabilityQueries
from models.traceability import WIP
from utils.serial import Queries as SerialQueries
from models.serial import Serial


class WIPDeclaredModel(BaseWIPModel):
  event_type: str = EventType.WIP_DECLARED.name
  product_key: str
  quantity: int

class WIPDeclared(BaseWIP):
  event_data: WIPDeclaredModel

  def set_model(self, base_model: EventModel):
    self.event_data = WIPDeclaredModel(**base_model.model_dump())

  def apply(self):
    if not self.job:
      self.get_job_data()

    self.next_phase_key = self.tx.aql.execute(
      TraceabilityQueries.GET_NEXT_PHASE_IN_WORK_ORDER,
      bind_vars=dict(wo_key=self.event_data.work_order_key, phase_key=self.event_data.phase_key)
    ).next()

    # Prepare new wip data and make a single call to the database with insert_many
    # Insert many requires passing dicts (does not use default db serializer)
    if getattr(self.job, 'traceability_level', None):
      bind_vars = dict(batch_key = self.event_data.batch_key)
      serial_to_declare_cursor = self.tx.aql.execute(SerialQueries.GET_BATCH_SERIALS, bind_vars=bind_vars)
      serial_to_declare = [Serial(**serial) for serial in serial_to_declare_cursor]

      new_wip_data = [dict(
        _from = f'Phase/{self.event_data.phase_key}',
        _to = f'Phase/{self.next_phase_key}',
        batch_key = self.event_data.batch_key,
        wo_key = self.event_data.work_order_key,
        product_key = self.event_data.product_key,
        quantity = 1,
        serial_key = s.key
      ) for s in serial_to_declare]

    else:
      new_wip_data = [dict(
        _from=f'Phase/{self.event_data.phase_key}',
        _to=f'Phase/{self.next_phase_key}',
        batch_key=self.event_data.batch_key,
        wo_key=self.event_data.work_order_key,
        product_key=self.event_data.product_key,
        quantity=self.event_data.quantity
      )]

    self.tx.collection('wip').insert_many(new_wip_data)

    self.update_wip_availability_for_phases(phase_keys=[self.next_phase_key])

