import traceback
import os
import shutil

from fastapi import APIRouter, HTTPException, Depends

from utils.db import db
from utils.serial import Queries as SerialQueries
from models.production import WorkStatus
from utils.api import APIResponse
from utils import auth


router = APIRouter()

traceability_collections = [
    'Batch',
    'batch_serial',
    'contains',
    'Event',
    'Job',
    'Queue',
    'StepExecutionData',
    'wip',
    'WorkOrder',
    'WorkSession',
    'Issue',
    'issue_rel',
    'message',
    'Serial',
  ]

media_directories = [
    'serial',
    'traceability',
    'issue'
  ]


def clean_dir(path):
 if os.path.isdir(path):
      shutil.rmtree(path)

@router.delete(
  '/reset/prod',
  response_model=APIResponse,
  responses={
    500: {"description": "Transaction or filesystem error during truncation"},
  },
  dependencies=[Depends(auth.verify_token)],
)
async def reset_production_and_traceability_data():
  """Truncate all production and traceability collections.

  Deletes every document from the traceability collections (Batch, Job,
  WorkOrder, Event, Serial, Issue, etc.) within a single ArangoDB transaction,
  then re-inserts a clean site Queue document and removes media sub-directories
  (`serial`, `traceability`, `issue`) from the `/media` volume.

  **WARNING:** This operation is irreversible. Use only in development or
  controlled staging environments.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `admin:operation:reset-prod`
  """
  # TODO: Delete also all files linked to StepExecutionData

  try:
    tx = db.begin_transaction(write=traceability_collections)

    for c in traceability_collections:
      tx.collection(c).truncate()

    tx.collection('Queue').insert(dict(
      type = 's', #What the queue refers to.
      site_key = '0',
      subqueue_target_key = None,
      work_orders = [],
      jobs = []
    ))

    tx.commit_transaction()

    for dir in media_directories:
      clean_dir("/media/"+dir)

    return APIResponse(message='Reset of Production and Traceability data successful')

  except Exception:
    tx.abort_transaction()
    raise HTTPException(
      status_code=500,
      detail=traceback.format_exc()
    )


async def get_work_order_jobs(work_order_key):
  cursor = db.collection('Job').find(dict(wo_key=work_order_key))
  return [j['_key'] for j in cursor]


@router.delete(
  '/reset/inventory',
  response_model=APIResponse,
  responses={
    500: {"description": "Database error while truncating inventory collections"},
  },
  dependencies=[Depends(auth.verify_token)],
)
async def reset_warehouse_data():
  """Truncate inventory movement data.

  Deletes all records from `movement` and `MovementList` collections, then
  removes all `is_in_position` edges whose `_from` vertex is a `Product`
  document. Position-definition documents (locations, bins) are preserved.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `admin:operation:reset-inventory`
  """
  try:
    for c in ['movement', 'MovementList']:
      db.collection(c).truncate()
    db.aql.execute("""
      FOR i IN is_in_position
      FILTER IS_SAME_COLLECTION(Product, i._from)
      REMOVE i IN is_in_position
    """)
    return APIResponse(message='Reset of inventory data successful')

  except Exception:
    tx.abort_transaction()
    raise HTTPException(
      status_code=500,
      detail=traceback.format_exc()
    )


@router.delete(
  '/force-delete-work-order/{work_order_key}',
  response_model=APIResponse,
  responses={
    404: {"description": "WorkOrder with the given key does not exist"},
    500: {"description": "Transaction error during cascade deletion"},
  },
  dependencies=[Depends(auth.verify_token)],
)
async def force_delete_work_order_data(work_order_key: str):
  """Permanently delete a work order and all related traceability data.

  Cascades through Job, Batch, StepExecutionData, WorkSession, Event,
  batch_serial, contains, wip and issue_rel records linked to the given
  work order key. Removes the work order from the site Queue. This is a
  hard delete — no audit trail is preserved. Use only when a work order
  was created in error.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `admin:operation:force-delete-work-order`
  """

  # Check if the work order actually exists
  if not db.collection('WorkOrder').has(work_order_key):
    raise HTTPException(status_code=404, detail="Work order key could not be found in the database")

  # 0. Setup transaction — Queue is a shared site singleton; lock it exclusively
  # so concurrent force-deletes serialize instead of racing for the doc lock.
  tx = db.begin_transaction(
    write=[c for c in traceability_collections if c != 'Queue'],
    exclusive=['Queue'],
  )

  try:
    match = dict(work_order_key=work_order_key)

    # 1. Delete Events, Batches, wip, WorkSessions and WorkOrder based on work_order_key
    tx.collection('Event').delete_match(match)
    tx.collection('Batch').delete_match(match)
    tx.collection('wip').delete_match(dict(wo_key=work_order_key))
    tx.collection('WorkSession').delete_match(match)
    tx.collection('WorkOrder').delete(work_order_key)

    # Delete batch_serial records
    tx.aql.execute(SerialQueries.CLEANUP_SERIAL_BATCH_LINKS)

    # Delete jobs and get job list
    job_delete_query = """
      FOR j IN Job
      FILTER j.wo_key == @work_order_key
      REMOVE j IN Job
      LET removed = OLD
      RETURN removed._key
    """
    cursor = tx.aql.execute(job_delete_query, bind_vars=match)
    jobs_to_delete = [j for j in cursor]

    # Delete StepExecutionData based on deleted job_key
    step_data_delete_query = """
      FOR s IN StepExecutionData
      FILTER s.job_key IN @jobs_to_delete
      REMOVE s IN StepExecutionData
    """
    tx.aql.execute(step_data_delete_query, bind_vars=dict(jobs_to_delete=jobs_to_delete))

    # Delete Work Order and Jobs from Queue
    queue_update_query = """
      FOR q IN Queue
      LET jobs = MINUS(q.jobs, @jobs_to_delete)
      LET work_orders = REMOVE_VALUE(q.work_orders, @work_order_key)
      UPDATE q WITH { jobs, work_orders } in Queue
    """
    bind_vars = dict(work_order_key=work_order_key, jobs_to_delete=jobs_to_delete)
    tx.aql.execute(queue_update_query, bind_vars=bind_vars)

    # Remove issues relationships (keep issue and rels to product/phase/etc)
    query = """
      FOR ir IN issue_rel
      FILTER ir._to IN flatten([@wo_id, @job_ids])
      REMOVE ir IN issue_rel
    """
    bind_vars = dict(
      wo_id = f'WorkOrder/{work_order_key}',
      job_ids = [f'Job/{j}' for j in jobs_to_delete]
    )
    tx.aql.execute(query, bind_vars=bind_vars)

    # Cleanup batch_serial/contains records pointing to deleted batches
    # TODO: Use named graphs to have this done automatically when deleting batches
    tx.aql.execute("""
      FOR b in batch_serial
      FILTER DOCUMENT(b._from) == null
      REMOVE b IN batch_serial
    """)

    tx.aql.execute("""
      FOR c in contains
      FILTER DOCUMENT(c._from) == null
      REMOVE c IN contains
    """)


    # 9. Commit and return
    tx.commit_transaction()
    return APIResponse(message=f"All data related to WorkOrder {work_order_key} has been deleted.")

  except Exception:
    tx.abort_transaction()
    raise HTTPException(status_code=500, detail=traceback.format_exc())



