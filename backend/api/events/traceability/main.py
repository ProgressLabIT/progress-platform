import traceback
import json

from fastapi.encoders import jsonable_encoder
from events.base import BaseEvent
from events.shared import EventMeta

from models.traceability import *
from models.production import Job, WorkStatus
from models.product import TraceabilityLevel

from utils.exceptions import JobIsStartedError, JobHasNoAssigneeError, WipNotAvailableError
from utils.production import Queries as ProductionQueries, update_target_queue
from utils.traceability import Queries as TraceabilityQueries
from utils.db import model_to_db_dict

from models.serial import Serial, SerialEvent, SerialCommandType
from models.form import SerialFormFieldValue

from utils.serial import Queries as SerialQueries

from fastapi import HTTPException



class ProductionActivityEvent(BaseEvent):
  production_collections = [
    'Batch',
    'batch_serial',
    'Event',
    'Job',
    'Queue',
    'Serial',
    'StepExecutionData',
    'wip',
    'WorkOrder',
    'WorkSession',
    'contains'
  ]

  production_post_processing = ['update_job_last_online', 'update_work_order']

  SERIAL_CREATED = EventMeta(
    collections=['Counter', 'Serial'],
    action="create_serial"
  )

  SERIAL_UPDATED = EventMeta(
    collections=production_collections,
    action="update_serial"
  )

  SERIAL_DELETED = EventMeta(
    collections=production_collections,
    action="delete_serial"
  )

  SERIAL_LINKED = EventMeta(
    collections=production_collections,
    action="link_serial"
  )
  ######################################################################
  # HELPER METHODS (Updates to specific collections)
  ######################################################################

  from .worksession import (
    create_work_session,
    get_current_work_session,
    close_work_session
  )

  from .serial import(
    send_to_consumer,
    create_serial,
    link_serial,
    update_serial,
    delete_serial,
    create_batch_serial_records,
    finalize_batch_serial,
    store_form_data,
    store_batch_data,
    finalize_wo_serial,
    send_link_batch_serial_event
  )

  from .batch import(
    create_batch,
    get_active_batch,
    get_batch_step_done_count,
    get_batch_execution_data,
    current_step_was_last_to_do
  )

  from .wip import(
    declare_wip,
    remove_wip,
    book_wip_serials,
    book_wip,
    unbook_wip,
    update_wip_availability_for_phases
  )

  from .job import (
    set_job_active_state,
    update_job_last_online,
    get_job_data,
    get_job_steps_count,
    update_job_step_progress,
    complete_job
  )


  ######################################################################
  # EVENT ACTIONS
  ######################################################################

  # ===================================================================
  #                 START JOB
  # ===================================================================

  JOB_STARTED = EventMeta(
    collections=production_collections,
    action='start_job',
    post_processing=production_post_processing
  )

  def start_job(self):
    # Check job hasn't been started already
    self.get_job_data()
    if self.job.stage != WorkStatus.CREATED:
      raise JobIsStartedError('Job has already been started')

    # Check config for unassigned jobs
    show_unassigned_jobs_to_operators = self.tx.collection('Config').get('show_unassigned_jobs_to_operators')
    can_self_assign = show_unassigned_jobs_to_operators.get('value', True) if show_unassigned_jobs_to_operators is not None else True
    add_to_queue = False

    if self.job.assigned_to is None:
      if not can_self_assign:
        raise JobHasNoAssigneeError('Unassigned jobs cannot be worked on as config "show_unassigned_jobs_to_operators" is false')
      else:
        add_to_queue = True

    # Create new batch and store _key in Event.info
    self.create_batch()

    # Create new WorkSession and store _key in Event.info
    self.create_work_session()

    # Update WorkOrder status
    wo = self.get_work_order_data()

    stage = WorkStatus.STARTED

    if wo.status == WorkStatus.CREATED:
      wo.status = stage
      wo.start = self.info.timestamp
      wo_update = model_to_db_dict(wo)
      self.tx.collection('WorkOrder').update(wo_update)

    # Update job
    job_update=dict(
      _key = self.info.job_key,
      start = self.info.timestamp,
      stage = stage,
      last_work_session_started = self.info.work_session_key,
      active_batch_key = self.batch.key,
      active_batch_qt = self.batch.qt_total,
      active = True,
      assigned_to = self.info.user_key,
      last_online = self.info.timestamp
    )
    self.job = Job(**self.tx.collection('Job').update(job_update, return_new=True)['new'])

    if add_to_queue:
      update_target_queue(
        job_key = self.info.job_key,
        target_key = self.info.user_key,
        action = 'add',
        tx = self.tx
      )


    self.response = dict(
      message = f"Job {self.info.job_key} started",
      batch_data = self.get_batch_execution_data(),
      job_data = self.job
    )

  # ===================================================================
  #               PAUSE JOB
  # ===================================================================

  JOB_PAUSED = EventMeta(
    collections=production_collections,
    action='pause_job',
    post_processing=production_post_processing
  )

  JOB_PAUSED_OFFLINE = EventMeta(
    collections=production_collections,
    action='pause_job',
    post_processing=production_post_processing
  )

  def pause_job(self):
    self.close_work_session(self.info.work_session_end)
    self.set_job_active_state(False)

  # ===================================================================
  #               RESUME JOB
  # ===================================================================

  JOB_RESUMED = EventMeta(
    collections=production_collections,
    action='resume_job',
    post_processing=production_post_processing
  )

  def resume_job(self):
    self.get_job_data()

    # Create batch if none is active and store data for work session creation
    if self.job.active_batch_key:
      self.get_active_batch()
    else:
      self.create_batch()

    self.create_work_session()

    job_update=dict(
      _key = self.info.job_key,
      last_work_session_started = self.info.work_session_key,
      active=True
    )


    if not self.job.active_batch_key:
      job_update['active_batch_key'] = self.batch.key

    job_update['active_batch_qt'] = self.batch.qt_total

    self.job = Job(**self.tx.collection('Job').update(job_update, return_new=True)['new'])

    self.response = dict(
      message=f"Job {self.info.job_key} resumed",
      batch_data = self.get_batch_execution_data(),
      job_data = self.job
    )

  # ===================================================================
  #                 RESTORE WORK SESSION
  # ===================================================================

  JOB_BACK_ONLINE = EventMeta(
    collections=production_collections,
    action='restore_work_session',
    post_processing=production_post_processing
  )

  def restore_work_session(self):
    updated_work_session = dict(
      _key=self.info.work_session_key,
      active=True,
      end=None
    )
    self.work_session = self.tx.collection('WorkSession').update(
      updated_work_session,
      return_new=True
    )['new']

    # update job as active
    self.set_job_active_state(True)

    self.response = self.job

  # ===================================================================
  #                      COMPLETE STEP
  # ===================================================================

  STEP_COMPLETED = EventMeta(
    collections=production_collections + ['Counter'],
    action='complete_step',
    post_processing=production_post_processing
  )

  def complete_step(self):
    self.get_job_data()
    self.get_active_batch()

    # Save current work session and batch keys in Event.info
    if not self.info.work_session_key:
      self.work_session = self.get_current_work_session()
      self.info.work_session_key = self.work_session.key


    # Create StepExecutionData record
    step_data = StepExecutionData(**vars(self.info))
    step_data.batch_key = self.info.active_batch_key
    step_data.completed = self.info.timestamp
    step_data.status = StepStatus.DONE
    self.tx.collection('StepExecutionData').insert(step_data)

    #if (step_data.form_data != None):
    #  if (self.job.traceability_level is not None):
    #    # update batch serials data
    #    self.udpate_batch_serial_data(step_data.form_data)

    # if last step complete batch
    if (self.current_step_was_last_to_do()):
      self.complete_batch()

    # else update job step progress
    else:
      self.update_job_step_progress()
      new_job_data = self.tx.aql.execute(ProductionQueries.GET_WORKING_JOB_DATA, bind_vars=dict(job_key = self.info.job_key)).next()
      if ('wo_bom' in new_job_data):
        setattr(self.job, 'wo_bom', new_job_data['wo_bom'])

      self.response = dict(
        message = f"Step completed for batch {self.info.active_batch_key}",
        job_data = self.job,
        batch_data = self.get_batch_execution_data()
      )

  # ===================================================================
  #                      EDIT STEP DATA
  # ===================================================================

  STEP_EDITED = EventMeta(
    collections=production_collections + ['Counter'],
    action='edit_step',
    post_processing=production_post_processing
  )

  def edit_step(self):
    self.get_job_data()
    self.get_active_batch()

    # Save current work session and batch keys in Event.info
    if not self.info.work_session_key:
      self.work_session = self.get_current_work_session()
      self.info.work_session_key = self.work_session.key


    # Create StepExecutionData record
    step_data = StepExecutionData(**vars(self.info))

    match = dict(job_key = step_data.job_key, step_key = step_data.step_key)
    update = dict(form_data = step_data.form_data, modified = self.info.timestamp)

    self.tx.collection('StepExecutionData').update_match(match, update)


    self.response = dict(
      message = f"Step edited for batch {self.info.active_batch_key}",
      job_data = self.job,
      batch_data = self.get_batch_execution_data()
    )


  # ===================================================================
  #             UPDATE ACTIVE BATCH
  # ===================================================================

  ACTIVE_BATCH_CHANGED = EventMeta(
    collections=production_collections,
    action="update_active_batch",
    post_processing=["update_job_last_online"]
  )

  def update_active_batch(self):
    self.get_job_data()
    self.get_active_batch()

    if not self.info.work_session_key:
      self.work_session = self.get_current_work_session()
      self.info.work_session_key = self.work_session.key

    active_batch_qt_delta = self.info.new_active_batch_qt - self.job.active_batch_qt

    if active_batch_qt_delta == 0 and not len(self.info.batch_serials):
      raise ValueError("Active batch quantity already matches the quantity requested")

    else:
      if self.job.traceability_level:
        if self.job.first_phase:
          # Create or delete batch_serial records if necessary
          # TODO: Refactor to use serial service
          #
          # JUST IN CASE the batch serials do not match the active quantity
          # ensure we're removing the right number of serials to get to the derised quantity
          batch_serials_qt = self.tx.aql.execute(
            SerialQueries.GET_BATCH_SERIALS,
            bind_vars = dict(batch_key = self.batch.key),
            count = True
          ).count()

          serials_delta = self.info.new_active_batch_qt - batch_serials_qt

          if serials_delta > 0:
            self.create_batch_serial_records(quantity=serials_delta)
          else:
            bind_vars = dict(
              batch_key = self.batch.key,
              to_delete = abs(serials_delta)
            )
            cursor = self.tx.aql.execute(
              SerialQueries.DELETE_BATCH_SERIALS,
              bind_vars=bind_vars
            )
            # TODO: Use named graph with auto deletion of edges to avoid the following
            self.tx.aql.execute(SerialQueries.CLEANUP_SERIAL_BATCH_LINKS)

        # Has serials but not first phase
        else:
          if self.info.batch_serials is not None and len(self.info.batch_serials) == self.info.new_active_batch_qt:
            self.book_wip_serials()
          else:
            raise ValueError(f"The serials provided do not match the update requested. New qt: {self.info.new_active_batch_qt}. Serials provided: {self.info.batch_serials}")
      # No serial, only update batch quantity
      else:
        if not self.job.first_phase:
          if active_batch_qt_delta > 0:
            self.book_wip(active_batch_qt_delta)
          else: # active_batch_qt_delta < 0:
            self.unbook_wip(abs(active_batch_qt_delta))
        # no else here, if first phase and no serial no need to manage other collections
        # just proceed with batch/job updates

    # Update Batch
    self.batch = Batch(**self.tx.collection('Batch').update(dict(
      _key=self.batch.key,
      qt_total=self.info.new_active_batch_qt
    ), return_new=True)['new'])

    # Update Job
    self.job = Job(**self.tx.collection('Job').update(dict(
      _key=self.job.key,
      active_batch_qt=self.info.new_active_batch_qt
    ), return_new=True)['new'])

    # Set response
    self.response = dict(
      message=f"Active batch { self.info.active_batch_key } has been correctly updated with quantity { self.info.new_active_batch_qt }",
      job_data=self.job,
      batch_data=self.get_batch_execution_data()
    )


  # ===================================================================
  #                   COMPLETE BATCH
  # ===================================================================


  BATCH_COMPLETED = EventMeta(
    collections=production_collections + ['Counter'],
    action='complete_batch',
    post_processing=production_post_processing
  )

  def complete_batch(self):
    if not hasattr(self, 'job'):
      self.get_job_data()

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
        bind_vars=dict(job_key=self.info.job_key)
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
          self.book_wip(free_wip_delta)
        elif free_wip_delta < 0:
          self.unbook_wip(abs(free_wip_delta))

      if (len(self.info.form_data) > 0):
        self.store_form_data(completed_batch_qt=completed_batch_qt, form_data=self.info.form_data)
      if (len(batch_execution_data) > 0):
        self.store_batch_data(completed_batch_qt=completed_batch_qt, batch_execution_data=batch_execution_data)

    elif (self.job.traceability_level is not None):
      # update batch serials data
      if (len(self.info.form_data) > 0):
        self.store_form_data(completed_batch_qt=completed_batch_qt, form_data=self.info.form_data)
      if (len(batch_execution_data) > 0):
        self.store_batch_data(completed_batch_qt=completed_batch_qt, batch_execution_data=batch_execution_data)
      self.finalize_batch_serial(completed_batch_qt=completed_batch_qt, batch_execution_data=batch_execution_data)

    self.info.completed_batch_key = self.job.active_batch_key
    self.info.completed_batch_qt = completed_batch_qt
    self.info.work_session_key = self.job.last_work_session_started

    self.close_work_session()

    # Complete batch
    self.tx.aql.execute(
      TraceabilityQueries.COMPLETE_BATCH, bind_vars=dict(
        batch_key=self.info.completed_batch_key,
        qt_pass=self.info.completed_batch_qt,
        end=self.info.timestamp
      )
    )

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
        self.create_batch()
        job_update['active_batch_key'] = self.batch.key
        job_update['active_batch_qt'] = self.batch.qt_total
        self.create_work_session()
        job_update['last_work_session_started'] = self.info.work_session_key
        job_update['active'] = True

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
      self.remove_wip(completed_batch_qt)

    # is next_phase generate a WIP record and update job input availability state
    if not self.job.last_phase:
      self.declare_wip()
    else:
      if getattr(self.job, 'traceability_level', None) is not None:
        # update batch serials data
        self.finalize_wo_serial(batch_execution_data=batch_execution_data)

# ===================================================================
#             END
# ===================================================================

