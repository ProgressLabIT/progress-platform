from models.traceability import *
from models.production import Job, WorkStatus
from utils.db import db


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
    'StepExecutionData', 
    'WorkSession'
  ]
  # read_collections = ['Phase', 'Product', 'Step

  # Mapping of event types to class methods
  JOB_STARTED = 'start_job'
  JOB_PAUSED = 'pause_job'
  JOB_RESUMED = 'resume_job'
  JOB_CLOSED = 'close_job' 
  STEP_COMPLETED = 'complete_step'
  BATCH_COMPLETED = 'declare_production'

  ######################################################################
  # INIT & SAVE
  ######################################################################

  def __init__(self, event: ProductionEvent, database=db):
    self.db = database
    self.info = event
    self.info.user_id = f'User/{event.user_key}'
    self.info.user_session_id = f'UserSession/{event.user_session_key}'

    # define action to be taken based on the event type
    self.action = getattr(self, self.info.event_type.value)
    # print(vars(self))


  def save(self):
    # Initialize transaction
    self.tx = self.db.begin_transaction(write=self.write_collections)
    
    # Apply updates to global application state
    getattr(self, self.action)()
    
    # Save event as is
    self.tx.collection('Event').insert(self.info)

    # Commit transaction
    self.tx.commit_transaction()


  ######################################################################
  # HELPER METHODS (Updates to specific collections)
  ######################################################################

  def create_work_session(self):
    new_work_session_in = WorkSession(
      job_id=self.info.job_id,
      user_id=f'User/{self.info.user_key}',
      user_session_id=f'UserSession/{self.info.user_session_key}',
      start=self.info.timestamp,
      active=True
    )
    new_work_session_out = self.tx.collection('WorkSession').insert(new_work_session_in, return_new=True)['new']
    work_session = WorkSession(**new_work_session_out)
    return work_session


  def get_current_work_session(self):
    match = {
      'job_id': self.info.job_id,
      'active': True
    }
    data_from_db = self.tx.collection('WorkSession').find(match).next()
    work_session = WorkSession(**data_from_db)
    return work_session


  def close_work_session(self):
    ws_update = {
      '_id': self.info.work_session_id,
      'end': self.info.timestamp,
      'active': False
    }
    updated_work_session = self.tx.update_document(ws_update, return_new=True, check_rev=False)['new']
    return WorkSession(**updated_work_session)
    

  # ....................................................................
  # Batch
  # ....................................................................

  def create_batch(self):
    new_batch_in = Batch(
      job_id=self.info.job_id,
      start=self.info.timestamp,
      active=True
    )
    new_batch_out = self.tx.collection('Batch').insert(new_batch_in, return_new=True)['new']
    batch = Batch(**new_batch_out)
    return batch


  def get_current_batch(self):
    match = {
      'job_id': self.info.job_id,
      'active': True
    }
    data_from_db = self.tx.collection('Batch').find(match).next()
    batch = Batch(**data_from_db)
    return batch


  def get_batch_step_done_count(self):
    # Instead of looking at total count, use distinct to 
    # bypass potential duplicate STEP_COMPLETED events on the same step
    # within the same batch
    query = """
      LET step_count = COUNT(
        FOR s IN StepExecutionData
        FILTER s.batch_id == @batch_id && s.status == @status
        RETURN DISTINCT s.step_id
      )
      RETURN step_count
    """
    bind_vars = {
      'batch_id': self.info.current_batch_id,
      'status': StepStatus.DONE
    }
    # return self.tx.collection('StepExecutionData').find(filter).count()
    return self.tx.aql.execute(query, bind_vars=bind_vars).next()


  def current_step_was_last_to_do(self):
    total_step_count = len(self.get_job_step_sequence())
    step_done_count = self.get_batch_step_done_count()
    return step_done_count == total_step_count


  # ....................................................................
  # BatchTimeRecord 
  # ....................................................................

  def create_batch_time_record(self, batch_id, ws_id):
    new_record = BatchTimeRecord(
      batch_id = batch_id,
      work_session_id = ws_id,
      start = self.info.timestamp
    )
    record_id = self.tx.collection('BatchTimeRecord').insert(new_record)['_id']

  
  def update_batch_time_record(self, full_session: bool):
    match = {
      'batch_id': self.info.current_batch_id,
      'work_session_id': self.info.work_session_id,
    }
    update = {
      'end': self.info.timestamp,
      'full_session': full_session
    }
    self.tx.collection('BatchTimeRecord').update_match(match, update)

  
  # ....................................................................
  # Job
  # ....................................................................
  
  def set_job_active_state(self, active: bool):
    job_id = self.info.job_id
    self.tx.update_document({ '_id': job_id, 'active': active }, check_rev=False)


  def get_job_data(self):
    job = self.tx.document(self.info.job_id)
    return Job(**job)


  def get_job_step_sequence(self):
    return self.tx.document(self.info.phase_id)['step_sequence']


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

    job_update = {
      '_id': job.id,
      'progress': round(total_progress * 100)
    }
    self.tx.collection('Job').update(job_update)


  ######################################################################
  # EVENT ACTIONS
  ######################################################################

  def start_job(self):
    # Create new WorkSession and store _id in Event.info
    self.work_session = self.create_work_session()
    self.info.work_session_id = self.work_session.id

    # Create new batch and store _id in Event.info
    self.batch = self.create_batch()
    self.info.current_batch_id = self.batch.id 

    # Craete batch timing record
    self.create_batch_time_record(
      batch_id=self.info.current_batch_id, 
      ws_id=self.info.work_session_id
    )
    
    # Update job
    job_update = {
      '_id': self.info.job_id,
      'start': self.info.timestamp,
      'stage': WorkStatus.STARTED,
      'last_work_session_started': self.info.work_session_id,
      'current_batch': self.info.current_batch_id,
      'active': True,
      'assigned_to': f'User/{self.info.user_key}'
    }
    self.tx.collection('Job').update(job_update)


  # ....................................................................

  def pause_job(self):
    # Update Work Session
    if not self.info.work_session_id:
      self.work_session = self.get_current_work_session()
      self.info.work_session_id = self.work_session.id
    
    self.close_work_session()

    # Update BatchTimeRecord
    if not self.info.current_batch_id:
      self.batch = self.get_current_batch()
      self.info.current_batch_id = self.batch.id


    # here we define whether the work session was fully dedicated to a given batch
    # if it is not it's because it was started before the beginning of the batch
    full_session = self.work_session.start >= self.batch.start

    self.update_batch_time_record(full_session=full_session)

    # Update job
    self.set_job_active_state(False)


  # ....................................................................

  def resume_job(self):
    self.work_session = self.create_work_session()
    self.info.work_session_id = self.work_session.id
    
    self.batch = self.get_current_batch()
    self.info.current_batch_id = self.batch.id

    self.create_batch_time_record(batch_id=self.batch.id, ws_id=self.work_session.id)

    job_update = {
      '_id': self.info.job_id,
      'last_work_session_started': self.work_session.id,
      'active': True
    }
    self.tx.collection('Job').update(job_update)


  # ....................................................................

  def complete_step(self):
    # Save current work session and batch ids in Event.info
    if not self.info.work_session_id:
      self.work_session = self.get_current_work_session()
      self.info.work_session_id = self.work_session.id

    if not self.info.current_batch_id:
      self.batch = self.get_current_batch()
      self.info.current_batch_id = self.batch.id

    # Create StepExecutionData record
    step_data = StepExecutionData(**vars(self.info))
    step_data.batch_id = self.batch.id
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
    if not self.info.work_session_id:
      self.work_session = self.get_current_work_session()
      self.info.work_session_id = self.work_session.id

    # Get completed batch data
    if not self.info.current_batch_id:
      self.completed_batch = self.get_current_batch()
      self.info.completed_batch_id = self.completed_batch.id
    else:
      self.info.completed_batch_id = self.info.current_batch_id

    # Get job data
    self.job = self.get_job_data()
    
    # # Complete step if step_check
    # if job.parameters.step_check:
    #   self.complete_step()

    # Complete batch
    batch_update = {
      '_id': self.info.completed_batch_id,
      'qt_pass': self.info.completed_batch_qt,
      'active': False,
      'end': self.info.timestamp
    }
    self.tx.update_document(batch_update, check_rev=False)

    # Update BatchTimeRecord
    self.update_batch_time_record(full_session=False)

    # Create new batch if there is a remaining quantity
    new_qt_completed = self.job.qt_completed + self.info.completed_batch_qt

    batch_is_last = new_qt_completed == self.job.qt_planned

    if batch_is_last:
      self.close_job()

    else:
      new_batch = self.create_batch()
      self.info.new_batch_id = new_batch.id
      self.create_batch_time_record(batch_id=new_batch.id, ws_id=self.info.work_session_id)

    # Update job qt_completed and progress
    new_progress = round(100 * new_qt_completed / self.job.qt_planned)
    job_update = {
      '_id': self.info.job_id,
      'current_batch': self.info.new_batch_id,
      'qt_completed': new_qt_completed,
      'qt_released': new_qt_completed,
      'progress': new_progress
    }
    self.tx.update_document(job_update, check_rev=False)


  # ....................................................................

  def close_job(self):
    # Close job
    # Query allows for single call to DB to get and update job data
    query = """
      FOR j IN Job
      FILTER j._id == @job_id
      UPDATE j WITH {
        active: false,
        stage: @stage,
        current_batch: null,
        qt_released: j.qt_completed,
        end: @end
      } IN Job
    """

    bind_vars = {
      'job_id': self.info.job_id,
      'stage': WorkStatus.CLOSED,
      'end': self.info.timestamp
    }

    self.tx.aql.execute(query, bind_vars=bind_vars)

    # Close work session
    if not self.info.work_session_id:
      self.work_session = self.get_current_work_session()
      self.info.work_session_id = self.work_session.id

    self.close_work_session()

    # Update batch time record
    if not self.batch:
      self.batch = self.get_current_batch()

    full_session = self.work_session.start >= self.batch.start
    self.update_batch_time_record(full_session=full_session)
