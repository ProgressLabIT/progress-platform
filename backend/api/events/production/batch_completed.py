from events.serial.serial_batch_confirmed import SerialBatchConfirmedEvent
from events.serial.serial_released import SerialReleasedEvent
from events.serial.serial_data_updated import SerialDataUpdatedEvent
from events.production.base_production import BaseProductionEvent, BaseProductionModel
from models.form import FormFieldValue
from models.traceability import *
from models.production import Job
from utils.exceptions import WipNotAvailableError
from utils.production import Queries as ProductionQueries
from utils.traceability import Queries as TraceabilityQueries
from models.event import EventType
from events.batch.base_batch import BaseBatchModel
from events.work_session.work_session_closed import WorkSessionClosedEvent
from events.wip.wip_declared import WIPDeclaredModel
from events.wip.wip_removed import WIPRemovedModel
from events.wip.wip_unbooked import WIPUnbookedModel
from events.inventory.movement_created import MovementCreatedModel
from events.work_session.work_session_created import WorkSessionCreatedEvent
from events.wip.wip_booked import WIPBookedModel
from models.inventory import InventoryMovementType, MovementStatus
from events.inventory import InventoryChangedEvent

class BatchCompletedEvent(BaseProductionEvent):
  class InfoModel(BaseBatchModel):
    completed_batch_key: str
    form_data: list[FormFieldValue]


  @classmethod
  def get_event_type(cls):
    return EventType.BATCH_COMPLETED


  from events.production.commons.serial import(
    convert_form_data,
    convert_batch_data,
  )

  def apply(self):
    self._get_job_data()

    if self.job.stage == 'closed':
      raise ValueError("Job is already closed")

    batch_execution_data = self.get_batch_execution_data()

    # save into a variable since self.job gets updated in the process
    active_batch_qt = self.job.active_batch_qt
    completed_batch_qt = self.info.completed_batch_qt or active_batch_qt

    if completed_batch_qt <= 0:
      raise ValueError("Quantity cannot be zero or negative")

    is_next_batch_available = self.job.next_batch_available

    if (self.job.traceability_level is not None):
      # update batch serials data
      if (len(self.info.form_data) > 0):
        self.store_batch_data(self.convert_form_data(self.info.form_data))
      elif (len(batch_execution_data) > 0):
        self.store_batch_data(self.convert_batch_data(dict(batch_execution_data)))

      SerialBatchConfirmedEvent.create_as_child(self, dict(
        batch_key = self.info.active_batch_key,
        batch_execution_data = self.convert_batch_data(dict(batch_execution_data)),
        job = self.job,
        user_key = self.info.user_key
      ))

    self.info.completed_batch_key = self.job.active_batch_key
    self.info.completed_batch_qt = completed_batch_qt
    self.info.work_session_key = self.job.last_work_session_started

    WorkSessionClosedEvent.create_as_child(self, dict(
      work_session_end = self.info.timestamp,
      job_key = self.info.job_key
    ));

    # Complete batch
    self.tx.aql.execute(
      TraceabilityQueries.COMPLETE_BATCH, bind_vars=dict(
        batch_key=self.info.completed_batch_key,
        qt_pass=self.info.completed_batch_qt,
        end=self.info.timestamp
      )
    )

    #create production movement
    InventoryProducedEvent.create_as_child(self, dict(
      job_key = self.info.job_key,
      product_key = self.info.product_key,
      batch_key = self.info.active_batch_key,
      quantity = self.info.completed_batch_qt,
    ))

    #create consumption movement
    InventoryConsumedEvent.create_as_child(self, dict(
      job_key = self.info.job_key,
      product_key = self.info.product_key,
      batch_key = self.info.active_batch_key
   ))


    # Update job completed quantity as reference for methods being called later (e.g. create_batch)
    self.job.qt_completed += self.info.completed_batch_qt

    # NO REMAINING QUANTITY TO DO - LAST BATCH
    if self.job.qt_completed >= self.job.qt_planned: # No more pieces to work
      self.complete_job(self.job.qt_completed)
      self.response = dict(
        message = f"Batch {self.info.active_batch_key} and Job {self.info.job_key} completed.",
        job_data = self.job
      )

    # JOB HAS REMAINING QUANTITY
    else:
      new_progress = round(100 * self.job.qt_completed / self.job.qt_planned)

      job_update = dict(
        _key = self.info.job_key,
        active_batch_key = None,
        active_batch_qt = 0,
        qt_completed = self.job.qt_completed,
        qt_released = self.job.qt_completed,
        progress = new_progress,
        active = False
      )

      # Auto new batch ignored if serials must be selected for new batch. Clients must select new serials to start the new one
      # The batch_serials event property could be confused with the ones of the batch being declared.
      create_new_batch = (
        self.job.parameters.auto_new_batch
        and is_next_batch_available
        and not (self.job.traceability_level and not self.job.first_phase)
      )

      if create_new_batch:
        self.info.work_session_key = WorkSessionCreatedEvent.create_as_child(self, dict(
          job_key = self.info.job_key,
          batch_key = self.batch.key,
          work_order_key = self.info.work_order_key,
          phase_key = self.info.phase_key,
        ))
        job_update.update(dict(
          active_batch_qt = self.batch.qt_total,
          active_batch_key = self.batch.key,
          last_work_session_started = self.info.work_session_key,
          active = True
        ))

      # Update job qt_completed and progress
      self.job = Job(**self.tx.collection('Job').update(job_update, check_rev=False, return_new=True)['new'])

      # Must be done after new batch and session have been created, if they have to
      self.response = dict(
        message = f"Batch {self.info.active_batch_key} completed.",
        job_data = self.job,
        batch_data = dict(),
      )

      if create_new_batch:
        self.response['batch_data'] = self.get_batch_execution_data()
        new_job_data = self.tx.aql.execute(ProductionQueries.GET_WORKING_JOB_DATA, bind_vars=dict(job_key = self.info.job_key)).next()
        if ('wo_bom' in new_job_data):
          setattr(self.job, 'wo_bom', new_job_data['wo_bom'])

    if not self.job.first_phase:
      WIPRemovedEvent.create_as_child(self, dict(
        job_key=self.info.job_key,
        phase_key=self.info.phase_key,
        work_order_key=self.info.work_order_key,
        quantity=completed_batch_qt,
        batch_key=self.info.new_batch_key
      ))

    # is next_phase generate a WIP record and update job input availability state
    if not self.job.last_phase:
      WIPDeclaredEvent.create_as_child(self, dict(
        job_key=self.info.job_key,
        phase_key=self.info.phase_key,
        work_order_key=self.info.work_order_key,
        quantity=completed_batch_qt,
        batch_key=self.info.new_batch_key,
        product_key=self.info.product_key,
      ))
    else:
      if getattr(self.job, 'traceability_level', None) is not None:
        # update batch serials data
        SerialReleasedEvent.create_as_child(self, dict(
          batch_key = self.info.active_batch_key,
          batch_execution_data = self.convert_batch_data(dict(batch_execution_data)),
          user_key = self.info.user_key
        ))

  def store_batch_data(self, batch_execution_data):
    if (len(batch_execution_data) > 0):
      SerialDataUpdatedEvent.create_as_child(self, dict(
        batch_key = self.info.active_batch_key,
        batch_execution_data = batch_execution_data,
        user_key = self.info.user_key
      ))


  def process_inventory_changes(self):
    # Check if warehouse management is enabled
    warehouse_enabled = self.tx.collection('Config').get('enable_inventory_management') or False
    if not warehouse_enabled:
      return

    # Generate production movement
    output_qt = self.info.completed_batch_qt

    product_data = self.tx.collection('Product').get(self.job.product_key)
    production_position_key = product_data.get('default_production_position', None)
    if production_position_key is None:
      production_position_key = self.tx.collection('Config').get('default_production_position').get('value', 'IN')

    InventoryChangedEvent.create_as_child(self, dict(
      position_to = f'Position/{production_position_key}',
      product_key = self.job.product_key,
      quantity = output_qt,
      type = InventoryMovementType.PRODUCTION,
    ))

    # Get phase bom and generate consumption movements
    bom = [line for line in self.job.wo_bom if line['phase_key'] == self.info.phase_key]
    default_consumption_position = self.tx.collection('Config').get('default_consumption_position').get('value', 'IN')

    for line in bom:
      component_data = self.tx.collection('Product').get(line['component_key'])
      consumption_position_key = component_data.get('default_consumption_position', default_consumption_position)
      InventoryChangedEvent.create_as_child(self, dict(
        position_from = f'Position/{consumption_position_key}',
        product_key = line['component_key'],
        quantity = line['qt'] * output_qt,
        type = InventoryMovementType.CONSUMPTION,
      ))
