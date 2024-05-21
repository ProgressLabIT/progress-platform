import traceback

from fastapi import APIRouter, HTTPException

from commons.utils.db import db
from models.production import WorkStatus
from commons.kafka_utils.kafka_admin import KafkaAdmin
from utils.api import APIResponse

router = APIRouter()

traceability_collections = [
    'Batch',
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
    'batch_serial'
  ]

@router.delete('/reset/prod')
async def reset_production_and_traceability_data():

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

    return 'Reset of Production and Traceability data successful'

  except Exception:
    tx.abort_transaction()
    raise HTTPException(
      status_code=500,
      detail=traceback.format_exc()
    )


async def get_work_order_jobs(work_order_key):
  cursor = db.collection('Job').find(dict(wo_key=work_order_key))
  return [j['_key'] for j in cursor]



@router.delete('/force-delete-work-order/{work_order_key}')
async def force_delete_work_order_data(work_order_key: str):

  # Check if the work order actually exists
  if not db.collection('WorkOrder').has(work_order_key):
    raise HTTPException(status_code=404, detail="Work order key could not be found in the database")

  # 0. Setup transaction
  tx = db.begin_transaction(write=traceability_collections)

  try:
    match = dict(work_order_key=work_order_key)

    # 1. Delete Events, Batches, wip, WorkSessions and WorkOrder based on work_order_key
    tx.collection('Event').delete_match(match)
    tx.collection('Batch').delete_match(match)
    tx.collection('wip').delete_match(dict(wo_key=work_order_key))
    tx.collection('WorkSession').delete_match(match)
    tx.collection('WorkOrder').delete(work_order_key)

    # 2. Delete jobs and get job list
    job_delete_query = """
      FOR j IN Job
      FILTER j.wo_key == @work_order_key
      REMOVE j IN Job
      LET removed = OLD
      RETURN removed._key
    """
    cursor = tx.aql.execute(job_delete_query, bind_vars=match)
    jobs_to_delete = [j for j in cursor]

    # 3. Delete StepExecutionData based on deleted job_key
    step_data_delete_query = """
      FOR s IN StepExecutionData
      FILTER POSITION(@jobs_to_delete, s.job_key)
      REMOVE s IN StepExecutionData
    """
    tx.aql.execute(step_data_delete_query, bind_vars=dict(jobs_to_delete=jobs_to_delete))

    # 3. Delete Work Order and Jobs from Queue
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

    # 9. Commit and return
    tx.commit_transaction()
    return f"All data related to WorkOrder {work_order_key} has been deleted."

  except Exception:
    tx.abort_transaction()
    raise HTTPException(status_code=500, detail=traceback.format_exc())


@router.put("/kafka/topic/{topic}")
async def put_kafka_topic(topic: str):
  try:
    message = KafkaAdmin.getInstance().create_topic(topic)
    return APIResponse(message = message)
  except:
    status_code = 500
    response = dict(
      status=status_code,
      message="There was an error while creating the topic",
      error=traceback.format_exc(),
    )
    raise HTTPException(status_code=status_code, detail=response)

@router.delete("/kafka/topic/{topic}")
async def delete_kafka_topic(topic: str):
  try:
    message = KafkaAdmin.getInstance().delete_topic(topic)
    return APIResponse(message = message)
  except:
    status_code = 500
    response = dict(
      status=status_code,
      message="There was an error while deleting the topic",
      error=traceback.format_exc(),
    )
    raise HTTPException(status_code=status_code, detail=response)

@router.get("/kafka/topics")
async def list_kafka_topic():
  try:
    message = KafkaAdmin.getInstance().list_topics()
    return APIResponse(message = message)
  except:
    status_code = 500
    response = dict(
      status=status_code,
      message="There was an error while retreiving topic list",
      error=traceback.format_exc(),
    )
    raise HTTPException(status_code=status_code, detail=response)

@router.get("/kafka/topic/{topic}")
async def get_kafka_topic(topic: str):
  try:
    message = KafkaAdmin.getInstance().describe_topic(topic)
    return APIResponse(message = message)
  except:
    status_code = 500
    response = dict(
      status=status_code,
      message="There was an error while retreiving the topic",
      error=traceback.format_exc(),
    )
    raise HTTPException(status_code=status_code, detail=response)


