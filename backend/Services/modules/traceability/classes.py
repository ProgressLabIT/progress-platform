from .models import *
from modules.production.models import WorkStatus
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
  BATCH_COMPLETED = 'complete_batch'

  ######################################################################
  # INIT & SAVE
  ######################################################################

  def __init__(self, event: ProductionEvent, database=db):
    self.db = database
    self.info = event

    # define action to be taken based on the event type
    self.action = getattr(self, self.info.event_type.value)
    print(vars(self))


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
      user_id=self.info.user_id,
      user_session_id=self.info.user_session_id,
      start=self.info.timestamp,
      active=True
    )
    new_work_session_out = self.tx.collection('WorkSession').insert(new_work_session_in, return_new=True)['new']
    return WorkSession(**new_work_session_out)


  def get_current_work_session(self):
    match = {
      'job_id': self.info.job_id,
      'active': True
    }
    data_from_db = self.tx.collection('WorkSession').find(match).next()
    return WorkSession(**data_from_db)


  def close_work_session(self):
    current_work_session = self.get_current_work_session()
    self.info.work_session_id = current_work_session.id

    ws_end = self.info.timestamp
    ws_update = {
      '_key': current_work_session.key,
      'end': self.info.timestamp,
      'active': False
    }
    collection = self.tx.collection('WorkSession')
    updated_work_session = collection.update(ws_update, return_new=True)['new']
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
    return Batch(**new_batch_out)

  def get_current_batch(self):
    match = {
      'job_id': self.info.job_id,
      'active': True
    }
    data_from_db = self.tx.collection('Batch').find(match).next()
    return Batch(**data_from_db)


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

  
  # def get_batch_time_record(self):
  #   match = {
  #     'work_session_id': f'WorkSession/{self.info.ws_key}',
  #     'batch_id': f'Batch/{self.info.batch_key}'
  #   }
  #   record = self.tx.collection('BatchTimeRecord').find(match)
  #   return record['_id']

  
  def update_batch_time_record(
    self, 
    full_session: bool,
    record_id: str = None, 
    batch_id: str = None, 
    ws_id: str = None 
  ):
    if record_id:
      record_update = {
        '_id': record_id,
        'end': self.info.timestamp,
        'full_session': full_session
      }
      self.tx.collection('BatchTimeRecord').update(record_update)

    else:
      match = {
        'batch_id': batch_id,
        'work_session_id': ws_id,
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
    self.tx.update_document({ '_id': job_id, 'active': active })




  ######################################################################
  # EVENT ACTIONS
  ######################################################################

  def start_job(self):
    # Create new WorkSession
    new_ws = self.create_work_session()
    self.info.work_session_id = new_ws.id

    # Create new batch
    new_batch = self.create_batch()
    self.info.batch_id = new_batch.id

    # Craete batch timing record
    self.create_batch_time_record(batch_id=new_batch.id, ws_id=new_ws.id)
    
    # Update job
    job_update_data = {
      '_id': self.info.job_id,
      'start': self.info.timestamp,
      'stage': WorkStatus.STARTED,
      'last_work_session_started': self.info.work_session_id,
      'current_batch': self.info.batch_id,
      'active': True,
      'assigned_to': self.info.user_id
    }
    self.tx.collection('Job').update(job_update_data)


  # ....................................................................

  def pause_job(self):
    # Update Work Session
    ws = self.close_work_session()
    self.info.work_session_id = ws.id
    
    # Update BatchTimeRecord
    batch = self.get_current_batch()
    self.info.batch_id = batch.id

    # here we define whether the work session was fully dedicated to a given batch
    # if it is not it's because it was started before the beginning of the batch
    full_session = ws.start >= batch.start
    self.update_batch_time_record(ws_id=ws.id, batch_id=batch.id, full_session=full_session)

    # Update job
    self.set_job_active_state(False)

  # ....................................................................

  def resume_job(self):
    new_ws = self.create_work_session()
    self.info.work_session_id = new_ws.id

    batch = self.get_current_batch()
    self.info.batch_id = batch.id

    self.create_batch_time_record(batch_id=batch.id, ws_id=new_ws.id)

    job_update = {
      '_id': self.info.job_id,
      'last_work_session_started': new_ws.id,
      'active': True
    }
    self.tx.collection('Job').update(job_update)

  # ....................................................................

  def complete_step(self):
    self.info.work_session_id = self.get_current_work_session().id
    self.info.batch_id = self.get_current_batch().id

    step_data = StepExecutionData(**vars(self.info))
    step_data.completed = self.info.timestamp
    step_data.status = StepStatus.DONE

    self.tx.collection('StepExecutionData').insert(step_data)
    

  # def complete_batch(self):


  # def close_job(self):
