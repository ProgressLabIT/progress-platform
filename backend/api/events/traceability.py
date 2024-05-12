import traceback
import json

from fastapi.encoders import jsonable_encoder
from events.base import BaseEvent
from events.shared import EventMeta

from models.traceability import *
from models.production import Job, WorkStatus

from utils.exceptions import JobIsStartedError, JobHasNoAssigneeError, WipNotAvailableError
from utils.production import Queries as ProductionQueries, update_target_queue
from utils.traceability import Queries as TraceabilityQueries
from commons.utils.db import model_to_db_dict

from commons.kafka_utils.kafka_producer import KafkaProducer
from commons.models.serial import SerialWithLinks

from fastapi import HTTPException



class ProductionActivityEvent(BaseEvent):
  production_collections = [
    'Batch',
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

  ######################################################################
  # HELPER METHODS (Updates to specific collections)
  ######################################################################

  # ===================================================================
  # WorkSession
  # ===================================================================

  def create_work_session(self):
    # Close unallowed parallel work sessions
    bind_vars = dict(
      user_key = self.info.user_key,
      timestamp = self.info.timestamp
    )

    closed_sessions_cursor = self.tx.aql.execute(
      TraceabilityQueries.CLOSE_UNALLOWED_PARALLEL_WORK_SESSIONS,
      bind_vars=bind_vars
    )
    closed_sessions_jobs = [ws['job_key'] for ws in closed_sessions_cursor]
    if len(closed_sessions_jobs):
      self.tx.aql.execute(
        """
        FOR j IN Job
        FILTER j._key IN @jobs
        UPDATE j WITH { 'active': false } IN Job
        """,
        bind_vars=dict(jobs=closed_sessions_jobs)
      )

    # Create new work session
    new_work_session = self.tx.aql.execute(
      TraceabilityQueries.CREATE_WORK_SESSION, bind_vars=dict(
        job_key = self.job.key,
        batch_key = self.batch.key, # in self info can be under new_batch_key or active_batch_key, taking it from self.batch makes it more consistent.
        work_order_key = self.job.wo_key,
        phase_key = self.job.phase_key,
        product_key = self.job.product_key,
        user_key = self.info.user_key,
        user_session_key = self.info.user_session_key,
        start = self.info.timestamp,
      )
    ).next()
    self.work_session = WorkSession(**new_work_session)
    self.info.work_session_key = self.work_session.key


  def get_current_work_session(self):
    match=dict(
      job_key=self.info.job_key,
      active=True
    )
    data_from_db = self.tx.collection('WorkSession').find(match).next()
    work_session = WorkSession(**data_from_db)
    return work_session


  def close_work_session(self, end=None):
    if end == None:
      end = self.info.timestamp

    updated_work_session = WorkSession(**self.tx.aql.execute(
      TraceabilityQueries.CLOSE_WORK_SESSION, bind_vars = dict(
        job_key = self.info.job_key,
        end = end,
    )).next())

    self.work_session = updated_work_session
    self.info.work_session_key = updated_work_session.key

    return updated_work_session


  # ===================================================================
  # Serial
  # ===================================================================

  def create_serial(self):
    serial_data = jsonable_encoder(SerialWithLinks(**self.info.serial_data))
    serial_data['operation'] = 'CREATE'

    try:
      KafkaProducer.getInstance().produce_async(topic="serials", key=serial_data.get('_key'), value=json.dumps(serial_data))
      self.response = dict(
        message="Serial created correctly",
      )
    except Exception:
      raise HTTPException(
        status_code=500,
        detail=dict(
          message="There was an error creating the serial.",
          error=traceback.format_exc()
        )
      )

  def update_serial(self):
    serial_data = jsonable_encoder(SerialWithLinks(**self.info.serial_data))
    serial_data['operation'] = 'UPDATE'

    try:
      KafkaProducer.getInstance().produce_async(topic="serials", key=serial_data.get('_key'), value=json.dumps(serial_data))
      self.response = dict(
        message="Serial updated correctly",
      )
    except Exception:
      raise HTTPException(
        status_code=500,
        detail=dict(
          message="There was an error updating the serial.",
          error=traceback.format_exc()
        )
      )

  def delete_serial(self):
    serial_data = jsonable_encoder(SerialWithLinks(**self.info.serial_data))
    serial_data['operation'] = 'DELETE'

    try:
      KafkaProducer.getInstance().produce_async(topic="serials", key=serial_data.get('_key'), value=json.dumps(serial_data))
      self.response = dict(
        message="Serial deleted correctly",
      )
    except Exception:
      raise HTTPException(
        status_code=500,
        detail=dict(
          message="There was an error updating the serial.",
          error=traceback.format_exc()
        )
      )


  # def create_batch_serial_records(self):
  #   if not self.job:
  #     self.job = self.get_job_data()

  #   default_batch = self.job.parameters.production_batch_qt
  #   remaining_qt = self.job.qt_planned - self.job.qt_completed
  #   batch_qt = min([default_batch, remaining_qt])

  #   next_serial = self.tx.aql.execute(
  #     TraceabilityQueries.GET_NEXT_SERIAL_NUMBER_FOR_WORK_ORDER,
  #     bind_vars=dict(wo_key=self.info.work_order_key)
  #   ).next()

  #   batch_serials = range(next_serial, next_serial + batch_qt)

  #   serial_keys = [
  #     self.create_serial(counter=i, batch_key=self.info.active_batch_key)
  #     for i in batch_serials
  #   ]

  #   self.tx.collection('Batch').update(dict(
  #     _key=self.info.active_batch_key,
  #     serial_numbers=serial_keys
  #   ))



  # ===================================================================
  # Batch
  # ===================================================================

  def create_batch(self):
    if not hasattr(self, 'job'):
      self.get_job_data()

    default_batch_qt = self.job.parameters.production_batch_qt

    # qt_completed must include any update from the current event being recorded
    remaining_qt = self.job.qt_planned - self.job.qt_completed

    # if production_batch_qt is zero, use total remaining quantity
    if default_batch_qt == 0:
      batch_qt = remaining_qt
    # Do not consider production batch if remaining quantity is lower
    else:
      batch_qt = min([default_batch_qt, remaining_qt])

    # Book wip from buffer
    if not self.job.first_phase:
      self.book_wip(batch_qt)

    new_batch_in = Batch(
      job_key = self.info.job_key,
      phase_key = self.info.phase_key,
      work_order_key = self.info.work_order_key,
      qt_total = batch_qt,
      start = self.info.timestamp,
      active = True
    )

    new_batch_out = self.tx.collection('Batch').insert(new_batch_in, return_new=True)['new']

    self.batch = Batch(**new_batch_out)
    self.info.new_batch_key = self.batch.key


  def get_active_batch(self):
    match = dict(
      _key=self.job.active_batch_key,
      active=True
    )

    try:
      data_from_db = self.tx.collection('Batch').find(match).next()
      self.batch = Batch(**data_from_db)
      self.info.active_batch_key = self.batch.key
      self.info.active_batch_qt = self.batch.qt_total
    except StopIteration:
      pass

  def get_batch_step_done_count(self):
    # Instead of looking at total count, use distinct to
    # bypass potential duplicate STEP_COMPLETED events on the same step
    # within the same batch

    bind_vars = dict(
      batch_key=self.batch.key,
      status=StepStatus.DONE
    )

    step_done_count = self.tx.aql.execute(
      TraceabilityQueries.GET_BATCH_STEP_DONE_COUNT,
      bind_vars=bind_vars
    ).next()

    return step_done_count


  def get_batch_execution_data(self):

    batch_execution_data = self.tx.aql.execute(
      TraceabilityQueries.GET_BATCH_EXECUTION_DATA,
      # in self info can be under new_batch_key or active_batch_key, taking it from self.batch makes it more consistent.
      bind_vars=dict(batch_key=self.batch.key)
    ).next()

    return batch_execution_data



  def current_step_was_last_to_do(self):
    total_step_count = self.get_job_steps_count()
    step_done_count = self.get_batch_step_done_count()

    return step_done_count == total_step_count


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

    new_wip = WIP(
      _from=f'Phase/{self.info.phase_key}',
      _to=f'Phase/{self.info.next_phase_key}',
      batch_key=self.info.completed_batch_key,
      wo_key=self.info.work_order_key,
      product_key=self.info.product_key,
      quantity=self.info.completed_batch_qt
    )

    self.tx.collection('wip').insert(new_wip)

    self.tx.aql.execute(
      TraceabilityQueries.UPDATE_NEXT_BATCH_AVAILABLE_STATE_FOR_JOBS_IN_PHASES,
      bind_vars=dict(wo_key=self.info.work_order_key, phase_keys=[self.info.next_phase_key])
    )


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

  def book_wip(self, quantity):
    if quantity == 0:
      return

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
    self.tx.aql.execute(
      TraceabilityQueries.UPDATE_NEXT_BATCH_AVAILABLE_STATE_FOR_JOBS_IN_PHASES,
      bind_vars=dict(wo_key=self.info.work_order_key, phase_keys=[self.info.phase_key])
    )


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
    self.tx.aql.execute(
      TraceabilityQueries.UPDATE_NEXT_BATCH_AVAILABLE_STATE_FOR_JOBS_IN_PHASES,
      bind_vars=dict(wo_key=self.info.work_order_key, phase_keys=[self.info.phase_key])
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

  def start_job(self):

    # Check job hasn't been started already
    self.get_job_data()
    if self.job.stage != WorkStatus.CREATED:
      raise JobIsStartedError('Job has already been started')

    # Check config for unassigned jobs
    show_unassigned_jobs_to_operators = self.tx.collection('Config').get('show_unassigned_jobs_to_operators')
    can_self_assign = show_unassigned_jobs_to_operators.get('value', True) if show_unassigned_jobs_to_operators is not None else True
    if self.job.assigned_to is None and not show_unassigned_jobs_to_operators.get('value', True):
      raise JobHasNoAssigneeError('Unassigned jobs cannot be worked on as config "show_unassigned_jobs_to_operators" is false')

    # Create new batch and store _key in Event.info
    self.create_batch()

    # Create new WorkSession and store _key in Event.info
    self.create_work_session()

    # Create batch serials
    # self.create_batch_serial_records()

    # Update WorkOrder status
    wo = self.get_work_order_data()

    if wo.status == WorkStatus.CREATED:
      wo.status = WorkStatus.STARTED
      wo.start = self.info.timestamp
      wo_update = model_to_db_dict(wo)
      self.tx.collection('WorkOrder').update(wo_update)

    # Update job
    job_update=dict(
      _key = self.info.job_key,
      start = self.info.timestamp,
      stage = WorkStatus.STARTED,
      last_work_session_started = self.info.work_session_key,
      active_batch_key = self.batch.key,
      active_batch_qt = self.batch.qt_total,
      active = True,
      assigned_to = self.info.user_key,
      last_online = self.info.timestamp
    )
    self.job = Job(**self.tx.collection('Job').update(job_update, return_new=True)['new'])

    # Update queue
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

  def pause_job(self):
    self.close_work_session(self.info.work_session_end)
    self.set_job_active_state(False)

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

      create_new_batch = self.job.parameters.auto_new_batch and is_next_batch_available

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

# --------------------------------------------------------------------
