from models.traceability import *
from models.production import Job, WorkOrderFull, WorkStatus
from utils.production import Queries as ProductionQueries
from utils.traceability import Queries as TraceabilityQueries
from utils.db import db, model_to_db_dict


class Event:

  ###################################
  # Class properties
  ###################################

  # Transaction parameters
  write_collections = [
    'Batch',
    'BatchTimeRecord',
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
  JOB_RESUMED = 'resume_job'
  JOB_CLOSED = 'close_job'
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

    # Apply updates to global application state
    getattr(self, self.action)()
    self.update_work_order()

    # Save event as is
    self.tx.collection('Event').insert(self.info)

    # Commit transaction
    self.tx.commit_transaction()

    # Return any required value
    return self.response


  ######################################################################
  # HELPER METHODS (Updates to specific collections)
  ######################################################################

  # ....................................................................
  # WorkSession
  # ....................................................................

  def create_work_session(self):
    new_work_session = self.tx.aql.execute(
      TraceabilityQueries.CREATE_WORK_SESSION, bind_vars=dict(
        job_key=self.info.job_key,
        work_order_key=self.info.work_order_key,
        user_key=self.info.user_key,
        user_session_key=self.info.user_session_key,
        start=self.info.timestamp,
        last_online=self.info.timestamp
      )
    ).next()

    return WorkSession(**new_work_session)


  def get_current_work_session(self):
    match=dict(
      job_key=self.info.job_key,
      active=True
    )
    data_from_db = self.tx.collection('WorkSession').find(match).next()
    work_session = WorkSession(**data_from_db)
    return work_session


  def close_work_session(self):
    ws_update=dict(
      _key=self.info.work_session_key,
      end=self.info.timestamp,
      active=False
    )
    updated_work_session = self.tx.collection('WorkSession').update(ws_update, return_new=True, check_rev=False)['new']
    return WorkSession(**updated_work_session)


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
  #     self.create_serial(counter=i, batch_key=self.info.current_batch_key)
  #     for i in batch_serials
  #   ]

  #   self.tx.collection('Batch').update(dict(
  #     _key=self.info.current_batch_key,
  #     serial_numbers=serial_keys
  #   ))



  # ....................................................................
  # Batch
  # ....................................................................

  def create_batch(self):

    self.job = self.get_job_data()

    # Book wip from buffer
    if not self.job.first_phase:
      self.book_wip()

    new_batch_in = Batch(
      job_key=self.info.job_key,
      phase_key=self.info.phase_key,
      work_order_key=self.info.work_order_key,
      start=self.info.timestamp,
      active=True
    )
    new_batch_out = self.tx.collection('Batch').insert(new_batch_in, return_new=True)['new']

    batch = Batch(**new_batch_out)
    self.info.current_batch_key = batch.key

    return batch


  def get_current_batch(self):
    match = dict(
      job_key=self.info.job_key,
      active=True
    )
    data_from_db = self.tx.collection('Batch').find(match).next()
    batch = Batch(**data_from_db)
    return batch


  def get_batch_step_done_count(self):
    # Instead of looking at total count, use distinct to
    # bypass potential duplicate STEP_COMPLETED events on the same step
    # within the same batch

    bind_vars = dict(
      batch_key=self.info.current_batch_key,
      status=StepStatus.DONE
    )

    return self.tx.aql.execute(
      TraceabilityQueries.GET_BATCH_STEP_DONE_COUNT,
      bind_vars=bind_vars
    ).next()


  def current_step_was_last_to_do(self):
    total_step_count = len(self.get_job_step_sequence())
    step_done_count = self.get_batch_step_done_count()
    return step_done_count == total_step_count


  # ....................................................................
  # BatchTimeRecord
  # ....................................................................

  def create_batch_time_record(self, batch_key, ws_key):
    new_record = BatchTimeRecord(
      batch_key=batch_key,
      work_session_key=ws_key,
      start=self.info.timestamp,
      phase_key=self.info.phase_key,
      work_order_key=self.info.work_order_key,
      product_key=self.info.product_key,
      active=True
    )
    record_key = self.tx.collection('BatchTimeRecord').insert(new_record)['_key']



  def update_batch_time_record(self, full_session: bool):
    batch_key = self.info.current_batch_key or self.info.completed_batch_key
    self.tx.aql.execute(
      TraceabilityQueries.UPDATE_BATCH_TIME_RECORD, bind_vars=dict(
        batch_key=batch_key,
        ws_key=self.info.work_session_key,
        end=self.info.timestamp,
        full_session=full_session
      )
    )


  # ....................................................................
  # WIP
  # ....................................................................

  def declare_wip(self):
    if not self.job:
      self.job = self.get_job_data()

    if not self.job.first_phase:
      wip_match_filter=dict(_to=f'Job/{self.info.job_key}')
      self.tx.collection('WIP').delete_match(wip_match_filter)

    new_wip = WIP(
      _from=f'Phase/{self.info.phase_key}',
      _to=f'Phase/{self.info.next_phase}',
      batch_key=self.info.completed_batch_key,
      wo_key=self.info.work_order_key,
      product_key=self.info.product_key,
      quantity=self.info.completed_batch_qt
    )

    self.tx.collection('WIP').insert(new_wip)


  def book_wip(self):
    if not self.job:
      self.job = self.get_job_data()

    # batches have no predefined qt, this is so that in the future qt may be user defined if necessary. However to monitor the WIP
    booking_qt = min([
      self.job.qt_planned - self.job.qt_completed,
      self.job.parameters.production_batch_qt
    ])

    available_batches_cursor = self.tx.aql.execute(
      TraceabilityQueries.RETRIEVE_AVAILABLE_WIP,
      bind_vars=dict(phase=self.info.phase_key)
    )

    available_batches = [WIP(**b) for b in available_batches_cursor]

    for b in available_batches:
      if b.quantity <= booking_qt:
        # Book entire batch for job
        self.tx.collection('WIP').update(dict(_key=b.key, _to=f'Job/{self.info.job_key}'))
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
          value=b.quantity * booking_percentage
        )
        self.tx.collection('WIP').insert(new_wip)

        break


  # def check_input_availability(self):
  #   if not self.job:
  #     self.job = self.get_job_data()

  #   if not (self.job.first_phase or self.job.input_available):
  #     status_code = 409
  #     message = "Cannot start work session, not enough input material available."
  #     response = dict(
  #       status=status_code,
  #       message=message,
  #     )
  #     raise HTTPException(status_code=status_code, detail=response)


  # ....................................................................
  # Job
  # ....................................................................

  def set_job_active_state(self, active: bool):
    job_key = self.info.job_key
    self.tx.collection('Job').update(dict(_key=job_key, active=active), check_rev=False)


  def get_job_data(self):
    job = self.tx.collection('Job').get(self.info.job_key)
    return Job(**job)


  def get_job_step_sequence(self):
    return self.tx.collection('Phase').get(self.info.phase_key)['step_sequence']


  def update_job_step_progress(self):
    job = self.get_job_data()
    default_batch = job.parameters.production_batch_qt
    remaining_qt = job.qt_planned - job.qt_completed
    batch_qt = min([default_batch, remaining_qt])
    current_batch_total_value = batch_qt / job.qt_planned

    procedure = self.get_job_step_sequence()
    step_progress_value = current_batch_total_value / len(procedure)
    step_done_count = self.get_batch_step_done_count()
    completed_qt_progress = job.qt_completed / job.qt_planned
    total_progress = completed_qt_progress + (step_progress_value * step_done_count)

    job_update=dict(
      _key=job.key,
      progress=round(total_progress * 100)
    )
    self.tx.collection('Job').update(job_update)


  def close_job(self, completed_qt):
    # Close job
    # Query allows for single call to DB to get and update job data

    bind_vars=dict(
      job_key=self.info.job_key,
      stage=WorkStatus.CLOSED,
      qt_completed=completed_qt,
      end=self.info.timestamp,
    )
    self.tx.aql.execute(TraceabilityQueries.CLOSE_JOB, bind_vars=bind_vars)

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
      self.job = self.get_job_data()
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
    self.batch = self.create_batch()
    self.info.current_batch_key = self.batch.key

    # Create new WorkSession and store _key in Event.info
    self.work_session = self.create_work_session()
    self.info.work_session_key = self.work_session.key

    # Create batch timing record
    self.create_batch_time_record(
      batch_key=self.info.current_batch_key,
      ws_key=self.info.work_session_key
    )

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
      _key=self.info.job_key,
      start=self.info.timestamp,
      stage=WorkStatus.STARTED,
      last_work_session_started=self.info.work_session_key,
      current_batch=self.info.current_batch_key,
      active=True,
      assigned_to=self.info.user_key,
      last_online=self.info.timestamp
    )
    self.tx.collection('Job').update(job_update)

    # Update queue
    queue_match = dict(
      subqueue_target_key=self.info.user_key,
      site_key='0'
    )
    operator_queue_exists = self.tx.collection('Queue').find(queue_match).count()

    if operator_queue_exists:
      self.tx.aql.execute(
        ProductionQueries.ADD_JOB_TO_QUEUE,
        bind_vars=dict(
          target_key=self.info.user_key,
          job_key=self.info.job_key
        )
      )

    else:
      self.tx.collection('Queue').insert(dict(
        **queue_match,
        jobs=[self.info.job_key]
      ))

  # ....................................................................

  def pause_job(self):
    # Update Work Session
    if not self.info.work_session_key:
      self.work_session = self.get_current_work_session()
      self.info.work_session_key = self.work_session.key

    self.close_work_session()

    # Update BatchTimeRecord
    if not self.info.current_batch_key:
      self.batch = self.get_current_batch()
      self.info.current_batch_key = self.batch.key


    # here we define whether the work session was fully dedicated to a given batch
    # if it is not it's because it was started before the beginning of the batch
    full_session = self.work_session.start >= self.batch.start

    self.update_batch_time_record(full_session=full_session)

    # Update job
    self.set_job_active_state(False)


  # ....................................................................

  def resume_job(self):
    self.work_session = self.create_work_session()
    self.info.work_session_key = self.work_session.key

    self.batch = self.get_current_batch()
    self.info.current_batch_key = self.batch.key

    self.create_batch_time_record(batch_key=self.batch.key, ws_key=self.work_session.key)

    job_update=dict(
      _key=self.info.job_key,
      last_work_session_started=self.work_session.key,
      active=True
    )
    self.tx.collection('Job').update(job_update)

    self.response = self.info.work_session_key


  # ....................................................................

  def complete_step(self):
    # Save current work session and batch keys in Event.info
    if not self.info.work_session_key:
      self.work_session = self.get_current_work_session()
      self.info.work_session_key = self.work_session.key

    if not self.info.current_batch_key:
      self.batch = self.get_current_batch()
      self.info.current_batch_key = self.batch.key

    # Create StepExecutionData record
    step_data = StepExecutionData(**vars(self.info))
    step_data.batch_key = self.batch.key
    step_data.completed = self.info.timestamp
    step_data.status = StepStatus.DONE
    self.tx.collection('StepExecutionData').insert(step_data)


    # if last step complete batch
    if (self.current_step_was_last_to_do()):
      self.complete_batch()

    # else update job step progress
    else:
      self.update_job_step_progress()


  # ....................................................................

  def complete_batch(self):
    # Get work_session_data
    if not self.info.work_session_key:
      self.work_session = self.get_current_work_session()
      self.info.work_session_key = self.work_session.key

    # Get completed batch data
    self.completed_batch = self.get_current_batch()

    if not self.info.current_batch_key:
      self.info.completed_batch_key = self.completed_batch.key
    else:
      self.info.completed_batch_key = self.info.current_batch_key

    # Create new batch if there is a remaining quantity
    self.job = self.get_job_data()
    new_qt_completed = self.job.qt_completed + self.info.completed_batch_qt
    batch_is_last = new_qt_completed >= self.job.qt_planned

    if batch_is_last:
      self.close_job(new_qt_completed)
      self.close_work_session()
      self.update_batch_time_record(full_session=True)

    else:
      # Update BatchTimeRecord
      self.update_batch_time_record(full_session=False)

      new_batch = self.create_batch()
      self.info.new_batch_key = new_batch.key
      self.create_batch_time_record(batch_key=new_batch.key, ws_key=self.info.work_session_key)

      # Update job qt_completed and progress
      new_progress = round(100 * new_qt_completed / self.job.qt_planned)
      job_update=dict(
        _key=self.info.job_key,
        current_batch=self.info.new_batch_key,
        qt_completed=new_qt_completed,
        qt_released=new_qt_completed,
        progress=new_progress
      )
      self.tx.collection('Job').update(job_update, check_rev=False)


    # Complete batch
    self.tx.aql.execute(
      TraceabilityQueries.COMPLETE_BATCH, bind_vars=dict(
        batch_key=self.info.completed_batch_key,
        qt_pass=self.info.completed_batch_qt,
        end=self.info.timestamp
      )
    )


    # Update input availability for jobs in this phase
    self.tx.aql.execute(
      TraceabilityQueries.UPDATE_INPUT_AVAILABLE_STATE_FOR_JOBS_IN_PHASE,
      bind_vars=dict(wo_key=self.info.work_order_key, phase=self.info.phase_key)
    )

    # Release WIP
    self.info.next_phase = self.tx.aql.execute(
      TraceabilityQueries.GET_NEXT_PHASE_IN_WORK_ORDER,
      bind_vars=dict(wo_key=self.info.work_order_key, phase_key=self.info.phase_key)
    ).next()

    # is next_phase generate a WIP record and update job input availability state
    if self.info.next_phase:
      self.declare_wip()
      self.tx.aql.execute(
        TraceabilityQueries.UPDATE_INPUT_AVAILABLE_STATE_FOR_JOBS_IN_PHASE,
        bind_vars=dict(wo_key=self.info.work_order_key, phase=self.info.next_phase)
      )



