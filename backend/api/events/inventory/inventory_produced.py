from events.inventory.base_inventory import BaseInventory
from events.event_type import EventType
from events.event_model import EventModel
from models.traceability import Batch
from models.product import TraceabilityLevel
from models.production import Job, WorkStatus
from utils.serial import Queries as SerialQueries
from events.event_model import EventModel
from models.serial import Serial
from models.inventory import InventoryMovementType, MovementStatus
from events.event_manager import EventManager
from events.inventory.movement_created import MovementCreatedModel
from utils.exceptions import InventoryMovementException

class InventoryProducedModel(EventModel):
  event_type: str = EventType.INVENTORY_PRODUCED.name
  batch_key: str
  job_key: str
  product_key: str
  quantity: float

class InventoryProduced(BaseInventory):
  event_data: InventoryProducedModel
  batch: Batch
  job: Job

  def set_model(self, base_model: EventModel):
    self.event_data = InventoryProducedModel(**base_model.model_dump())

  def validate_event(self):
    enable_inventory_management = self.tx.collection('Config').get('enable_inventory_management') or False
    if not enable_inventory_management:
      self.not_handled_response('Inventory management is not enabled')
      return False
    return super().validate_event()

  def apply(self):
    self._get_product()
    self._get_batch()
    self._get_job()

    if (self.job['traceability_level'] is not None):
      cursor = self.tx.aql.execute(
         SerialQueries.GET_BATCH_SERIALS,
         bind_vars=dict(batch_key=self.event_data.batch_key
      ))
      # JUST IN CASE: Consider only serials to be released to avoid reassigning a new release date
      batch_serials = [Serial(**s) for s in cursor if s['released'] is None]
      for serial in batch_serials:
        EventManager.notify_event(self, MovementCreatedModel(
          movement = dict(
            product_key = serial.product_key,
            qt_planned = 1,
            qt_confirmed = 1,
            serial_key = serial.key,
            type = InventoryMovementType.PRODUCTION,
            status = MovementStatus.COMPLETED,
          )
        ))
    else:
      EventManager.notify_event(self, MovementCreatedModel(
        movement = dict(
          batch_key = self.event_data.batch_key,
          job_key = self.event_data.job_key,
          product_key = self.event_data.product_key,
          quantity = self.event_data.quantity,
        )
      ))

  def _get_product(self):
    self.product = self.tx.collection('Product').get(self.event_data.product_key)
    if self.product is None:
      raise InventoryMovementException(f'Product not found')

  def _get_batch(self):
    self.batch = self.tx.collection('Batch').get(self.event_data.batch_key)
    if self.batch is None:
      raise Exception(f'Batch not found')

  def _get_job(self):
    self.job = self.tx.collection('Job').get(self.event_data.job_key)
    if self.job is None:
      raise Exception(f'Job not found')
