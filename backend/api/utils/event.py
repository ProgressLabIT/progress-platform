from models.traceability import *
from models.production import Job, WorkOrderFull, WorkStatus
from utils.production import Queries as ProductionQueries, update_target_queue
from utils.traceability import Queries as TraceabilityQueries
from utils.db import db, model_to_db_dict

class Event:

  ###################################
  # Class properties
  ###################################

  # Transaction parameters
  write_collections = [
    'Batch',
    'Event',
    'Job',
    'Queue',
    # 'Serial',
    'StepExecutionData',
    'WIP',
    'WorkOrder',
    'WorkSession'
  ]
  # read_collections = ['Phase', 'Product', 'Step

  # Mapping of event types to class methods
  JOB_STARTED = 'start_job'
  JOB_PAUSED = 'pause_job'
  JOB_PAUSED_OFFLINE = 'pause_job'
  JOB_RESUMED = 'resume_job'
  JOB_BACK_ONLINE = 'restore_work_session'
  STEP_COMPLETED = 'complete_step'
  BATCH_COMPLETED = 'complete_batch'

  ######################################################################
  # INIT & SAVE
  ######################################################################

  def __init__(self, event: ProductionEvent, database=db):
    self.db = database
    self.info = event
    self.response = None

    # define action to be taken based on the event type
    self.action = getattr(self, self.info.event_type.value)

  def save(self):
    # Initialize transaction
    self.tx = self.db.begin_transaction(write=self.write_collections)

    try:
      # Apply updates to global application state
      getattr(self, self.action)()
      self.update_job_last_online()
      self.update_work_order()

      # Save event as is
      self.tx.collection('Event').insert(self.info)

      # Commit transaction
      self.tx.commit_transaction()

      # Return any required value
      return self.response

    # In case of exceptions, abort transaction without catching them
    finally:
      if self.tx.transaction_status() != 'committed':
        self.tx.abort_transaction()


  ######################################################################
  # HELPER METHODS (Updates to specific collections)
  ######################################################################

  # ....................................................................
  # WorkSession
  # ....................................................................

  def create_work_session(self):
    # Check no other work session is active from the user and close it if necessary
    match = dict(
      user_key=self.info.user_key,
      active=True
    )
    cursor = self.tx.collection('WorkSession').find(match)
    if cursor.count():
      for ws in cursor:
        ws.update(dict(
          active=False,
          end=self.info.timestamp
        ))
        self.tx.collection('WorkSession').update(ws)
        self.tx.collection('Job').update({ '_key': ws['job_key'], 'active': False })

    new_work_session = self.tx.aql.execute(
      TraceabilityQueries.CREATE_WORK_SESSION, bind_vars=dict(
        job_key = self.info.job_key,
        batch_key = self.batch.key, # in self info can be under new_batch_key or active_batch_key, taking it from self.batch makes it more consistent.
        work_order_key = self.info.work_order_key,
        phase_key = self.info.phase_key,
        product_key = self.info.product_key,
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


  def close_work_session(self):
    updated_work_session = WorkSession(**self.tx.aql.execute(
      TraceabilityQueries.CLOSE_WORK_SESSION, bind_vars = dict(
        job_key = self.info.job_key,
        end = self.info.timestamp,
    )).next())

    self.work_session = updated_work_session
    self.info.work_session_key = updated_work_session._key

    return updated_work_session


  # ....................................................................
  # Serial
  # ....................................................................

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



  # ....................................................................
  # Batch
  # ....................................................................

  def create_batch(self, batch_qt):
    self.get_job_data()

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

    return self.tx.aql.execute(
      TraceabilityQueries.GET_BATCH_STEP_DONE_COUNT,
      bind_vars=bind_vars
    ).next()


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


  # ....................................................................
  # WIP
  # ....................................................................

  def declare_wip(self):
    if not self.job:
      self.get_job_data()

    if not self.job.first_phase:
      # Delete booked WIP from the previous phase
      wip_match_filter=dict(_to=f'Job/{self.info.job_key}')
      self.tx.collection('WIP').delete_match(wip_match_filter)

    new_wip = WIP(
      _from=f'Phase/{self.info.phase_key}',
      _to=f'Phase/{self.info.next_phase_key}',
      batch_key=self.info.completed_batch_key,
      wo_key=self.info.work_order_key,
      product_key=self.info.product_key,
      quantity=self.info.completed_batch_qt
    )

    self.tx.collection('WIP').insert(new_wip)

    self.tx.aql.execute(
      TraceabilityQueries.UPDATE_NEXT_BATCH_AVAILABLE_STATE_FOR_JOBS_IN_PHASE,
      bind_vars=dict(wo_key=self.info.work_order_key, phase_key=self.info.next_phase_key)
    )


  def book_wip(self, booking_qt):
    if not self.job:
      self.get_job_data()

    available_batches_cursor = self.tx.aql.execute(
      TraceabilityQueries.RETRIEVE_AVAILABLE_WIP,
      bind_vars=dict(phase=self.info.phase_key)
    )

    available_batches = [WIP(**b) for b in available_batches_cursor]

    for b in available_batches:
      if b.quantity <= booking_qt:
        # Book entire batch for job
        self.tx.collection('WIP').update(dict(
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
        self.tx.collection('WIP').update(dict(
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
        self.tx.collection('WIP').insert(new_wip)

        break

    # Update input availability for jobs in this phase
    self.tx.aql.execute(
      TraceabilityQueries.UPDATE_NEXT_BATCH_AVAILABLE_STATE_FOR_JOBS_IN_PHASE,
      bind_vars=dict(wo_key=self.info.work_order_key, phase_key=self.info.phase_key)
    )


  # ....................................................................
  # Job
  # ....................................................................

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
    self.get_job_data()
    default_batch = self.job.parameters.production_batch_qt
    remaining_qt = self.job.qt_planned - self.job.qt_completed
    batch_qt = min([default_batch, remaining_qt])
    current_batch_total_value = batch_qt / self.job.qt_planned

    procedure = self.get_job_step_sequence()
    step_progress_value = current_batch_total_value / len(procedure)
    step_done_count = self.get_batch_step_done_count()
    completed_qt_progress = self.job.qt_completed / self.job.qt_planned
    total_progress = completed_qt_progress + (step_progress_value * step_done_count)

    job_update=dict(
      _key = self.job.key,
      progress = round(total_progress * 100)
    )
    self.tx.collection('Job').update(job_update)


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


  # ....................................................................
  # WorkOrder
  # ....................................................................

  def get_work_order_data(self):
    wo_data = self.tx.collection('WorkOrder').get(self.info.work_order_key)
    wo_data_out = WorkOrderFull(**wo_data)
    return wo_data_out


  def update_work_order(self):
    if not self.info.work_order_key:
      self.get_job_data()
      self.info.work_order_key = self.job.wo_key

    updated_wo = self.tx.aql.execute(
      TraceabilityQueries.UPDATE_WORK_ORDER,
      bind_vars=dict(wo_key=self.info.work_order_key)
    ).next()

    if updated_wo['status'] == WorkStatus.CLOSED.value:
      self.tx.aql.execute(
        ProductionQueries.REMOVE_WORK_ORDER_FROM_QUEUE,
        bind_vars=dict(wo_key=self.info.work_order_key)
      )

  ######################################################################
  # EVENT ACTIONS
  ######################################################################

  def start_job(self):
    # Create new batch and store _key in Event.info
    self.get_job_data()
    self.create_batch(self.job.qt_next_batch)

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

  # ....................................................................

  def pause_job(self):
    self.close_work_session()
    self.set_job_active_state(False)

  # ....................................................................

  def resume_job(self):
    self.get_job_data()

    # Create batch if none is active and store data for work session creation
    if self.job.active_batch_key:
      self.get_active_batch()
    else:
      self.create_batch(self.job.qt_next_batch)

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

  # ....................................................................

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

  # ....................................................................

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


  # ....................................................................

  def complete_batch(self):

    self.get_job_data()

    self.info.completed_batch_key = self.job.active_batch_key
    self.info.work_session_key = self.job.last_work_session_started

    # Complete batch
    self.tx.aql.execute(
      TraceabilityQueries.COMPLETE_BATCH, bind_vars=dict(
        batch_key=self.info.completed_batch_key,
        qt_pass=self.info.completed_batch_qt,
        end=self.info.timestamp
      )
    )
    self.close_work_session()

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
      default_batch_qt = self.job.parameters.production_batch_qt
      remaining_qt = self.job.qt_planned - self.job.qt_completed
      qt_next_batch = min([default_batch_qt, remaining_qt])

      new_progress = round(100 * new_qt_completed / self.job.qt_planned)
      job_update = dict(
        _key = self.info.job_key,
        active_batch_key = None,
        active_batch_qt = 0,
        qt_completed = new_qt_completed,
        qt_released = new_qt_completed,
        qt_next_batch = qt_next_batch,
        progress = new_progress,
        active = False
      )

      create_new_batch = self.job.parameters.auto_new_batch and self.job.next_batch_available

      if create_new_batch:
        self.create_batch(qt_next_batch)
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


    # Release WIP
    self.info.next_phase_key = self.tx.aql.execute(
      TraceabilityQueries.GET_NEXT_PHASE_IN_WORK_ORDER,
      bind_vars=dict(wo_key=self.info.work_order_key, phase_key=self.info.phase_key)
    ).next()

    # is next_phase generate a WIP record and update job input availability state
    if self.info.next_phase_key:
      self.declare_wip()




