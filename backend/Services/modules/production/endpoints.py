import traceback
from typing import Dict, List

from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder

from .models import *
from modules.process.models import PhaseProcedure
from modules.process.endpoints import search_step_media
from utils.db import db
from utils.api import APIResponse


router = APIRouter()
# work_orders = db.collection('WorkOrder')
# jobs = db.collection('Job')


@router.post('/work-order')
async def create_work_order(new_wo: WorkOrderNew):

  # Initialize transaction
  tx = db.begin_transaction(write=['WorkOrder', 'Job'], read=['Phase', 'Product'])
  wo_coll = tx.collection('WorkOrder')
  job_coll = tx.collection('Job')
  product_coll = tx.collection('Product')

  # Create WO record
  def create_wo_record(wo: WorkOrderNew, collection):
    data_in = jsonable_encoder(wo)
    new_wo_record = WorkOrderFull(**data_in)
    prepped = jsonable_encoder(new_wo_record, by_alias=True, include_none=False)
    new_wo_record.id = collection.insert(prepped)['_id']
    return new_wo_record

  try:
    product_data = product_coll.get(new_wo.product_id)
    new_wo.product_code = product_data['code']
    new_wo.product_description = product_data['description']
    new_wo_record = create_wo_record(new_wo, wo_coll)
  except:
    status_code=500
    response = {
      'status': status_code,
      'message': "There was a problem creating the work order record in the db",
      'error': traceback.format_exc()
    }
    raise HTTPException(
      status_code=status_code,
      detail=response
    )


  # Get phase data from products & phase parameters from phase
  # Create Jobs
  process = tx.document(new_wo_record.product_id)['process_phases']

  def create_job_record(wo_data, phase_id, collection):
    phase = PhaseProcedure(**tx.document(phase_id))
    new_job_record = Job(
      wo_id = new_wo_record.id,
      wo_code = new_wo_record.wo_code,
      wo_line = new_wo_record.wo_line,
      phase_id = phase_id,
      phase_alias = phase.alias,
      product_id = wo_data.product_id,
      product_code = wo_data.product_code,
      product_description = wo_data.product_description,
      operation_id = phase.operation_id,
      parameters = phase.params,
      qt_planned = wo_data.qt_planned
    )
    prepped = jsonable_encoder(new_job_record, by_alias=True, include_none=False)
    new_job_record.id = collection.insert(prepped)['_id']
    return new_job_record
  
  try:
    new_job_records = [create_job_record(new_wo_record, p_id, job_coll) for p_id in process]
  except:
    status_code=500
    response = {
      'status': status_code,
      'message': "There was a problem creating job records in the db",
      'error': traceback.format_exc()
    }
    raise HTTPException(
      status_code=status_code,
      detail=response
    )

  # Commit transaction
  tx.commit_transaction()
  return APIResponse(
    message="Work order and jobs created",
    details={
      'work_order': new_wo_record,
      'jobs': new_job_records
    }
  )


@router.get('/work-order')
async def get_wo_list():

  query = """
    FOR wo IN WorkOrder
      LET qt_remaining = wo.qt_planned - wo.qt_completed
      LET jobs = ( FOR j IN Job FILTER !j.trash && j.wo_id == wo._id RETURN j)
      LET phases = ( FOR j IN jobs FILTER !j.trash RETURN DISTINCT j.phase_alias )
      LET active = TO_BOOL(SUM(FOR j IN jobs FILTER !j.trash && j.active RETURN 1))
      RETURN MERGE ([wo, { qt_remaining: qt_remaining, phase_sequence: phases, active: active }])  
  """

  # wo_list = [WorkOrderFull(**wo) for wo in db.collection('WorkOrder').all()]
  wo_list = [wo for wo in db.aql.execute(query)]
  return APIResponse(detail=wo_list)


@router.get('/work-order/{wo_key}')
async def get_wo_data(wo_key: str):
  
  query = """
    FOR wo IN WorkOrder
      FILTER wo._key == @wo_key
      
      // LET qt_remaining = wo.qt_planned - wo.qt_completed
      
      // get phases in order from product data
      LET phases = FIRST( FOR p IN Product FILTER p._id == wo.product_id RETURN p.process_phases )

      

      // get job data
      LET jobs =  ( 
        FOR j IN Job
        FILTER j.wo_id == wo._id && !j.trash
        LET operator = KEEP(DOCUMENT(j.assigned_to), '_id', 'name', 'surname', 'active')
        RETURN MERGE( j, { assigned_to: operator } )
      )

      // check if any job is active
      LET active = TO_BOOL(COUNT(FOR j IN Job FILTER !j.trash && j.wo_id == wo._id && j.active RETURN 1))

      // Return enriched wo data
      RETURN MERGE ([
        wo, { 
        // qt_remaining: qt_remaining, 
        phase_sequence: phases, 
        jobs: jobs, 
        active: active 
      }])
  """

  wo_data = db.aql.execute(query, bind_vars={ 'wo_key': wo_key }).next()
  return APIResponse(detail=WorkOrderDetails(**wo_data))

@router.get('/job')
async def get_job_list():

  db_resp = db.aql.execute("FOR j IN Job FILTER !j.trash RETURN j")
  job_list = [Job(**j) for j in db_resp]

  return APIResponse(detail=job_list)



@router.get('/job-assignment')
async def get_assignment_list(user_id: str = None):

  result = db.aql.execute("""
    LET assigned_jobs_by_operator = (
      LET user_id = @user_id ? : '*'
      FOR o IN User
      FILTER o.roles.operator == true && o._id LIKE user_id
      LET assigned_jobs = (    
        FOR j in Job
        FILTER !j.trash && j.assigned_to == o._id
        RETURN j
      )
      
      RETURN {
        operator: KEEP(o, '_id', 'name', 'surname', 'active', 'department_id'),
        assigned_jobs: assigned_jobs
      }
    )

    LET unassigned_jobs = (
      FOR j in Job
      FILTER !j.trash && j.assigned_to == null
      RETURN j
    )

    RETURN {
      assigned_jobs_by_operator: assigned_jobs_by_operator,
      unassigned_jobs: unassigned_jobs
    }  
  """, bind_vars= { "user_id": user_id}).next()

  return APIResponse(detail=AssignmentsResponse(**result))
  # cursor = db.collection('assigned_to').find({ 'rel_type': 'JobOperator'})
  # assignment_list = [JobAssignment(**a) for a in cursor]
  # return APIResponse(detail=assignment_list)


@router.get('/job/{job_key}')
async def get_job_data(job_key: str):

  try:
    job_data = db.collection('Job').get(job_key)
  except:
    status_code=500
    response = {
      'status_code': status_code,
      'message': "Couldn't retrieve data from the DB",
      'error': traceback.format_exc()
    }
    raise HTTPException(status_code=status_code, detail=response)
  
  # print(job_data)
  if job_data['stage'] == 'created':
  # job hasn't been started yet. Retrieve latest procedure
    query = """
      FOR p IN Phase
      FILTER p._id == @phase_id
        FOR s IN p.step_sequence
        RETURN DOCUMENT(s)
    """
    bind_vars = { 'phase_id': job_data['phase_id'] }
    
    try:
      # db_steps = db.collection('Step').find({ 'phase_id': job_data['phase_id'] })
      db_steps = db.aql.execute(query, bind_vars=bind_vars)
      job_steps = [s for s in db_steps]
      # print(job_steps)
    except:
      status_code=500
      response = {
        'status_code': status_code,
        'message': "Couldn't retrieve data from the DB",
        'error': traceback.format_exc()
      }
      raise HTTPException(status_code=status_code, detail=response)

    for s in job_steps:
      try: 
        filenames = search_step_media(s['_key'])
        s['media'] = [media_name for media_name in filenames]
        # print(s)
      except:
        status_code=500
        response = {
          'status_code': status_code,
          'message': f"Error while retrieving media info about {s['_id']}",
          'error': traceback.format_exc()
        }
        raise HTTPException(status_code=status_code, detail=response)

    job_data['step_sequence'] = job_steps
    print(job_data)

    response = {
      'message': f"Retrieved data for Job/{job_key}",
      'detail': JobWithProcedure(**job_data)
    }
    return APIResponse(**response)


  
  
    

 




@router.patch('/job/{job_key}')
async def update_job(job_key: str, job_data: dict):
  # print(**job_data)

  try:
    db_resp = db.collection('Job').update({ '_key': job_key, **job_data }, return_new=True)
  except:
    status_code = 500
    response = {
     'status_code': status_code,
     'message': "Couldn't update Job on the db",
     'error': traceback.format_exc()
    }
    raise HTTPException(status_code=status_code, detail=response)

  status_code = 200
  response = {
    'message': f"Job {job_key} updated correctly",
    'detail': db_resp['new']
  }
  return APIResponse(**response)


@router.post('/job/update')
async def update_jobs(job_updates:List[JobUpdate]):

  print(job_updates)
  tx = db.begin_transaction(write=['Job'])
  job_db = tx.collection('Job')

  results = []
  
  try:
    for u in job_updates:

      if u.action == JobUpdateType.INSERT:
        new_job_record = jsonable_encoder(Job(**u.data), by_alias=True, include_none=False)
        db_resp = job_db.insert(new_job_record, return_new=True)['new']

      elif u.action == JobUpdateType.UPDATE:
        db_resp = job_db.update(u.data, return_new=True)['new']

      elif u.action == JobUpdateType.DELETE:
        db_resp = job_db.update({ **u.data, 'trash': True })['new']

      results.append(db_resp)
    
    tx.commit_transaction()
    return APIResponse(detail=db_resp, message="Jobs updated successfully")

  except: 
    status_code = 500
    error_str = traceback.format_exc()

    response = {
      'status_code': status_code,
      'message': "There was an error saving the updates",
      'error': error_str 
    }

    raise HTTPException(status_code=status_code, detail=response)


