from fastapi import APIRouter

from utils.db import db

router = APIRouter()

@router.delete('/reset/prod')
async def reset_production_and_traceability_data():
  collections = [
    'Batch',
    'Event',
    'Job',
    'Queue',
    'StepExecutionData',
    'wip',
    'WorkOrder',
    'WorkSession',
  ]

  tx = db.begin_transaction(write=collections)

  for c in collections:
    tx.collection(c).truncate()

  tx.collection('Queue').insert(dict(
    type = 's', #What the queue refers to.
    site_key = '0',
    subqueue_target_key = None,
    work_orders = [],
    jobs = []
  ))

  tx.commit_transaction()
