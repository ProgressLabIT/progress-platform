import traceback
from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, Body, HTTPException
from fastapi.encoders import jsonable_encoder

from models.process import PhaseData
from models.product import ProductDetails
from models.production import *
from utils.api import APIResponse
from utils.bom import get_bom_from_db
from utils.counter import generate_counter
from utils.db import db
from utils.dt import timestamp
from utils.process import search_step_media
from utils.product import get_product_docs
from utils.production import Queries, update_target_queue
from utils.traceability import update_job_progress


router = APIRouter()

# ----------------------------------------------------------------------


@router.post('/work-order')
async def create_work_order(new_wo: WorkOrderNew):

  # Initialize transaction
  tx = db.begin_transaction(write=['WorkOrder', 'Job', 'Queue', 'Counter'], read=['Phase', 'Product'])
  wo_coll = tx.collection('WorkOrder')
  job_coll = tx.collection('Job')
  product_coll = tx.collection('Product')

  # Create WO record
  def create_wo_record(wo: WorkOrderNew, collection):
    # data_in = jsonable_encoder(wo)
    new_wo_record = WorkOrderFull(
      **wo.dict(),
      wo_docs = get_product_docs(wo.product_key),
      wo_bom = get_bom_from_db(tx, wo.product_key)
    )
    prepped = jsonable_encoder(new_wo_record, by_alias=True)
    db_resp = collection.insert(prepped)
    new_wo_record.id = db_resp['_id']
    new_wo_record.key = db_resp['_key']
    return new_wo_record

  if not new_wo.wo_code:
    try:
      # Generate automatic wo_code if not present
      new_wo.wo_code = generate_counter(tx, 'work_order')
    except:
      tx.abort_transaction()
      status_code=500
      response = dict(
        status=status_code,
        message="Please provide a work order code or set up an automatic counter correctly",
        error=traceback.format_exc()
      )
      raise HTTPException(
        status_code=status_code,
        detail=response
      )

  try:
    product_data = ProductDetails(**product_coll.get(new_wo.product_key))
    new_wo.product_code = product_data.code
    new_wo.product_description = product_data.description

    if len(product_data.process_phases):
      new_wo.phase_sequence = product_data.process_phases
    else:
      new_wo.phase_sequence = ['default']
      # TODO: replace default alias with default operation (stored and cached in config)

    new_wo_record = create_wo_record(new_wo, wo_coll)

  except:
    tx.abort_transaction()
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
      tx.abort_transaction()
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
        tx.abort_transaction()
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

    first_phase = phase_key == wo_data.phase_sequence[0]
    new_job_record = Job(
      wo_key = wo_data.key,
      wo_code = wo_data.wo_code,
      phase_key = phase_key,
      phase_alias = phase.alias,
      first_phase = first_phase,
      product_key = wo_data.product_key,
      product_code = wo_data.product_code,
      product_description = wo_data.product_description,
      project_code = wo_data.project_code,
      operation_key = phase.operation_key,
      parameters = phase.params,
      qt_planned = wo_data.qt_planned,
      qt_next_batch = min([phase.params.production_batch_qt, wo_data.qt_planned]),
      next_batch_available = True if first_phase else False,
      step_sequence = get_procedure_for_new_job(phase_key),
      job_docs = wo_data.wo_docs,
      job_bom = [x for x in wo_data.wo_bom if x.phase_key == phase_key]
    )

    prepped = jsonable_encoder(new_job_record, by_alias=True)
    new_job_record.key = collection.insert(prepped)['_key']
    return new_job_record

  try:
    new_job_records = [create_job_record(new_wo_record, phase_key, job_coll) for phase_key in new_wo_record.phase_sequence]

  except:
    tx.abort_transaction()
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
    tx.abort_transaction()
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
  new_qt: float = Body(None),
  new_project_code: str = Body(None)
  ):

  tx = db.begin_transaction(write=['WorkOrder'])
  update = dict(_key=wo_key)

  if new_due_date:
    update['due_by'] = new_due_date

  if new_qt:
    update['qt_planned'] = new_qt

  if new_project_code:
    update['project_code'] = new_project_code
    match = { 'wo_key': wo_key }
    job_update = { 'project_code': new_project_code }
    tx.collection('Job').update_match(match, job_update)

  updated_wo_data = tx.collection('WorkOrder').update(update, return_new=True)['new']

  tx.commit_transaction()

  return APIResponse(detail=updated_wo_data)

# ----------------------------------------------------------------------


@router.get('/work-order/{wo_key}')
async def get_wo_data(wo_key: str):

  wo_data = db.aql.execute(Queries.GET_WORK_ORDER_DATA, bind_vars=dict(wo_key=wo_key)).next()
  return APIResponse(detail=wo_data)


# ----------------------------------------------------------------------

@router.delete('/work-order/{wo_key}')
async def delete_work_order(wo_key: str):
  try:
    tx = db.begin_transaction(write=['WorkOrder', 'Job', 'Queue'])

    # Delete Work Order
    wo_coll = tx.collection('WorkOrder')
    wo_data = wo_coll.get(wo_key)

    if wo_data['status'] not in [WorkStatus.CREATED.value, WorkStatus.PLANNED.value]:
      tx.abort_transaction()
      status_code=403
      response = dict(
        status=status_code,
        message=f"Work order {wo_key} cannot be deleted because it has been started",
      )
      raise HTTPException(
        status_code=status_code,
        detail=response
      )

    wo_coll.delete(wo_key)

    # Delete Jobs
    query = """
      FOR j in Job
      FILTER j.wo_key == @wo_key
      REMOVE j in Job
      LET removed = OLD
      RETURN removed._key
    """
    cursor = tx.aql.execute(query, bind_vars={ 'wo_key': wo_key })
    jobs_to_remove = [j for j in cursor]

    # Remove WorkOrder from queue
    q_coll = tx.collection('Queue')

    query = """
      FOR q in Queue
      FILTER q.type == 's'
      LET queue_update = { work_orders: REMOVE_VALUE(q.work_orders, @wo_key) }
      UPDATE q WITH queue_update in Queue
    """
    tx.aql.execute(query, bind_vars={ 'wo_key': wo_key })

    # Remove Jobs from queues
    query = """
      FOR q in Queue
      FILTER q.type == 'o'
      LET queue_update = { jobs: REMOVE_VALUES(q.jobs, @jobs_to_remove) }
      UPDATE q WITH queue_update in Queue
    """
    tx.aql.execute(query, bind_vars={ 'jobs_to_remove': jobs_to_remove })

    tx.commit_transaction()

    return APIResponse(message='Work order deleted correctly')

  except Exception as e:
    tx.abort_transaction()

    status_code=500
    response = dict(
      status=status_code,
      message=f"There has been a problem while deleting the work order",
      error=traceback.format_exc()
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )



# ----------------------------------------------------------------------


@router.get('/queue/site/{site_key}')
async def get_site_queue(site_key: str):

  cursor = db.aql.execute(Queries.GET_SITE_WORK_ORDER_DATA, bind_vars=dict(site_key=site_key))
  return APIResponse(detail=[wo for wo in cursor])




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

  try:
    result = db.aql.execute(Queries.GET_ASSIGNMENT_LIST, bind_vars=dict(user_key=user_key)).next()
    return APIResponse(detail=AssignmentsResponse(**result))

  except:
    status_code=500
    response=dict(
      status_code=status_code,
      message="Couldn't retrieve data from the DB",
      error=traceback.format_exc()
    )
    raise HTTPException(status_code=status_code, detail=response)


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

        results.append(new_job_data)

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

        results.append(db_resp)

      elif u.action == JobUpdateType.CLOSE:
        bind_vars = dict(
          job_key = u.data['_key'],
          stage = WorkStatus.CLOSED,
          end = timestamp(),
          notes = u.data['notes']
        )

        new_job_data = tx.aql.execute(
          Queries.CLOSE_JOB,
          bind_vars = bind_vars,
        ).next()

        if new_job_data['assigned_to']:
          update_target_queue(
            job_key = u.data['_key'],
            target_key = new_job_data['assigned_to'],
            action = 'remove',
            tx = tx
          )

        results.append(new_job_data)

    tx.commit_transaction()
    return APIResponse(detail=results, message="Jobs updated successfully")

  except:
    status_code = 500
    error_str = traceback.format_exc()

    response=dict(
      status_code=status_code,
      message="There was an error saving the updates",
      error=error_str
    )

    raise HTTPException(status_code=status_code, detail=response)


