from events import SerialDataUpdated, SerialBatchConfirmed, SerialReleased
from events.serial.serial_batch_confirmed import SerialBatchConfirmedModel
from events.serial.serial_released import SerialReleasedModel
from events.production.base_production import BaseProductionEvent, BaseProductionModel
from models.traceability import *
from models.production import Job
from utils.exceptions import WipNotAvailableError
from utils.production import Queries as ProductionQueries
from utils.traceability import Queries as TraceabilityQueries
from models.event import EventModel
from models.event import EventType
from events.serial.serial_data_updated import SerialDataUpdatedModel
from events.work_session.work_session_closed import WorkSessionClosedEvent
from events.wip.wip_declared import WIPDeclaredModel
from events.wip.wip_removed import WIPRemovedModel
from events.wip.wip_unbooked import WIPUnbookedModel
from events.inventory.movement_created import MovementCreatedModel
from events.work_session.work_session_created import WorkSessionCreatedEvent
from events.wip.wip_booked import WIPBookedModel
from models.inventory import InventoryMovementType, MovementStatus
from events.inventory.inventory_produced import InventoryProducedModel
from events.inventory.inventory_consumed import InventoryConsumedModel
class BatchCompletedModel(BaseProductionModel):
  event_type: str = EventType.BATCH_COMPLETED.name

class BatchCompleted(BaseProductionEvent):
  event_data: BatchCompletedModel

  def set_model(self, base_model: EventModel):
    self.info = BatchCompletedModel(**base_model.model_dump())

  from events.production.commons.serial import(
    convert_form_data,
    convert_batch_data,
    _convert_form_field
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

    if not self.job.first_phase:
      # TODO: the book_wip method already raises an error if there's not enough available wip upstream.
      # Consider removing the check here if redundant
      wip = self.tx.aql.execute(
        TraceabilityQueries.GET_AVAILABLE_WIP_UPSTREAM_AND_DOWNSTREAM_OF_JOB,
        bind_vars=dict(job_key=self.job_key)
      ).next()

      free_wip_qt_upstream = sum(w['quantity'] for w in wip['upstream_free_wip'])
      max_declarable_qt = free_wip_qt_upstream + self.job.active_batch_qt

      if completed_batch_qt > max_declarable_qt:
        raise WipNotAvailableError("The previous phase has not made enough progress to make this change")
      if completed_batch_qt == max_declarable_qt:
        is_next_batch_available = False
        self.job.next_batch_available = False

      # If there is more or less free wip than the booked wip, book or unbook the difference
      if active_batch_qt != completed_batch_qt:
        booked_wip_quantity = active_batch_qt
        free_wip_delta = completed_batch_qt - booked_wip_quantity
        if free_wip_delta > 0:
          WIPBookedEvent.create_as_child(self, dict(
            job_key=self.info.job_key,
            phase_key=self.info.phase_key,
            work_order_key=self.info.work_order_key,
            quantity=free_wip_delta,
            batch_key=self.info.new_batch_key
          ))
        elif free_wip_delta < 0:
          WIPUnbookedEvent.create_as_child(self, dict(
            job_key=self.info.job_key,
            phase_key=self.info.phase_key,
            work_order_key=self.info.work_order_key,
            quantity=abs(free_wip_delta),
            batch_key=self.info.new_batch_key
          ))

      if (len(self.form_data) > 0):
        self.store_batch_data(self.convert_form_data(self.form_data))
      elif (len(batch_execution_data) > 0):
        self.store_batch_data(self.convert_batch_data(dict(batch_execution_data)))

    elif (self.job.traceability_level is not None):
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
      work_session_end = self.info.work_session_end,
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
      self.set_response(dict(
        message = f"Batch {self.info.active_batch_key} and Job {self.info.job_key} completed.",
        job_data = self.job
      ))

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
        job_update['active_batch_key'] = self.batch.key
        job_update['active_batch_qt'] = self.batch.qt_total
        self.info.work_session_key = WorkSessionCreatedEvent.create_as_child(self, dict(
          job_key = self.info.job_key,
          batch_key = self.batch.key,
          work_order_key = self.info.work_order_key,
          phase_key = self.info.phase_key,
        ))
        job_update['last_work_session_started'] = self.info.work_session_key
        job_update['active'] = True

      # Update job qt_completed and progress
      self.job = Job(**self.tx.collection('Job').update(job_update, check_rev=False, return_new=True)['new'])

      # Must be done after new batch and session have been created, if they have to
      self.set_response(dict(
        message = f"Batch {self.info.active_batch_key} completed.",
        job_data = self.job,
        batch_data = dict(),
      ))

      if create_new_batch:
        self.get_response()['batch_data'] = self.get_batch_execution_data()
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
