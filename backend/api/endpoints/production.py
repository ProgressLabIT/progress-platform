import traceback
from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, Body, HTTPException
from fastapi.encoders import jsonable_encoder

from models.process import PhaseData
from models.product import ProductData
from models.production import *
from utils.api import APIResponse
from utils.db import db
from utils.process import search_step_media
from utils.production import Queries
from utils.traceability import update_job_progress


router = APIRouter()

# ----------------------------------------------------------------------


@router.post('/work-order')
async def create_work_order(new_wo: WorkOrderNew):

  # Initialize transaction
  tx = db.begin_transaction(write=['WorkOrder', 'Job', 'Queue'], read=['Phase', 'Product'])
  wo_coll = tx.collection('WorkOrder')
  job_coll = tx.collection('Job')
  product_coll = tx.collection('Product')

  # Create WO record
  def create_wo_record(wo: WorkOrderNew, collection):
    data_in = jsonable_encoder(wo)
    new_wo_record = WorkOrderFull(**data_in)
    prepped = jsonable_encoder(new_wo_record, by_alias=True)
    db_resp = collection.insert(prepped)
    new_wo_record.id = db_resp['_id']
    new_wo_record.key = db_resp['_key']
    return new_wo_record

  try:
    product_data = ProductData(**product_coll.get(new_wo.product_key))
    new_wo.product_code = product_data.code
    new_wo.product_description = product_data.description

    if len(product_data.process_phases):
      new_wo.phase_sequence = product_data.process_phases
    else:
      new_wo.phase_sequence = ['default']

    new_wo_record = create_wo_record(new_wo, wo_coll)

  except:
    status_code=500
    response = dict(
      status=status_code,
      message="There was a problem creating the work order record in the db",
      error=traceback.format_exc()
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )


  # Get phase data from products, phase parameters from phase & Create Jobs
  def get_procedure_for_new_job(phase_key):
    try:
      db_steps = tx.aql.execute(
        Queries.GET_PHASE_STEP_DATA, 
        bind_vars=dict(phase_key=phase_key)
      )
      job_steps = [s for s in db_steps]

    except:
      status_code=500
      response=dict(
        status_code=status_code,
        message=f"Couldn't retrieve data from the DB about Phase {phase_key}",
        error=traceback.format_exc()
      )
      raise HTTPException(status_code=status_code, detail=response)

    for s in job_steps:
      try: 
        filenames = search_step_media(s['_key'])
        s['media'] = [media_name for media_name in filenames]
        # print(s)
      except:
        status_code=500
        response=dict(
          status_code=status_code,
          message=f"Error while retrieving media info about Step {s['_key']}",
          error=traceback.format_exc()
        )
        raise HTTPException(status_code=status_code, detail=response)

    return job_steps


  def create_job_record(wo_data, phase_key, collection):
    if phase_key == 'default':
      phase = PhaseData(alias='default')
    else:
      phase = PhaseData(**tx.document(f'Phase/{phase_key}'))

    create_serial = phase_key == wo_data.phase_sequence[0]

    new_job_record = Job(
      wo_key = new_wo_record.key,
      wo_code = new_wo_record.wo_code,
      wo_line = new_wo_record.wo_line,
      phase_key = phase_key,
      phase_alias = phase.alias,
      create_serial = create_serial,
      product_key = wo_data.product_key,
      product_code = wo_data.product_code,
      product_description = wo_data.product_description,
      operation_key = phase.operation_key,
      parameters = phase.params,
      qt_planned = wo_data.qt_planned,
      step_sequence = get_procedure_for_new_job(phase_key)
    )

    prepped = jsonable_encoder(new_job_record, by_alias=True)
    new_job_record.key = collection.insert(prepped)['_key']
    return new_job_record
  
  try:
    new_job_records = [create_job_record(new_wo_record, phase_key, job_coll) for phase_key in new_wo_record.phase_sequence]

  except:
    status_code=500
    response = dict(
      status=status_code,
      message="There was a problem creating job records in the db",
      error=traceback.format_exc()
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )

  # Add work order to default site queue
  try:
    tx.aql.execute(Queries.ADD_WORK_ORDER_TO_QUEUE, bind_vars=dict(new_wo_key=new_wo_record.key))
    
  except:
    status_code=500
    response = dict(
      status=status_code,
      message="There was a problem adding the work order to the queue",
      error=traceback.format_exc()
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )

  # Commit transaction
  tx.commit_transaction()
  return APIResponse(
    message="Work order and jobs created",
    detail=dict(work_order=new_wo_record, jobs=new_job_records)
  )


# ----------------------------------------------------------------------


@router.patch('/work-order/{wo_key}')
async def update_work_order(
  wo_key: str, 
  new_due_date: str = Body(None),
  new_qt: float = Body(None)
  ):
  
  tx = db.begin_transaction(write=['WorkOrder'])
  update = dict(_key=wo_key)
  
  if new_due_date:
    update['due_by'] = new_due_date 
    
  if new_qt:
    update['qt_planned'] = new_qt

  updated_wo_data = tx.collection('WorkOrder').update(update, return_new=True)['new']
  
  if new_qt and updated_wo_data['status'] != WorkStatus.CREATED.value:
    status_code = 423
    response = dict(
      status=status_code,
      message="Work Order in progress or completed. Cannot modify the quantity",
    )
    raise HTTPException(status_code=status_code, detail=response)

  else:
    tx.commit_transaction()

  return APIResponse(detail=updated_wo_data)


# ----------------------------------------------------------------------


@router.get('/queue/site/{site_key}')
async def get_site_queue(site_key: str):

  cursor = db.aql.execute(Queries.GET_SITE_WORK_ORDER_DATA, bind_vars=dict(site_key=site_key))
  return APIResponse(detail=[wo for wo in cursor])


# ----------------------------------------------------------------------


@router.get('/work-order/{wo_key}')
async def get_wo_data(wo_key: str):

  wo_data = db.aql.execute(Queries.GET_WORK_ORDER_DATA, bind_vars=dict(wo_key=wo_key)).next()
  return APIResponse(detail=wo_data)


# ----------------------------------------------------------------------

@router.put('/queue')
async def update_queue(queue_update: Queue):

  try:
    match = dict(type=queue_update.type, site_key=queue_update.site_key)
    
    subqueue = queue_update.subqueue_target_key
    if subqueue:
      match['subqueue_target_key'] = subqueue

    db.collection('Queue').update_match(match, queue_update, keep_none=False, sync=True)
    
    # If updating the work order queue, reorder all job queues too
    if not subqueue:
      db.aql.execute(Queries.REORDER_JOB_QUEUES)

  except:
    status_code = 500
    response = dict(
      status=status_code,
      message="Could not update queue on the DB",
      error_str=traceback.format_exc()
    )
    raise HTTPException(status_code=status_code, detail=response)

  return APIResponse(detail="Queue updated")

# ----------------------------------------------------------------------


@router.get('/job')
async def get_job_list():

  db_resp = db.aql.execute("FOR j IN Job FILTER !j.trash RETURN j")
  job_list = [Job(**j) for j in db_resp]

  return APIResponse(detail=job_list)


# ----------------------------------------------------------------------


@router.get('/job-assignment')
async def get_assignment_list(user_key: str = None):

  result = db.aql.execute(Queries.GET_ASSIGNMENT_LIST, bind_vars=dict(user_key=user_key)).next()

  return APIResponse(detail=AssignmentsResponse(**result))


# ----------------------------------------------------------------------


@router.get('/job/{job_key}')
async def get_job_data(job_key: str):

  try:
    job_data = db.collection('Job').get(job_key)
  except:
    status_code=500
    response=dict(
      status_code=status_code,
      message="Couldn't retrieve data from the DB",
      error=traceback.format_exc()
    )
    raise HTTPException(status_code=status_code, detail=response)
  

  response=dict(
    message=f"Retrieved data for Job/{job_key}",
    detail=jsonable_encoder(job_data)
  )

  return APIResponse(**response)
 

# ----------------------------------------------------------------------


@router.post('/job/update')
async def update_jobs(job_updates:List[JobUpdate]):

  def update_target_queue(job_key, target_key, action, tx):

    try:
      if action == 'remove':
        tx.aql.execute(
          Queries.REMOVE_JOB_FROM_QUEUE, 
          bind_vars=dict(job_key=job_key, target_key=target_key)
        )

      if action == 'add':
        queue_match = dict(
          subqueue_target_key=target_key,
          site_key='0'
        )
        operator_queue_exists = tx.collection('Queue').find(queue_match).count()

        if operator_queue_exists:
          tx.aql.execute(
            Queries.ADD_JOB_TO_QUEUE, 
            bind_vars=dict(target_key=target_key, job_key=job_key)
          )

        else:
          tx.collection('Queue').insert(dict(
            **queue_match,
            type='o',
            jobs=[job_key]
          ))

    except:
      status_code = 500
      response =dict(
       status_code=status_code,
       message="Couldn't update queue on the db",
       error=traceback.format_exc()
      )
      raise HTTPException(status_code=status_code, detail=response)


  tx = db.begin_transaction(write=['Job', 'Queue'])
  job_db = tx.collection('Job')

  results = []
  
  try:
    for u in job_updates:

      if u.action == JobUpdateType.INSERT:
        new_job_record = jsonable_encoder(Job(**u.data), by_alias=True)
        new_job_data = job_db.insert(new_job_record, return_new=True)['new']

        if 'assigned_to' in u.data:
          update_target_queue(
            job_key=new_job_data['_key'], 
            target_key=new_job_data['assigned_to'],
            action='add',
            tx=tx
          )

      elif u.action == JobUpdateType.UPDATE:

        db_resp = job_db.update(u.data, return_new=True, return_old=True)
        new_job_data = db_resp['new']
        old_job_data = db_resp['old']

        if 'qt_planned' in u.data:
          update_job_progress(db=tx, job_key=db_resp['_key'])

        if 'assigned_to' in u.data:  
          if 'assigned_to' in old_job_data:
            update_target_queue(
              job_key=u.data['_key'],
              target_key=old_job_data['assigned_to'],
              action='remove',
              tx=tx    
            )
          
          update_target_queue(
            job_key=u.data['_key'], 
            target_key=u.data['assigned_to'],
            action='add',
            tx=tx
          ) 
          
      elif u.action == JobUpdateType.DELETE:
        new_job_data = job_db.update(dict(**u.data, trash=True), return_new=True)['new']
        
        if new_job_data['assigned_to']:
          update_target_queue(
            job_key=u.data['_key'],
            target_key=new_job_data['assigned_to'],
            action='remove',
            tx=tx
          )

      results.append(new_job_data)
    
    tx.commit_transaction()
    return APIResponse(detail=db_resp, message="Jobs updated successfully")

  except: 
    status_code = 500
    error_str = traceback.format_exc()

    response=dict(
      status_code=status_code,
      message="There was an error saving the updates",
      error=error_str 
    )

    raise HTTPException(status_code=status_code, detail=response)


