import traceback
import json

from fastapi.encoders import jsonable_encoder
from events.base import BaseEvent
from events.shared import EventMeta

from commons.models.traceability import *
from models.production import Job, WorkStatus
from commons.models.product import TraceabilityLevel

from utils.exceptions import JobIsStartedError, JobHasNoAssigneeError, WipNotAvailableError
from utils.production import Queries as ProductionQueries, update_target_queue
from utils.traceability import Queries as TraceabilityQueries
from commons.utils.db import model_to_db_dict

from commons.models.serial import Serial, SerialEvent, SerialEventType
from commons.models.form import SerialFormFieldValue

from commons.utils.serial import Queries as SerialQueries

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
    'WorkSession'
  ]

  production_post_processing = ['update_job_last_online', 'update_work_order']


  # EVENTS DEFINITION ========================
  JOB_STARTED = EventMeta(
    collections=production_collections,
    action='start_job',
    post_processing=production_post_processing
  )

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

  JOB_RESUMED = EventMeta(
    collections=production_collections,
    action='resume_job',
    post_processing=production_post_processing
  )

  JOB_BACK_ONLINE = EventMeta(
    collections=production_collections,
    action='restore_work_session',
    post_processing=production_post_processing
  )

  STEP_COMPLETED = EventMeta(
    collections=production_collections,
    action='complete_step',
    post_processing=production_post_processing
  )

  STEP_QUANTITY_CHANGED = EventMeta(
    collections=production_collections,
    action='step_quantity_changed',
    post_processing=production_post_processing
  )

  ACTIVE_BATCH_CHANGED = EventMeta(
    collections=production_collections,
    action="update_active_batch",
    post_processing=["update_job_last_online"]
  )

  BATCH_COMPLETED = EventMeta(
    collections=production_collections,
    action='complete_batch',
    post_processing=production_post_processing
  )

  SERIAL_CREATED = EventMeta(
    collections=production_collections,
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
    finalize_wo_serial,
    udpate_batch_serial_data
  )

  from .batch import(
    create_batch,
    send_link_batch_serial_event,
    get_active_batch,
    get_batch_step_done_count,
    get_batch_execution_data,
    current_step_was_last_to_do
  )
 

  # ===================================================================
  # WIP
  # ===================================================================

  def declare_wip(self):
    if not self.job:
      self.get_job_data()

    self.info.next_phase_key = self.tx.aql.execute(
      TraceabilityQueries.GET_NEXT_PHASE_IN_WORK_ORDER,
      bind_vars=dict(wo_key=self.info.work_order_key, phase_key=self.info.phase_key)
    ).next()

    # Prepare new wip data and make a single call to the database with insert_many
    # Insert many requires passing dicts (does not use default db serializer)
    if getattr(self.job, 'traceability_level', None):
      bind_vars = dict(batch_key = self.info.completed_batch_key)
      serial_to_declare_cursor = self.tx.aql.execute(SerialQueries.GET_BATCH_SERIALS, bind_vars=bind_vars)
      serial_to_declare = [Serial(**serial) for serial in serial_to_declare_cursor]
      
      new_wip_data = [dict(
        _from = f'Phase/{self.info.phase_key}',
        _to = f'Phase/{self.info.next_phase_key}',
        batch_key = self.info.completed_batch_key,
        wo_key = self.info.work_order_key,
        product_key = self.info.product_key,
        quantity = 1,
        serial_key = s.key
      ) for s in serial_to_declare]

    else:
      new_wip_data = [dict(
        _from=f'Phase/{self.info.phase_key}',
        _to=f'Phase/{self.info.next_phase_key}',
        batch_key=self.info.completed_batch_key,
        wo_key=self.info.work_order_key,
        product_key=self.info.product_key,
        quantity=self.info.completed_batch_qt
      )]

    self.tx.collection('wip').insert_many(new_wip_data)

    self.update_wip_availability_for_phases(phase_keys=[self.info.next_phase_key])

  def remove_wip(self, quantity):
    """
    Remove upstream wip records related to the completed batch
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
      if quantity >= wip.quantity:
        # Remove entire wip for job
        self.tx.collection('wip').delete(wip.key)
        quantity -= wip.quantity
        if quantity == 0:
          break
      else:
        # Partially remove wip by reducing the quantity
        unbooking_percentage = quantity / wip.quantity
        self.tx.collection('wip').update(dict(
          _key=wip.key,
          quantity=wip.quantity - quantity,
          value=wip.value * (1 - unbooking_percentage)
        ))
        quantity = 0
        break

    if quantity > 0:
      raise WipNotAvailableError(f"Not enough booked wip to remove. Needed { quantity } more")

  def book_wip_serials(self):
    # Reset job/batch links in wip and batch_serial so that it works
    # when serials are changed or the quantity reduced
    reset_wip_match = dict(_to=f'Job/{self.info.job_key}')
    reset_wip_update = dict(_to=f'Phase/{self.info.phase_key}', active=False)
    self.tx.collection('wip').update_match(reset_wip_match, reset_wip_update)

    reset_batch_serial_match = dict(_from=f'Batch/{self.batch.key}')
    self.tx.collection('batch_serial').delete_match(reset_batch_serial_match)

    # Book and link to batch new serials, checking they are all available
    free_wip_cursor = self.tx.aql.execute(
      TraceabilityQueries.RETRIEVE_AVAILABLE_WIP,
      bind_vars=dict(phase_key=self.info.phase_key, wo_key=self.info.work_order_key)
    )
    free_wip_serials = [WIP(**wip).serial_key for wip in free_wip_cursor]

    serials_to_update = []
    unavailable_serials = []
    for serial_key in self.info.batch_serials:
      target = serials_to_update if serial_key in free_wip_serials else unavailable_serials
      target.append(serial_key)

    if len(unavailable_serials):
      raise WipNotAvailableError(f'Serials {unavailable_serials} are not available')
    else:
      self.tx.aql.execute(
        SerialQueries.BOOK_SERIAL_WIP,
        bind_vars=dict(
          serial_keys=serials_to_update,
          job_key=self.info.job_key
        )
      )
      self.send_link_batch_serial_event()
    
    self.update_wip_availability_for_phases(phase_keys=[self.info.phase_key])


  def book_wip(self, quantity) -> None:
    if quantity == 0:
      raise ValueError("Cannot book a quantity of zero")

    # Traceability Enabled -> Book specific serials in case of phases following the first
    if getattr(self.job, 'traceability_level', None) and self.info.batch_serials != None and not self.job.first_phase:
      if len(self.info.batch_serials) == quantity:
        self.book_wip_serials()
      else:
        raise ValueError("The number of serials provided does not match the requested quantity")
    
    # Traceability 
    else:
      free_wips_cursor = self.tx.aql.execute(
        TraceabilityQueries.RETRIEVE_AVAILABLE_WIP,
        bind_vars=dict(phase_key=self.info.phase_key, wo_key=self.info.work_order_key)
      )
      free_wips = [WIP(**wip) for wip in free_wips_cursor]
      free_wips = sorted(free_wips, key=lambda wip: wip.quantity)

      # TODO: change using while loop like in events/admin.py@override_progress
      for wip in free_wips:
        if quantity >= wip.quantity:
          # Book entire batch for job
          self.tx.collection('wip').update(dict(
            _key = wip.key,
            _to = f'Job/{self.info.job_key}',
            active = True
          ))
          quantity -= wip.quantity
          if quantity == 0:
            break

        else:
          # Partially book batch for job
          booking_percentage = quantity / wip.quantity
          self.tx.collection('wip').update(dict(
            _key=wip.key,
            quantity=wip.quantity - quantity,
            value=wip.value * (1 - booking_percentage)
          ))

          # Add wip record with partially booked batch
          new_wip = WIP(
            from_doc=wip.from_doc,
            to_doc=f'Job/{self.info.job_key}',
            wo_key=wip.wo_key,
            batch_key=wip.batch_key,
            product_key=wip.product_key,
            quantity=quantity,
            value=wip.quantity * booking_percentage,
            active=True
          )
          self.tx.collection('wip').insert(new_wip)
          quantity = 0
          break

      if quantity > 0:
        raise WipNotAvailableError(f"Not enough free wip available to book. Needed { quantity } more")

    # Update input availability for jobs in this phase
    # Execute both with and without traceability
    self.update_wip_availability_for_phases(phase_keys=[self.info.phase_key])
    

  def unbook_wip(self, quantity):
    if quantity == 0:
      return

    booked_wips_cursor = self.tx.collection('wip').find(dict(
      _to=f'Job/{self.info.job_key}',
    ))
    booked_wips = [WIP(**wip) for wip in booked_wips_cursor]
    booked_wips = sorted(booked_wips, key=lambda wip: wip.quantity)

    for wip in booked_wips:
      if quantity >= wip.quantity:
        # Unbook entire batch for job
        self.tx.collection('wip').update(dict(
          _key = wip.key,
          _to = f'Phase/{self.info.phase_key}'
        ))
        quantity -= wip.quantity
        if quantity == 0:
          break
      else:
        # Partially unbook batch for job
        unbooking_percentage = quantity / wip.quantity
        self.tx.collection('wip').update(dict(
          _key=wip.key,
          quantity=wip.quantity - quantity,
          value=wip.value * (1 - unbooking_percentage)
        ))

        # Add free wip record with partially unbooked batch
        new_wip = WIP(
          from_doc=wip.from_doc,
          to_doc=f'Phase/{self.info.phase_key}',
          wo_key=wip.wo_key,
          batch_key=wip.batch_key,
          product_key=wip.product_key,
          quantity=quantity,
          value=wip.quantity * unbooking_percentage,
          active=True
        )
        self.tx.collection('wip').insert(new_wip)
        quantity = 0
        break

    if quantity > 0:
      raise WipNotAvailableError(f"Not enough booked wip available to unbook. Needed { quantity } more")

    # Update input availability for jobs in this phase
    self.update_wip_availability_for_phases(phase_keys=[self.info.phase_key])


  def update_wip_availability_for_phases(self, phase_keys: list[str]):
    self.tx.aql.execute(
      TraceabilityQueries.UPDATE_NEXT_BATCH_AVAILABLE_STATE_FOR_JOBS_IN_PHASES,
      bind_vars=dict(wo_key=self.info.work_order_key, phase_keys=phase_keys)
    )

  # ===================================================================
  # Job
  # ===================================================================

  def set_job_active_state(self, active: bool):
    update_data = dict(
      _key=self.info.job_key,
      active=active
    )
    updated_job = self.tx.collection('Job').update(update_data, check_rev=False, return_new=True)['new']
    self.job = Job(**updated_job)


  def update_job_last_online(self):
    update_data = dict(
      _key=self.info.job_key,
      last_online=self.info.timestamp
    )
    self.tx.collection('Job').update(update_data)


  def get_job_data(self):
    job = self.tx.collection('Job').get(self.info.job_key)
    self.job = Job(**job)
    self.info.job_key = self.job.key
    self.info.work_order_key = self.job.wo_key
    self.info.phase_key = self.job.phase_key
    self.info.active_batch_key = self.job.active_batch_key


  def get_job_steps_count(self):
    return self.tx.aql.execute(
      """
      FOR job IN Job
        FILTER job._key == @job_key
        RETURN LENGTH(job.step_sequence)
      """,
      bind_vars=dict(job_key=self.info.job_key)
    ).next()


  # TODO: Use TraceabilityQueries.UPDATE_JOB_PROGRESS instead (?)
  def update_job_step_progress(self):
    if not self.job:
      self.get_job_data()

    current_batch_total_value = self.job.active_batch_qt / self.job.qt_planned

    steps_count = self.get_job_steps_count()
    step_progress_value = current_batch_total_value / steps_count
    step_done_count = self.get_batch_step_done_count()
    completed_qt_progress = self.job.qt_completed / self.job.qt_planned
    total_progress = completed_qt_progress + (step_progress_value * step_done_count)

    job_update=dict(
      _key = self.job.key,
      progress = round(total_progress * 100)
    )

    self.job = Job(**self.tx.collection('Job').update(job_update, return_new=True)['new'])


  def complete_job(self, completed_qt):
    # Close job
    # Query allows for single call to DB to get and update job data

    bind_vars=dict(
      job_key=self.info.job_key,
      stage=WorkStatus.CLOSED,
      notes="Job completed",
      qt_completed=completed_qt,
      end=self.info.timestamp,
    )
    completed_job = self.tx.aql.execute(
      TraceabilityQueries.COMPLETE_JOB,
      bind_vars=bind_vars
    ).next()

    self.job = Job(**completed_job)

    self.tx.aql.execute(
      ProductionQueries.REMOVE_JOB_FROM_QUEUE,
      bind_vars=dict(
        job_key=self.info.job_key,
        target_key=self.info.user_key
      )
    )


  ######################################################################
  # EVENT ACTIONS
  ######################################################################

  # ===================================================================
  #                 START JOB
  # ===================================================================

  def start_job(self):
    # Check job hasn't been started already
    self.get_job_data()
    if self.job.stage != WorkStatus.CREATED:
      raise JobIsStartedError('Job has already been started')

    # Check config for unassigned jobs
    show_unassigned_jobs_to_operators = self.tx.collection('Config').get('show_unassigned_jobs_to_operators')
    can_self_assign = show_unassigned_jobs_to_operators.get('value', True) if show_unassigned_jobs_to_operators is not None else True
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

  def pause_job(self):
    self.close_work_session(self.info.work_session_end)
    self.set_job_active_state(False)

  # ===================================================================
  #               RESUME JOB
  # ===================================================================

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

    if (step_data.form_data != None):
      if (self.job.traceability_level != None and self.job.traceability_level != TraceabilityLevel.NONE):
        # update batch serials data
        self.udpate_batch_serial_data(step_data.form_data)

    # if last step complete batch
    if (self.current_step_was_last_to_do()):
      self.complete_batch()

    # else update job step progress
    else:
      self.update_job_step_progress()
      self.response = dict(
        message = f"Step completed for batch {self.info.active_batch_key}",
        job_data = self.job,
        batch_data = self.get_batch_execution_data()
      )

  # ===================================================================
  #             UPDATE ACTIVE BATCH
  # ===================================================================

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
          if self.info.batch_serials is not None and len(self.info.batch_serials):
            self.book_wip_serials()
          else:
            raise ValueError("You must provide a list of serials to update the batch with")
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

  def complete_batch(self):
    if not hasattr(self, 'job'):
      self.get_job_data()

    if self.job.stage == 'closed':
      raise ValueError("Job is already closed")

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

    if (self.job.traceability_level != None and self.job.traceability_level != TraceabilityLevel.NONE):
      # update batch serials data
      self.finalize_batch_serial(completed_batch_qt)

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

    if not self.job.first_phase:
      self.remove_wip(completed_batch_qt)

    # is next_phase generate a WIP record and update job input availability state
    if not self.job.last_phase:
      self.declare_wip()
    else:
      if getattr(self.job, 'traceability_level', None) is not None:
        # update batch serials data
        self.finalize_wo_serial(completed_batch_qt)

# ===================================================================
#             END
# ===================================================================

