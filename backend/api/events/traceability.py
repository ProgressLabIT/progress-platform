from events.shared import EventMeta

from models.traceability import *
from models.production import Job, WorkOrderFull, WorkStatus

from utils.exceptions import JobIsStartedError
from utils.production import Queries as ProductionQueries, update_target_queue
from utils.traceability import Queries as TraceabilityQueries
from utils.db import db, model_to_db_dict


class ProductionActivityEvent:
  production_collections = [
    'Batch',
    'Event',
    'Job',
    'Queue',
    # 'Serial',
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

  # def create_serial(self, counter, batch_key):
  #   new_serial = Serial(
  #     start=self.info.timestamp,
  #     wo_key=self.info.work_order_key,
  #     counter=counter,
  #     product_key=self.info.product_key,
  #     batches=[batch_key]
  #   )
  #   new_serial_key = self.tx.collection('Serial').insert(new_serial)['_key']

  #   return new_serial_key


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
    total_step_count = len(self.get_job_step_sequence())
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


  def remove_wip(self):
    # Delete booked WIP from the previous phase
    wip_match_filter=dict(_to=f'Job/{self.info.job_key}')
    self.tx.collection('wip').delete_match(wip_match_filter)

    # TODO: Make sure only wip related to active batch gets deleted
    # This setup would delete also other wip booked in advance.

  def book_wip(self, booking_qt):
    if not self.job:
      self.get_job_data()

    available_batches_cursor = self.tx.aql.execute(
      TraceabilityQueries.RETRIEVE_AVAILABLE_WIP,
      bind_vars=dict(phase_key=self.info.phase_key, wo_key=self.info.work_order_key)
    )

    available_batches = [WIP(**b) for b in available_batches_cursor]
    total_available = sum(wip.quantity for wip in available_batches)

    # TODO: change using while loop like in events/admin.py@override_progress
    for b in available_batches:
      if b.quantity <= booking_qt:
        # Book entire batch for job
        self.tx.collection('wip').update(dict(
          _key = b.key,
          _to = f'Job/{self.info.job_key}',
          active = True
        ))
        # Decrease booking quantity
        booking_qt -= b.quantity
        if not booking_qt:
          break

      else:
        # Book only booking_qt
        booking_percentage = booking_qt / b.quantity
        self.tx.collection('wip').update(dict(
          _key=b.key,
          quantity=b.quantity - booking_qt,
          value=b.value * (1 - booking_percentage)
        ))

        # Add wip record with partially booked batch
        new_wip = WIP(
          from_doc=b.from_doc,
          to_doc=f'Job/{self.info.job_key}',
          wo_key=b.wo_key,
          batch_key=b.batch_key,
          product_key=b.product_key,
          quantity=booking_qt,
          value=b.quantity * booking_percentage,
          active=True
        )
        self.tx.collection('wip').insert(new_wip)

        break

    # Update input availability for jobs in this phase
    self.tx.aql.execute(
      TraceabilityQueries.UPDATE_NEXT_BATCH_AVAILABLE_STATE_FOR_JOBS_IN_PHASES,
      bind_vars=dict(wo_key=self.info.work_order_key, phase_keys=[self.info.phase_key])
    )

    return total_available


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


  def get_job_step_sequence(self):
    return self.tx.collection('Phase').get(self.info.phase_key)['step_sequence']


  def update_job_step_progress(self):
    if not self.job:
      self.get_job_data()

    current_batch_total_value = self.job.active_batch_qt / self.job.qt_planned

    procedure = self.get_job_step_sequence()
    step_progress_value = current_batch_total_value / len(procedure)
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

    if not self.job.first_phase:
      # TODO: check for wip availability
      pass

    self.info.completed_batch_key = self.job.active_batch_key
    self.info.completed_batch_qt = self.info.completed_batch_qt or self.job.active_batch_qt
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

    new_qt_completed = self.job.qt_completed + self.info.completed_batch_qt

    # NO REMAINING QUANTITY TO DO - LAST BATCH
    if new_qt_completed >= self.job.qt_planned: # No more pieces to work
      self.complete_job(new_qt_completed)
      self.response = dict(
        message = f"Batch {self.info.active_batch_key} and Job {self.info.job_key} completed.",
        job_data = self.job
      )

    # JOB HAS REMAINING QUANTITY
    else:
      new_progress = round(100 * new_qt_completed / self.job.qt_planned)
      job_update = dict(
        _key = self.info.job_key,
        active_batch_key = None,
        active_batch_qt = 0,
        qt_completed = new_qt_completed,
        qt_released = new_qt_completed,
        progress = new_progress,
        active = False
      )

      create_new_batch = self.job.parameters.auto_new_batch and self.job.next_batch_available

      if create_new_batch:
        self.create_batch()
        job_update['active_batch_key'] = self.batch.key
        job_update['active_batch_qt'] = self.batch.qt_total
        self.create_work_session()
        job_update['last_work_session_started'] = self.info.work_session_key
        job_update['active'] = True

      # Update job qt_completed and progress
      self.job = Job(**self.tx.collection('Job').update(job_update, check_rev=False, return_new=True)['new'])

      self.response = dict(
        message = f"Batch {self.info.active_batch_key} completed.",
        job_data = self.job,
        batch_data = dict(),
      )

      if create_new_batch:
        self.response['batch_data'] = self.get_batch_execution_data()

    if not self.job.first_phase:
      self.remove_wip()

    # is next_phase generate a WIP record and update job input availability state
    if not self.job.last_phase:
      self.declare_wip()

# --------------------------------------------------------------------
