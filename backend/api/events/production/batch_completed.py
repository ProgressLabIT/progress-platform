from events import EventManager, SerialDataUpdated, SerialBatchConfirmed, EventType, SerialReleased
from events.serial.serial_batch_confirmed import SerialBatchConfirmedModel
from events.serial.serial_released import SerialReleasedModel
from events.production.base_production import BaseProduction, BaseProductionModel
from models.traceability import *
from models.production import Job
from utils.exceptions import WipNotAvailableError
from utils.production import Queries as ProductionQueries
from utils.traceability import Queries as TraceabilityQueries
from events.event_model import EventModel
from events.event_type import EventType
from events.serial.serial_data_updated import SerialDataUpdatedModel
from events.work_session.work_session_closed import WorkSessionClosedModel
from events.wip.wip_declared import WIPDeclaredModel
from events.wip.wip_removed import WIPRemovedModel
from events.wip.wip_unbooked import WIPUnbookedModel
from events.batch.batch_created import BatchCreatedModel
from events.work_session.work_session_created import WorkSessionCreatedModel
from events.wip.wip_booked import WIPBookedModel

class BatchCompletedModel(BaseProductionModel):
  event_type: str = EventType.BATCH_COMPLETED.name

class BatchCompleted(BaseProduction):
  event_data: BatchCompletedModel

  def set_model(self, base_model: EventModel):
    self.event_data = BatchCompletedModel(**base_model.model_dump())

  from events.production.commons.serial import(
    convert_form_data,
    convert_batch_data,
    _convert_field,
    _convert_form_field
  )

  def apply(self):
    self._get_job_data()

    if self.job.stage == 'closed':
      raise ValueError("Job is already closed")

    batch_execution_data = self.get_batch_execution_data()

    # save into a variable since self.job gets updated in the process
    active_batch_qt = self.job.active_batch_qt
    completed_batch_qt = self.event_data.completed_batch_qt or active_batch_qt

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
          EventManager.notify_event(self, WIPBookedModel(
            job_key=self.event_data.job_key,
            phase_key=self.event_data.phase_key,
            work_order_key=self.event_data.work_order_key,
            quantity=free_wip_delta,
            batch_key=self.event_data.new_batch_key
          ))
        elif free_wip_delta < 0:
          EventManager.notify_event(self, WIPUnbookedModel(
            job_key=self.event_data.job_key,
            phase_key=self.event_data.phase_key,
            work_order_key=self.event_data.work_order_key,
            quantity=abs(free_wip_delta),
            batch_key=self.event_data.new_batch_key
          ))

      if (len(self.form_data) > 0):
        self.store_batch_data(self.convert_form_data(self.form_data))
      elif (len(batch_execution_data) > 0):
        self.store_batch_data(self.convert_batch_data(dict(batch_execution_data)))

    elif (self.job.traceability_level is not None):
      # update batch serials data
      if (len(self.event_data.form_data) > 0):
        self.store_batch_data(self.convert_form_data(self.event_data.form_data))
      elif (len(batch_execution_data) > 0):
        self.store_batch_data(self.convert_batch_data(dict(batch_execution_data)))

      EventManager.notify_event(self, SerialBatchConfirmedModel(
        batch_key = self.event_data.active_batch_key,
        batch_execution_data = self.convert_batch_data(dict(batch_execution_data)),
        job = self.job,
        user_key = self.event_data.user_key
      ))

    self.event_data.completed_batch_key = self.job.active_batch_key
    self.event_data.completed_batch_qt = completed_batch_qt
    self.event_data.work_session_key = self.job.last_work_session_started

    EventManager.notify_event(self, WorkSessionClosedModel(
      work_session_end = self.event_data.work_session_end,
      job_key = self.event_data.job_key
    ));

    # Complete batch
    self.tx.aql.execute(
      TraceabilityQueries.COMPLETE_BATCH, bind_vars=dict(
        batch_key=self.event_data.completed_batch_key,
        qt_pass=self.event_data.completed_batch_qt,
        end=self.event_data.timestamp
      )
    )

    # Update job completed quantity as reference for methods being called later (e.g. create_batch)
    self.job.qt_completed += self.event_data.completed_batch_qt

    # NO REMAINING QUANTITY TO DO - LAST BATCH
    if self.job.qt_completed >= self.job.qt_planned: # No more pieces to work
      self.complete_job(self.job.qt_completed)
      self.set_response(dict(
        message = f"Batch {self.event_data.active_batch_key} and Job {self.event_data.job_key} completed.",
        job_data = self.job
      ))

    # JOB HAS REMAINING QUANTITY
    else:
      new_progress = round(100 * self.job.qt_completed / self.job.qt_planned)

      job_update = dict(
        _key = self.event_data.job_key,
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
        self.batch = EventManager.notify_event(self, BatchCreatedModel(
          job_key = self.event_data.job_key,
          work_order_key = self.event_data.work_order_key,
          phase_key = self.event_data.phase_key,
          batch_serials = self.event_data.batch_serials,
          product_key = self.event_data.product_key,
        ))['new_batch_out']
        job_update['active_batch_key'] = self.batch.key
        job_update['active_batch_qt'] = self.batch.qt_total
        self.event_data.work_session_key = EventManager.notify_event(self, WorkSessionCreatedModel(
          job_key = self.event_data.job_key,
          batch_key = self.batch.key,
          work_order_key = self.event_data.work_order_key,
          phase_key = self.event_data.phase_key,
        ))['work_session_key']
        job_update['last_work_session_started'] = self.event_data.work_session_key
        job_update['active'] = True

      # Update job qt_completed and progress
      self.job = Job(**self.tx.collection('Job').update(job_update, check_rev=False, return_new=True)['new'])

      # Must be done after new batch and session have been created, if they have to
      self.set_response(dict(
        message = f"Batch {self.event_data.active_batch_key} completed.",
        job_data = self.job,
        batch_data = dict(),
      ))

      if create_new_batch:
        self.get_response()['batch_data'] = self.get_batch_execution_data()
        new_job_data = self.tx.aql.execute(ProductionQueries.GET_WORKING_JOB_DATA, bind_vars=dict(job_key = self.event_data.job_key)).next()
        if ('wo_bom' in new_job_data):
          setattr(self.job, 'wo_bom', new_job_data['wo_bom'])

    if not self.job.first_phase:
      EventManager.notify_event(self, WIPRemovedModel(
        job_key=self.event_data.job_key,
        phase_key=self.event_data.phase_key,
        work_order_key=self.event_data.work_order_key,
        quantity=completed_batch_qt,
        batch_key=self.event_data.new_batch_key
      ))

    # is next_phase generate a WIP record and update job input availability state
    if not self.job.last_phase:
      EventManager.notify_event(self, WIPDeclaredModel(
        job_key=self.event_data.job_key,
        phase_key=self.event_data.phase_key,
        work_order_key=self.event_data.work_order_key,
        quantity=completed_batch_qt,
        batch_key=self.event_data.new_batch_key,
        product_key=self.event_data.product_key,
      ))
    else:
      if getattr(self.job, 'traceability_level', None) is not None:
        # update batch serials data
        EventManager.notify_event(self, SerialReleasedModel(
          batch_key = self.event_data.active_batch_key,
          batch_execution_data = self.convert_batch_data(dict(batch_execution_data)),
          user_key = self.event_data.user_key
        ))

  def store_batch_data(self, batch_execution_data):
    if (len(batch_execution_data) > 0):
      EventManager.notify_event(self, SerialDataUpdatedModel(
        batch_key = self.event_data.active_batch_key,
        batch_execution_data = batch_execution_data,
        user_key = self.event_data.user_key
      ))
