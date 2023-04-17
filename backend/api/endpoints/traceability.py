import traceback

from fastapi import APIRouter, HTTPException, Request

from events.main import Event
from models.traceability import *
from models.event import EventModel
from utils.api import APIResponse
from utils.db import db
from utils.dt import timestamp
from utils.traceability import Queries

router = APIRouter()


@router.post('/event')
async def apply_production_event(data: EventModel):
  try:
    event = Event(data)
    response = event.save()
    return APIResponse(detail=response)

  except:
    status_code=500
    error_str = traceback.format_exc()
    response = dict(
      status=status_code,
      message="There was a problem saving the event in the db",
      error=error_str
    )

    raise HTTPException(
      status_code=status_code,
      detail=response
    )



@router.get('/event')
async def get_events(
  issue_key: str = None,
  job_key: str = None,
  work_order_key: str = None,
  time_from: datetime = None,
  time_to: datetime = None
  ):
  bind_vars = dict(
    issue_key = issue_key,
    job_key = job_key,
    work_order_key = work_order_key,
    time_from = time_from,
    time_to = time_to
  )
  return [e for e in db.aql.execute(Queries.GET_EVENTS, bind_vars=bind_vars)]



@router.get('/batch/{batch_key}')
async def get_batch_execution_data(batch_key: str):

  try:
    db_resp = db.aql.execute(Queries.GET_BATCH_EXECUTION_DATA, bind_vars=dict(batch_key=batch_key))
    batch_data = db_resp.next()

  except StopIteration:
    batch_data = dict()

  except Exception:
    status_code=500
    error_str = traceback.format_exc()
    response = dict(
      status=status_code,
      message="There was a problem retrieving the batch from the db",
      error=error_str
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )

  return APIResponse(detail=batch_data)



@router.post('/job/{job_key}/heartbeat')
async def job_heartbeat(job_key: str, work_session_key: str = None):
  """
  Updates the work session `last_online` attribute with current time
  """
  try:
    now = timestamp()
    tx = db.begin_transaction(write=['Job', 'WorkSession'])
    tx.collection('Job').update({"_key": job_key, "last_online": now})

    """
    TODO: INSERT HERE UPDATE OF FALSELY CLOSED WORK SESSIONS

    E.g. If work_session_key exists and it's inactive, update it with active state and remove the end time
    """

    tx.commit_transaction()

    return APIResponse(detail={"last_online": now})

  except Exception:
    tx.abort_transaction()


@router.get('/wip')
async def get_wip_availability_for_job(job_key: str):
  tx = db.begin_transaction()
  job_data = tx.collection('Job').get(job_key)
  available_wip_records = tx.aql.execute(
    Queries.GET_AVAILABLE_WIP_UPSTREAM_AND_DOWNSTREAM_OF_JOB,
    bind_vars=dict(job_key=job_key)
  ).next()

  free_wip_qt_upstream = sum(w['quantity'] for w in available_wip_records['upstream_free_wip'])
  free_wip_qt_downstream = sum(w['quantity'] for w in available_wip_records['downstream_free_wip'])

  return dict(
    job_key = job_key,
    free_wip_qt_downstream = free_wip_qt_downstream,
    free_wip_qt_upstream = free_wip_qt_upstream
  )
