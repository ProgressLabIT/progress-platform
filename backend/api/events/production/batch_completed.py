
from events.inventory.movement_completed import MovementCompletedEvent
from events.production.base_production import BaseProductionEvent
from events.production.batch_created import BatchCreatedEvent
from events.production.job_closed import JobClosedEvent
from events.serial.serial_batch_confirmed import SerialBatchConfirmedEvent
from events.serial.serial_data_updated import SerialDataUpdatedEvent
from events.serial.serial_released import SerialReleasedEvent
from events.wip.wip_declared import WIPDeclaredEvent
from events.wip.wip_removed import WIPRemovedEvent
from events.work_session.work_session_closed import WorkSessionClosedEvent
from events.work_session.work_session_created import WorkSessionCreatedEvent
from models.event import EventInfoModel, EventType
from models.form import FormFieldValue, SerialFormFieldValue
from models.inventory import InventoryMovementReferences, InventoryMovementType
from models.production import Job
from models.traceability import *
from utils.production import Queries as ProductionQueries
from utils.traceability import Queries as TraceabilityQueries


class BatchCompletedEvent(BaseProductionEvent):
  class InfoModel(EventInfoModel):
    active_batch_key: str
    completed_batch_qt: int
    form_data: list[FormFieldValue] | None = None
    serial_data: list[SerialFormFieldValue] | None = None


  @classmethod
  def get_event_type(cls):
    return EventType.BATCH_COMPLETED

  def apply(self):
    self.batch = Batch(**self.tx.collection('Batch').get(self.info.active_batch_key))
    self.info.job_key = self.batch.job_key
    self._get_job_data()

    if self.job.stage == 'closed':
      raise ValueError("Job is already closed")

    batch_execution_data = self.get_batch_execution_data()

    # save into a variable since self.job gets updated in the process
    active_batch_qt = self.job.active_batch_qt
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

    self.info.active_batch_key = self.job.active_batch_key
    self.info.completed_batch_qt = self.batch.qt_total

    WorkSessionClosedEvent.create_as_child(self, dict(
      work_session_end = self.info.timestamp,
      work_session_key = self.info.work_session_key
    ))

    # Complete batch
    self.tx.aql.execute(
      TraceabilityQueries.COMPLETE_BATCH, bind_vars=dict(
        batch_key=self.info.active_batch_key,
        qt_pass=self.info.completed_batch_qt,
        end=self.info.timestamp
      )
    )

    self._process_inventory_changes()

    # Update job completed quantity as reference for methods being called later (e.g. create_batch)
    self.job.qt_completed += self.info.completed_batch_qt

    # NO REMAINING QUANTITY TO DO - LAST BATCH
    if self.job.qt_completed >= self.job.qt_planned: # No more pieces to work
      self.job = JobClosedEvent.create_as_child(self, dict(
        job_key = self.info.job_key,
        completed_qt = self.job.qt_completed,
      ))
      self.response = dict(
        message = f"Batch {self.info.active_batch_key} and Job {self.info.job_key} completed.",
        job_data = self.job
      )
      return

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
        new_batch = BatchCreatedEvent.create_as_child(self, dict(
          # batch_serials is not needed since auto new batch works only without serials
          job_key = self.info.job_key,
          work_order_key = self.info.work_order_key,
          phase_key = self.info.phase_key,
          product_key = self.info.product_key,
        ))
        new_work_session = WorkSessionCreatedEvent.create_as_child(self, dict(job_key = self.info.job_key))

        job_update.update(dict(
          active_batch_qt = new_batch.qt_total,
          active_batch_key = new_batch.key,
          last_work_session_started = new_work_session.key,
          active = True
        ))

      # Update job qt_completed and progress
      self.job = Job(**self.tx.collection('Job').update(job_update, check_rev=False, return_new=True)['new'])

      # Must be done after new batch and session have been created, if they have to
      self.response = dict(
        message = f"Batch {self.batch.key} completed.",
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
        quantity=self.info.completed_batch_qt,
      ))

    # is next_phase generate a WIP record and update job input availability state
    if not self.job.last_phase:
      WIPDeclaredEvent.create_as_child(self, dict(
        job_key=self.info.job_key,
        batch_key=self.info.active_batch_key,
        quantity=self.info.completed_batch_qt,
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


  # ===================================================================
  # GENERATE PRODUCTION/CONSUMPTION MOVEMENTS
  # ===================================================================

  def _process_inventory_changes(self):
    # Check if warehouse management is enabled
    warehouse_enabled = self.tx.collection('Config').get('enable_inventory_management')
    if warehouse_enabled is None or not warehouse_enabled.get('value', False):
      return

    references = InventoryMovementReferences(
      work_order_key = self.info.work_order_key,
      job_key = self.info.job_key,
      batch_key = self.info.active_batch_key,
    )

    # Generate production movement
    output_qt = self.info.completed_batch_qt
    production_position_key = self.tx.collection('WorkOrder').get(self.info.work_order_key).get('output_position_key', 'IN')

    MovementCompletedEvent.create_as_child(self, dict(
      position_to = production_position_key,
      product_key = self.job.product_key,
      qt_confirmed = output_qt,
      qt_planned = output_qt,
      movement_type = InventoryMovementType.PRODUCTION,
      references = references,
    ))

    # Get phase bom and generate consumption movements
    bom = [line for line in self.job.job_bom if line.phase_key == self.info.phase_key]

    for line in bom:
      MovementCompletedEvent.create_as_child(self, dict(
        position_from = line.consumption_options.consumption_position_key,
        product_key = line.component_key,
        qt_confirmed = line.qt * output_qt,
        qt_planned = line.qt * output_qt,
        movement_type = InventoryMovementType.CONSUMPTION,
        references = references,
      ))
