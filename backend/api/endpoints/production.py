import traceback
from datetime import datetime
from typing import List

from events.production.work_order_events import WorkOrderUpdatedEvent
from models.event import EventType

from fastapi import APIRouter, Body, HTTPException, Query, Depends
from utils import auth

from models.bom import WOBomLine
from models.product import ProductDetails
from models.production import *
from utils.api import APIResponse
from utils.counter import _generate_counter
from utils.db import db
from utils.exceptions import HTTPError
from utils.production import (
  Queries,
  create_job_record,
  create_wo_record,
  update_target_queue,
  close_job_and_update_queues,
  reassign_job_in_queues
)
from utils.traceability import (
  _update_job_progress,
  _get_phase_batch_available_state,
  Queries as TraceabilityQueries
)


router = APIRouter()

# ----------------------------------------------------------------------


@router.post('/work-order',
    dependencies=[Depends(auth.verify_token)],
    response_model=APIResponse,
    responses={
        409: {"description": "Work order code already exists"},
        500: {"description": "Counter misconfigured, product not found, or transaction failure"},
    })
async def create_work_order(new_wo: WorkOrderNew):
  """Create a new work order with its associated job records.

  Validates the product by key or code, generates a work order code via the
  configured counter if not provided, and inserts the WorkOrder, Job, and Queue
  records in a single ArangoDB transaction.

  **Emits:** *(direct transaction — no event class)*
  **Required scope:** `production:work-order:create`
  """

  # Initialize transaction
  tx = db.begin_transaction(write=['WorkOrder', 'Job', 'Queue', 'Counter'], read=['Phase', 'Product', 'Config'])
  wo_coll = tx.collection('WorkOrder')
  product_coll = tx.collection('Product')

  # 0. Handle Work Order Code
  # 0.1 Generate automatic wo_code if not provided
  if not new_wo.wo_code:
    try:
      counter_key = tx.collection('Config').get('system_counters')['work_orders']
      new_wo.wo_code = _generate_counter(tx, counter_key)
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

    if product_data.traceability_level:
      new_wo.traceability_level = product_data.traceability_level

    if product_data.serial_code_on_creation:
      new_wo.serial_code_on_creation = product_data.serial_code_on_creation

    new_wo_record = create_wo_record(tx, new_wo)

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

  except Exception:
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


@router.patch('/work-order/{wo_key}',
    dependencies=[Depends(auth.verify_token)],
    response_model=APIResponse,
    responses={
        500: {"description": "Transaction failure while updating the work order"},
    })
async def update_work_order(
  wo_key: str,
  new_due_date: datetime | date | None = Body(None),
  new_from_date: datetime | date | None = Body(None),
  new_project_code: str | None = Body(None),
  new_bom: list[WOBomLine] | None = Body(None),
  new_output_position_key: str | None = Body(None),
  notes: str | None = Body(None)
  ):
  """Update editable fields of an existing work order.

  Accepts any combination of due date, start date, project code, BOM lines,
  output position, and notes. Updates matching Job records for fields that
  propagate to jobs (start date, project code). Commits all changes in a
  single transaction.

  **Emits:** WORK_ORDER_UPDATED
  **Required scope:** `production:work-order:update`
  """

  try:
    event = WorkOrderUpdatedEvent(info=dict(
      event_type=EventType.WORK_ORDER_UPDATED,
      work_order_key=wo_key,
      new_due_date=new_due_date,
      new_from_date=new_from_date,
      new_project_code=new_project_code,
      new_bom=new_bom,
      new_output_position_key=new_output_position_key,
      notes=notes,
      primary=True,
    ))
    event.save()
    return APIResponse(detail=event.response)

  except ValueError as e:
    raise HTTPException(status_code=422, detail=dict(
      error_type=e.__class__.__name__,
      message=e.args[0] if e.args else None,
    ))

  except Exception:
    raise HTTPError(500, "There was a problem updating the work order")

# ----------------------------------------------------------------------

@router.patch('/work-order/{wo_key}/update-quantities',
    dependencies=[Depends(auth.verify_token)],
    response_model=APIResponse,
    responses={
        422: {"description": "Missing or inconsistent quantity/job update payload"},
        500: {"description": "Transaction failure while updating quantities"},
    })
async def update_work_order_quantities(
  wo_key: str,
  new_quantity: float | None = Body(None),
  job_updates: List[JobUpdate] = Body(None)
):
  """Update the planned quantity of a work order and its jobs.

  Accepts a new work order quantity and a list of job-level updates (insert,
  update, or close). Recalculates progress for affected jobs; closes jobs whose
  completed quantity meets or exceeds the new planned quantity. Removes or
  re-adds the work order from the site queue based on resulting status.

  **Emits:** *(direct transaction — no event class)*
  **Required scope:** `production:work-order:update-quantities`
  """

  if not new_quantity:
    raise HTTPError(422, "Please provide a new work order quantity")

  if not job_updates:
    raise HTTPError(422, "Please provide the necessary job updates to ensure the new work order quantity is correctly planned for.")

  # TODO: Ensure job_updates are coherent with the work order update

  try:
    # Include Event, Task, and event_source collections to ensure JobClosed events are stored correctly
    tx = db.begin_transaction(write=['WorkOrder', 'Job', 'Queue', 'Event', 'Task', 'event_source'])
    wo_data = WorkOrderFull(**tx.collection('WorkOrder').get(wo_key))

    for update in job_updates:
      if 'qt_planned' not in update.data:
        raise HTTPError(422, "Please provide a planned quantity for each job update")

      if update.action == JobUpdateType.INSERT:
        if 'phase_key' not in update.data:
          raise HTTPError(422, "Please provide a phase key for each new job")

        phase_doc = tx.document(f'Phase/{update.data["phase_key"]}')
        production_batch_qt = phase_doc.get('params', {}).get('production_batch_qt', 0) if phase_doc else 0
        update.data['next_batch_available'] = _get_phase_batch_available_state(
          db=tx,
          wo_key=wo_key,
          phase_key=update.data['phase_key'],
          qt_planned=update.data['qt_planned'],
          production_batch_qt=production_batch_qt,
        )

        create_job_record(
          tx,
          wo_data = wo_data,
          **update.data
        )

      elif update.action == JobUpdateType.UPDATE:
        if '_key' not in update.data:
          raise HTTPError(422, "Please provide a job key for each update")

        result = tx.collection('Job').update(update.data, return_new=True, return_old=True)
        job = Job(**result['new'])

        _update_job_progress(db=tx, job_key=job.key)

        if job.qt_completed >= job.qt_planned:
          close_job_and_update_queues(tx, Job(**result['old']))

      elif update.action == JobUpdateType.CLOSE:
        if '_key' not in update.data:
          raise HTTPError(422, "Please provide a job key for each close action")
        current_job = Job(**tx.collection('Job').get(update.data['_key']))
        close_job_and_update_queues(tx, current_job, notes=update.data.get('notes'))
      else:
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

    # Handle work order status changes in the queue
    if wo_data.status != WorkStatus.CLOSED and updated_wo_data['status'] == WorkStatus.CLOSED:
      tx.aql.execute(
        Queries.REMOVE_WORK_ORDER_FROM_QUEUE,
        bind_vars=dict(wo_key=wo_key)
      )

    if wo_data.status == WorkStatus.CLOSED and updated_wo_data['status'] != WorkStatus.CLOSED:
      tx.aql.execute(
        Queries.ADD_WORK_ORDER_TO_QUEUE,
        bind_vars=dict(new_wo_key=wo_key)
      )

    tx.commit_transaction()
    return APIResponse(detail=updated_wo_data)

  except Exception as e:
    if isinstance(e, HTTPError):
      raise e

    else:
      raise HTTPError(500, "There was a problem updating the work order quantities")

  finally:
    if tx.transaction_status() == 'running': # See transaction statuses in the HTTP API of ArangoDB
      tx.abort_transaction()


# ----------------------------------------------------------------------

@router.get('/work-order/{wo_key}',
    dependencies=[Depends(auth.verify_token)],
    response_model=APIResponse,
    responses={
        404: {"description": "Work order not found"},
        500: {"description": "Database error while fetching work order data"},
    })
async def get_wo_data(wo_key: str):
  """Fetch full data for a single work order by key.

  Executes the GET_WORK_ORDER_DATA AQL query and returns the enriched work
  order document including computed fields.

  **Emits:** *(read-only — no event)*
  **Required scope:** `production:work-order:read`
  """

  try:
    wo_data = db.aql.execute(Queries.GET_WORK_ORDER_DATA, bind_vars=dict(wo_key=wo_key)).next()
    return APIResponse(detail=wo_data)
  except StopIteration:
    raise HTTPException(status_code=404, detail="Work order not found")
  except Exception as e:
    status_code=500
    response = dict(
      status=status_code,
      message=f"There has been a problem while fetching the work order",
      error=traceback.format_exc()
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )


# ----------------------------------------------------------------------

@router.get('/work-order/{wo_key}/traceability',
    dependencies=[Depends(auth.verify_token)],
    response_model=APIResponse,
    responses={
        500: {"description": "Database error while fetching traceability data"},
    })
async def get_wo_traceability_data(wo_key: str):
  """Fetch serial traceability data for a work order.

  Returns the list of serial records linked to the work order, as produced
  by the GET_WORK_ORDER_TRACEABILITY_DATA AQL query.

  **Emits:** *(read-only — no event)*
  **Required scope:** `production:work-order:read`
  """
  try:
    wo_traceability_data = list(db.aql.execute(
      Queries.GET_WORK_ORDER_TRACEABILITY_DATA,
      bind_vars=dict(wo_key=wo_key)
    ))
    return APIResponse(detail=wo_traceability_data)
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error fetching serials from the db.",
        error=traceback.format_exc()
      )
    )


# ----------------------------------------------------------------------

@router.delete('/work-order/{wo_key}',
    dependencies=[Depends(auth.verify_token)],
    response_model=APIResponse,
    responses={
        403: {"description": "Work order has been started and cannot be deleted"},
        500: {"description": "Transaction failure while deleting the work order"},
    })
async def delete_work_order(wo_key: str):
  """Delete a work order and its associated jobs from the system.

  Only work orders in `created` or `planned` status may be deleted. Removes
  the work order document, all child Job records, queue entries (site and
  operator), and any issue relationship edges in a single transaction.

  **Emits:** *(direct transaction — no event class)*
  **Required scope:** `production:work-order:delete`
  """
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

  except HTTPException:
    raise
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

@router.get('/work-order-search-opts',
    dependencies=[Depends(auth.verify_token)],
    response_model=list,
    responses={})
async def search_work_orders():
  """Return distinct work order code/project code options for search filters.

  Executes the GET_WORK_ORDER_SEARCH_OPTIONS AQL query and returns a flat list
  of option objects used to populate search dropdowns in the UI.

  **Emits:** *(read-only — no event)*
  **Required scope:** `production:work-order:read`
  """

  try:
    cursor = db.aql.execute(Queries.GET_WORK_ORDER_SEARCH_OPTIONS, bind_vars=dict())
    return [opt for opt in cursor]
  except StopIteration:
    return []

# ----------------------------------------------------------------------

@router.get('/work-order',
    dependencies=[Depends(auth.verify_token)],
    response_model=list,
    responses={})
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
  """Search and filter work orders with optional date range and status filters.

  By default returns closed orders only. Includes computed performance metrics
  (processing time, processing cost, total cost) and open issue count per work
  order. Results sorted by end date descending, capped by `limit`.

  **Emits:** *(read-only — no event)*
  **Required scope:** `production:work-order:read`
  """
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
      FILTER ws.work_order_key == wo._key && ws.canceled == null
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

@router.get('/queue/site/{site_key}',
    dependencies=[Depends(auth.verify_token)],
    response_model=APIResponse,
    responses={
        500: {"description": "Database error while fetching site queue"},
    })
async def get_site_queue(site_key: str):
  """Fetch the work order queue for a given site.

  Executes GET_SITE_WORK_ORDER_DATA and returns the ordered list of work
  orders currently in the site-level queue, enriched with job and progress data.

  **Emits:** *(read-only — no event)*
  **Required scope:** `production:queue:read`
  """

  try:
    cursor = db.aql.execute(Queries.GET_SITE_WORK_ORDER_DATA, bind_vars=dict(site_key=site_key))
  except Exception:
    raise HTTPError(500, "There was an error while fetching work orders")
  return APIResponse(detail=[wo for wo in cursor])




# ----------------------------------------------------------------------

@router.put('/queue',
    dependencies=[Depends(auth.verify_token)],
    response_model=APIResponse,
    responses={
        500: {"description": "Database error while updating the queue"},
    })
async def update_queue(queue_update: Queue):
  """Replace the ordered sequence of a site or operator queue.

  Accepts a Queue document with the new ordered work_orders or jobs list.
  When updating the site-level queue (no subqueue_target_key), also
  re-sorts all subordinate job queues to match the new work order order.

  **Emits:** *(direct transaction — no event class)*
  **Required scope:** `production:queue:update`
  """
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

@router.put('/queue/operator/{operator_key}',
    dependencies=[Depends(auth.verify_token)],
    response_model=APIResponse,
    responses={
        500: {"description": "Database error while updating the operator queue"},
    })
async def update_operator_queue(
  operator_key: str,
  site_key: str | None = None,
  update: OperatorQueueUpdateInput = Body(...)
):
  """Update the job queue for a specific operator.

  Replaces the operator's ordered job list and optionally toggles the
  `independent` flag that controls whether the queue follows the global
  work order order. When `independent` is set to False, triggers a
  full reorder of job queues for the target site.

  **Emits:** *(direct transaction — no event class)*
  **Required scope:** `production:queue:update`
  """
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


@router.get('/job',
    dependencies=[Depends(auth.verify_token)],
    response_model=APIResponse,
    responses={})
async def get_job_list(
  job_key: List[str] = Query(None),
  work_order_key: List[str] = Query(None),
  phase_key: List[str] = Query(None)
  ):
  """Return a filtered list of jobs with their assigned operator details.

  Filters by any combination of job key(s), work order key(s), and phase
  key(s). Each result is merged with the resolved User document for the
  assignee. Returns an empty list if no jobs match.

  **Emits:** *(read-only — no event)*
  **Required scope:** `production:job:read`
  """

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


@router.get('/job-assignment',
    dependencies=[Depends(auth.verify_token)],
    response_model=APIResponse,
    responses={
        500: {"description": "Database error while fetching assignment list"},
    })
async def get_assignment_list(user_key: str | None = None):
  """Fetch the current job assignment state grouped by operator.

  Returns operators with their assigned jobs and the list of unassigned
  jobs, as produced by the GET_ASSIGNMENT_LIST AQL query. Optionally
  filtered by a specific user key.

  **Emits:** *(read-only — no event)*
  **Required scope:** `production:job:read`
  """

  try:
    result = db.aql.execute(Queries.GET_ASSIGNMENT_LIST, bind_vars=dict(user_key=user_key)).next()
    return APIResponse(detail=result)
  except:
    status_code=500
    response=dict(
      status_code=status_code,
      message="Couldn't retrieve data from the DB",
      error=traceback.format_exc()
    )
    raise HTTPException(status_code=status_code, detail=response)


# ----------------------------------------------------------------------


@router.get('/job/{job_key}',
    dependencies=[Depends(auth.verify_token)],
    response_model=APIResponse,
    responses={
        500: {"description": "Database error while fetching job data"},
    })
async def get_job_data(job_key: str):
  """Fetch full working data for a single job by key.

  Executes GET_WORKING_JOB_DATA which returns the job document enriched
  with step execution progress, active batch info, and operator details.

  **Emits:** *(read-only — no event)*
  **Required scope:** `production:job:read`
  """

  bind_vars = dict(job_key = job_key)

  try:
    job_data = db.aql.execute(Queries.GET_WORKING_JOB_DATA, bind_vars=bind_vars).next()

  except StopIteration:
    raise HTTPException(status_code=404, detail=f"Job/{job_key} not found")

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


@router.get('/work-session',
    dependencies=[Depends(auth.verify_token)],
    response_model=APIResponse,
    responses={
        500: {"description": "Database error while fetching active work session"},
    })
async def get_active_work_session_for_job(job_key: str):
  """Fetch the currently active work session for a job.

  Executes GET_ACTIVE_WORK_SESSION_FOR_JOB and returns the most recent
  unclosed WorkSession record for the given job key.

  **Emits:** *(read-only — no event)*
  **Required scope:** `production:work-session:read`
  """

  bind_vars = dict(job_key = job_key)

  try:
    ws = db.aql.execute(Queries.GET_ACTIVE_WORK_SESSION_FOR_JOB, bind_vars=bind_vars).next()

  except:
    status_code=500
    response=dict(
      status_code=status_code,
      message="Couldn't retrieve data from the DB",
      error=traceback.format_exc()
    )
    raise HTTPException(status_code=status_code, detail=response)


  response=dict(
    message=f"Retrieved session for Job/{job_key}",
    detail=ws
  )

  return APIResponse(**response)



# ----------------------------------------------------------------------


@router.post('/job/update',
    dependencies=[Depends(auth.verify_token)],
    response_model=APIResponse,
    responses={
        500: {"description": "Transaction failure while applying job updates"},
    })
async def update_jobs(job_updates:List[JobUpdate]):
  """Apply a batch of job insert, update, or close operations.

  Accepts a list of JobUpdate items each specifying an action (insert,
  update, close) and a data dict. For each affected work order, recalculates
  progress and adjusts queue membership (adds back or removes) based on the
  resulting status. All mutations run in a single ArangoDB transaction.

  **Emits:** *(direct transaction — no event class)*
  **Required scope:** `production:job:update`
  """

  tx = db.begin_transaction(write=['Job', 'Queue', 'WorkOrder', 'Event', 'event_source'])
  job_db = tx.collection('Job')

  results = []

  try:
    # Collect affected work orders to update them after job modifications
    affected_wo_keys = set()

    for u in job_updates:

      if u.action == JobUpdateType.INSERT:
        wo_data = WorkOrderFull(**tx.collection('WorkOrder').get(u.data['work_order_key']))

        # Get next batch available state for the job
        phase_doc = tx.document(f'Phase/{u.data["phase_key"]}')
        production_batch_qt = phase_doc.get('params', {}).get('production_batch_qt', 0) if phase_doc else 0
        u.data['next_batch_available'] = _get_phase_batch_available_state(
          db=tx,
          wo_key=u.data['work_order_key'],
          phase_key=u.data['phase_key'],
          qt_planned=u.data['qt_planned'],
          production_batch_qt=production_batch_qt,
        )

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

        affected_wo_keys.add(new_job_data.wo_key)
        results.append(new_job_data)

      elif u.action == JobUpdateType.UPDATE:
        db_resp = job_db.update(u.data, return_new=True, return_old=True)
        new_job_data = Job(**db_resp['new'])
        old_job_data = Job(**db_resp['old'])

        if 'qt_planned' in u.data:
          _update_job_progress(db=tx, job_key=new_job_data.key)

          if new_job_data.qt_completed >= new_job_data.qt_planned:
            new_job_data = close_job_and_update_queues(tx, old_job_data)

        if 'assigned_to' in u.data:
          reassign_job_in_queues(tx, job_key=u.data['_key'], old_assignee=getattr(old_job_data, 'assigned_to', None), new_assignee=u.data['assigned_to'])

        affected_wo_keys.add(new_job_data.wo_key)
        results.append(new_job_data)

      elif u.action == JobUpdateType.CLOSE:
        job_key = u.data['_key']
        current_job_data = Job(**job_db.get(job_key))

        # Delete job instead of closing if not started
        if current_job_data.stage == WorkStatus.CREATED:
          job_db.delete(job_key)
          # This is just a formality to pass on the WorkOrder code later on for wip update
          current_job_data.stage = WorkStatus.CLOSED
          affected_wo_keys.add(current_job_data.wo_key)
          results.append(current_job_data)

        else:
          new_job_data = close_job_and_update_queues(tx, current_job_data, notes=u.data.get('notes'))
          affected_wo_keys.add(new_job_data.wo_key)
          results.append(new_job_data)


    # Update all affected work orders
    for wo_key in affected_wo_keys:
      work_order_data = tx.collection('WorkOrder').get(wo_key)

      # Update work order
      updated_wo_data = tx.aql.execute(
        TraceabilityQueries.UPDATE_WORK_ORDER,
        bind_vars = dict(wo_key = wo_key)
      ).next()

      # Handle work order status changes in the queue
      if work_order_data['status'] != WorkStatus.CLOSED and updated_wo_data['status'] == WorkStatus.CLOSED:
        tx.aql.execute(
          Queries.REMOVE_WORK_ORDER_FROM_QUEUE,
          bind_vars=dict(wo_key=wo_key)
        )

      if work_order_data['status'] == WorkStatus.CLOSED and updated_wo_data['status'] != WorkStatus.CLOSED:
        tx.aql.execute(
          Queries.ADD_WORK_ORDER_TO_QUEUE,
          bind_vars=dict(new_wo_key=wo_key)
        )

    tx.commit_transaction()
    return APIResponse(detail=results, message="Jobs updated successfully")

  except Exception:
    raise HTTPError(500, "There was an error saving the updates")

  finally:
    if tx.transaction_status() == 'running':
      tx.abort_transaction()

@router.get("/job/{job_key}/time",
    dependencies=[Depends(auth.verify_token)],
    response_model=APIResponse,
    responses={
        500: {"description": "Database error while fetching elapsed time"},
    })
async def get_job_elapsed_time(job_key):
  """Fetch elapsed and estimated time metrics for a job.

  Executes GET_JOB_ELAPSED_TIME and returns timing data including elapsed
  time, estimated remaining time, and on-time status for the given job.

  **Emits:** *(read-only — no event)*
  **Required scope:** `production:job:read`
  """
  try:
    bind_vars = dict(job_key = job_key)
    progress_data = db.aql.execute(Queries.GET_JOB_ELAPSED_TIME, bind_vars=bind_vars).next()
  except:
    status_code=500
    response=dict(
      status_code=status_code,
      message="Couldn't retrieve data from the DB",
      error=traceback.format_exc()
    )
    raise HTTPException(status_code=status_code, detail=response)


  response=dict(
    message=f"Retrieved elapsed time for job {job_key}",
    detail=progress_data
  )

  return APIResponse(**response)

