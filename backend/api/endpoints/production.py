import traceback
from datetime import datetime
from typing import List

from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.encoders import jsonable_encoder

from models.product import ProductDetails
from models.production import *
from utils.api import APIResponse
from utils.bom import get_bom_from_db
from utils.counter import _generate_counter
from utils.db import db
from utils.dt import timestamp
from utils.exceptions import HTTPError
from utils.product import get_product_docs
from utils.production import (
  Queries,
  create_job_record,
  update_target_queue
)
from utils.traceability import _update_job_progress, Queries as TraceabilityQueries


router = APIRouter()

# ----------------------------------------------------------------------


@router.post('/work-order')
async def create_work_order(new_wo: WorkOrderNew):

  # Initialize transaction
  tx = db.begin_transaction(write=['WorkOrder', 'Job', 'Queue', 'Counter'], read=['Phase', 'Product'])
  wo_coll = tx.collection('WorkOrder')
  job_coll = tx.collection('Job')
  product_coll = tx.collection('Product')

  # Define WO record creation procedure
  def create_wo_record(wo: WorkOrderNew, collection):
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

  # 0. Handle Work Order Code
  # 0.1 Generate automatic wo_code if not provided
  if not new_wo.wo_code:
    try:
      new_wo.wo_code = _generate_counter(tx, 'work_order')
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

  # 0.2 Check Work Order Code is not already present
  wo_code_in_use = wo_coll.find({'wo_code': new_wo.wo_code }).count()
  if wo_code_in_use:
    tx.abort_transaction()
    raise HTTPException(
      status_code=409,
      detail="The work order code already exists. Please provide a new code. If you are using automatic counters, please check the configuration."
    )


  try:
    # 1. Fetch product data by code or key
    match = dict(active=True, trash=False)

    if not new_wo.product_key:
      match['code'] = new_wo.product_code

    else:
      match['_key'] = new_wo.product_key

    product_data = ProductDetails(**product_coll.find(match).next())

    if not new_wo.product_key:
      new_wo.product_key = product_data.key

    if not new_wo.product_code:
      new_wo.product_code = product_data.code

    if not new_wo.product_description:
      new_wo.product_description = product_data.description

    if len(product_data.process_phases):
      new_wo.phase_sequence = product_data.process_phases
    else:
      new_wo.phase_sequence = ['default']
      # TODO: replace default alias with default operation (stored and cached in config)

    new_wo_record = create_wo_record(new_wo, wo_coll)

  except StopIteration:
    tx.abort_transaction()
    status_code=404
    response = dict(
      status=status_code,
      message="There is no active product present with the key or code provided"
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )
    raise HTTPException()

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

  # 2. Create Jobs
  try:
    new_job_records = [create_job_record(tx, new_wo_record, phase_key, new_wo.qt_planned) for phase_key in new_wo_record.phase_sequence]

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

  # 3. Add work order to default site queue
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
  new_due_date: datetime | date | None = Body(None),
  new_from_date: datetime | date | None = Body(None),
  new_project_code: str | None = Body(None),
  notes: str | None = Body(None)
  ):

  try:
    tx = db.begin_transaction(write=['WorkOrder', 'Job'])
    wo_update = dict(_key=wo_key)
    job_match = dict(wo_key=wo_key)
    job_update = dict()

    if new_due_date is not None:
      wo_update['due_by'] = new_due_date

    if notes is not None:
      wo_update['notes'] = notes

    if new_from_date is not None:
      wo_update['start_from'] = new_from_date
      job_update.update({ 'start_from': new_from_date })

    if new_project_code is not None:
      wo_update['project_code'] = new_project_code
      job_update.update({ 'project_code': new_project_code })

    if new_project_code or new_from_date:
      tx.collection('Job').update_match(job_match, job_update)

    updated_wo_data = tx.collection('WorkOrder').update(wo_update, return_new=True)['new']

    tx.commit_transaction()

    return APIResponse(detail=updated_wo_data)

  except Exception:
    tx.abort_transaction()
    raise HTTPError(500, "There was a problem updating the work order")

# ----------------------------------------------------------------------

@router.patch('/work-order/{wo_key}/update-quantities')
async def update_work_order_quantities(
  wo_key: str,
  new_quantity: float | None = Body(None),
  job_updates: List[JobUpdate] = Body(None)
):
  """
  Updates the planned quantity of the work order and the planned quantity of each job.
  The progress of the work order and each job is updated accordingly.
  If the planned quantity of a job is updated to be equal or greater than the completed quantity,
  the job is closed and removed from the queue.
  If all the jobs are closed, the work order is closed and removed from the queue.
  """

  if not new_quantity:
    raise HTTPError(422, "Please provide a new work order quantity")

  if not job_updates:
    raise HTTPError(422, "Please provide the necessary job updates to ensure the new work order quantity is correctly planned for.")

  # TODO: Ensure job_updates are coherent with the work order update

  try:
    tx = db.begin_transaction(write=['WorkOrder', 'Job', 'Queue'])
    wo_data = WorkOrderFull(**tx.collection('WorkOrder').get(wo_key))

    for update in job_updates:
      if 'qt_planned' not in update.data:
        tx.abort_transaction()
        raise HTTPError(422, "Please provide a planned quantity for each job update")

      if update.action == JobUpdateType.INSERT:
        if 'phase_key' not in update.data:
          tx.abort_transaction()
          raise HTTPError(422, "Please provide a phase key for each new job")

        create_job_record(
          tx,
          wo_data = wo_data,
          **update.data
        )

      elif update.action == JobUpdateType.UPDATE:
        if '_key' not in update.data:
          tx.abort_transaction()
          raise HTTPError(422, "Please provide a job key for each update")

        result = tx.collection('Job').update(update.data, return_new=True)
        job = Job(**result['new'])

        _update_job_progress(db=tx, job_key=job.key)

        if job.qt_completed >= job.qt_planned:
          tx.aql.execute(
            Queries.CLOSE_JOB,
            bind_vars=dict(
              job_key=job.key,
              stage=WorkStatus.CLOSED,
              end=timestamp(),
              notes=job.notes
            ),
          )
      else:
        tx.abort_transaction()
        raise HTTPError(422, "Invalid job update action")

    updated_wo_data = tx.collection('WorkOrder').update(
      dict(
        _key=wo_key,
        qt_planned=new_quantity
      ),
      return_new=True
    )['new']

    # Handle status, progress, and performance metrics
    updated_wo_data = tx.aql.execute(
      TraceabilityQueries.UPDATE_WORK_ORDER,
      bind_vars=dict(wo_key=wo_key)
    ).next()

    # If the work order became closed, remove it from the queue
    if updated_wo_data['status'] == WorkStatus.CLOSED:
      tx.aql.execute(
        Queries.REMOVE_WORK_ORDER_FROM_QUEUE,
        bind_vars=dict(wo_key=wo_key)
      )

    tx.commit_transaction()

    return APIResponse(detail=updated_wo_data)

  except Exception:
    tx.abort_transaction()
    raise HTTPError(500, "There was a problem updating the work order quantities")


# ----------------------------------------------------------------------

@router.get('/work-order/{wo_key}')
async def get_wo_data(wo_key: str):

  wo_data = db.aql.execute(Queries.GET_WORK_ORDER_DATA, bind_vars=dict(wo_key=wo_key)).next()
  return APIResponse(detail=wo_data)


# ----------------------------------------------------------------------

@router.delete('/work-order/{wo_key}')
async def delete_work_order(wo_key: str):
  try:
    tx = db.begin_transaction(write=['WorkOrder', 'Job', 'Queue', 'issue_rel'])

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

    # Remove issues relationships (keep issue and rels to product/phase/etc)
    query = """
      FOR ir IN issue_rel
      FILTER ir._to IN flatten([@wo_id, @job_ids])
      REMOVE ir IN issue_rel
    """
    bind_vars = dict(
      wo_id = f'WorkOrder/{wo_key}',
      job_ids = [f'Job/{j}' for j in jobs_to_remove]
    )
    tx.aql.execute(query, bind_vars=bind_vars)

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

@router.get('/work-order')
async def search_work_orders(
  search: str | None = None,
  open: bool = False,
  closed: bool = True,
  limit: int = 100,
  time_start_from: datetime | None = None,
  time_start_to: datetime | None = None,
  time_end_from: datetime | None = None,
  time_end_to: datetime | None = None
):
  """By default searches for closed orders only. Can change the behavior by setting the `open` and `closed` parameters."""
  query = """
    FOR wo IN WorkOrder
    FILTER
      // closed and open parameters define whether these orders should be included in results
      (@closed ? true : wo.status != 'closed')
      && (@open ? true : wo.status == 'closed')
      && (@search ? (
        CONTAINS(LOWER(wo.wo_code), LOWER(@search))
        || CONTAINS(LOWER(wo.product_code), LOWER(@search))
        || CONTAINS(LOWER(wo.project_code), LOWER(@search))
        ) : true)
      && (@time_start_from ? wo.start >= @time_start_from : true)
      && (@time_start_to ? wo.start <= @time_start_to : true)
      && (@time_end_from ? wo.end >= @time_end_from : true)
      && (@time_end_to ? wo.end <= @time_end_to : true)
    SORT wo.end DESC
    LIMIT @limit

    LET issue_count = COUNT(FOR i IN issue_rel FILTER i._to == wo._id RETURN 1)

    LET now = DATE_NOW()
    LET work_sessions = (
      FOR ws IN WorkSession
      FILTER ws.work_order_key == wo._key && !ws.canceled
      LET duration = ws.active ? DATE_DIFF(ws.start, now, 'f') : ws.duration
      LET cost = ws.hourly_cost * duration / 3600000
      RETURN MERGE({ duration, cost })
    )
    LET processing_time = SUM(work_sessions[*].duration)
    LET processing_cost = SUM(work_sessions[*].cost)

    LET total_cost = processing_cost + wo.material_cost

    RETURN MERGE(wo, { issue_count, processing_time, processing_cost, total_cost })
  """
  try:
    cursor = db.aql.execute(query, bind_vars=dict(
      search = search,
      closed = closed,
      open = open,
      time_start_from = time_start_from,
      time_start_to = time_start_to,
      time_end_from = time_end_from,
      time_end_to = time_end_to,
      limit = limit
    ))
    # Return results as is without wrapping them in WorkOrderFull
    # otherwise, performance measure properties such as processing_time will be missing
    # as they are computed in the query and not specified in the WorkOrderFull model
    return [wo for wo in cursor]
  except StopIteration:
    return []


# ----------------------------------------------------------------------

@router.get('/queue/site/{site_key}')
async def get_site_queue(site_key: str):

  try:
    cursor = db.aql.execute(Queries.GET_SITE_WORK_ORDER_DATA, bind_vars=dict(site_key=site_key))
  except Exception:
    raise HTTPError(500, "There was an error while fetching work orders")
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
      bind_vars = dict(
        site_key = queue_update.site_key,
        target_key = None,
      )
      db.aql.execute(Queries.REORDER_JOB_QUEUES, bind_vars=bind_vars)

  except:
    status_code = 500
    response = dict(
      status=status_code,
      message="Could not update queue on the DB",
      error_str=traceback.format_exc()
    )
    raise HTTPException(status_code=status_code, detail=response)

  return APIResponse(detail="Queue updated")

@router.put('/queue/operator/{operator_key}')
async def update_operator_queue(
  operator_key: str,
  site_key: str | None = None,
  update: OperatorQueueUpdateInput = Body(...)
):
  try:
    updated_queue = db.aql.execute(
      """
      FOR q IN Queue
        FILTER q.type == 'o' && q.subqueue_target_key == @operator_key
        UPDATE q WITH @update IN Queue
        RETURN NEW
      """,
      bind_vars=dict(
        operator_key = operator_key,
        update = update.model_dump(exclude_none=True)
      )
    ).next()

    if update.independent == False:
      db.aql.execute(
        Queries.REORDER_JOB_QUEUES,
        bind_vars=dict(
          site_key = site_key, # default of 0 is handled in the query
          target_key = operator_key,
        )
      )

    return APIResponse(message="Queue updated", detail=updated_queue)
  except:
    raise HTTPError(500, "Could not update queue on the DB")

# ----------------------------------------------------------------------


@router.get('/job')
async def get_job_list(
  job_key: List[str] = Query(None),
  work_order_key: List[str] = Query(None),
  phase_key: List[str] = Query(None)
  ):

  query = """
    // parameters are passed as lists
    FOR j IN Job
    FILTER
      (@job_key ? POSITION(@job_key, j._key) : true)
      && (@work_order_key ? POSITION(@work_order_key, j.wo_key) : true)
      && (@phase_key ? POSITION(@phase_key, j.phase_key) : true)
      && !j.trash
    LET assigned_to = DOCUMENT(User, j.assigned_to)
    RETURN MERGE(j, { assigned_to })
  """

  db_resp = db.aql.execute(query, bind_vars=dict(
    job_key = job_key,
    work_order_key = work_order_key,
    phase_key = phase_key
  ))
  job_list = [Job(**j) for j in db_resp]

  return APIResponse(detail=job_list)


# ----------------------------------------------------------------------


@router.get('/job-assignment')
async def get_assignment_list(user_key: str | None = None):

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
  query = """
    FOR j IN Job
    FILTER j._key == @job_key
    LET issue_count = COUNT(FOR i IN issue_rel FILTER i._to == j._id RETURN 1)
    LET product_notes = DOCUMENT(Product, j.product_key).production_notes
    LET phase_notes = DOCUMENT(Phase, j.phase_key).notes
    LET order_notes = DOCUMENT(WorkOrder, j.wo_key).notes
    LET message_count = COUNT(FOR m IN message FILTER m._to == CONCAT('WorkOrder/', j.wo_key) RETURN 1)
    RETURN MERGE(j, { issue_count, product_notes, phase_notes, order_notes, message_count })
  """
  bind_vars = dict(job_key = job_key)

  try:
    job_data = db.aql.execute(query, bind_vars=bind_vars).next()

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
    detail=job_data
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
        wo_data = WorkOrderFull(**tx.collection('WorkOrder').get(u.data['work_order_key']))
        new_job_data = create_job_record(
          tx,
          wo_data = wo_data,
          **u.data
        )

        if 'assigned_to' in u.data:
          update_target_queue(
            job_key=new_job_data.key,
            target_key=new_job_data.assigned_to,
            action='add',
            tx=tx
          )

        results.append(new_job_data)

      elif u.action == JobUpdateType.UPDATE:
        db_resp = job_db.update(u.data, return_new=True, return_old=True)
        new_job_data = Job(**db_resp['new'])
        old_job_data = Job(**db_resp['old'])

        if 'qt_planned' in u.data:
          _update_job_progress(db=tx, job_key=new_job_data.key)

          if new_job_data.qt_completed >= new_job_data.qt_planned:
            bind_vars = dict(
              job_key=new_job_data.key,
              stage=WorkStatus.CLOSED,
              end=timestamp(),
              notes=new_job_data.notes
            )

            new_job_data = Job(**tx.aql.execute(
              Queries.CLOSE_JOB,
              bind_vars=bind_vars,
            ).next())

        if 'assigned_to' in u.data:
          if hasattr(old_job_data, 'assigned_to'):
            update_target_queue(
              job_key=u.data['_key'],
              target_key=old_job_data.assigned_to,
              action='remove',
              tx=tx
            )

          update_target_queue(
            job_key=u.data['_key'],
            target_key=u.data['assigned_to'],
            action='add',
            tx=tx
          )

        results.append(new_job_data)

      elif u.action == JobUpdateType.CLOSE:
        job_key = u.data['_key']
        current_job_data = Job(**job_db.get(job_key))

        # Delete job instead of closing if not started
        if current_job_data.stage == WorkStatus.CREATED:
          job_db.delete(job_key)
          # This is just a formality to pass on the WorkOrder code later on for wip update
          current_job_data.stage = WorkStatus.CLOSED
          results.append(current_job_data)

        else:
          bind_vars = dict(
            job_key = job_key,
            stage = WorkStatus.CLOSED,
            end = timestamp(),
            notes = u.data['notes']
          )

          new_job_data = Job(**tx.aql.execute(
            Queries.CLOSE_JOB,
            bind_vars = bind_vars,
          ).next())

          update_target_queue(
            job_key = job_key,
            target_key = current_job_data.assigned_to,
            action = 'remove',
            tx = tx
          )

          results.append(new_job_data)

        if 'assigned_to' in current_job_data:
          update_target_queue(
            job_key = job_key,
            target_key = current_job_data.assigned_to,
            action = 'remove',
            tx = tx
          )


    wo_key = results[0].wo_key
    work_order_data = tx.collection('WorkOrder').get(wo_key)

    # Update next_batch_available throughout the work order
    tx.aql.execute(
      TraceabilityQueries.UPDATE_NEXT_BATCH_AVAILABLE_STATE_FOR_JOBS_IN_PHASES,
      bind_vars = dict(
        wo_key = work_order_data['_key'],
        phase_keys = work_order_data['phase_sequence']
      )
    )

    tx.commit_transaction()
    return APIResponse(detail=results, message="Jobs updated successfully")

  except:
    tx.abort_transaction()
    status_code = 500
    error_str = traceback.format_exc()

    response=dict(
      status_code=status_code,
      message="There was an error saving the updates",
      error=error_str
    )

    raise HTTPException(status_code=status_code, detail=response)


