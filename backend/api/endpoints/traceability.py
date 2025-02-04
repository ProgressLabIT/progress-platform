import traceback

from fastapi import APIRouter, HTTPException, Depends
from utils import auth

from models.event import EventInputModel, EventType, EventModel
from models.traceability import *

from utils.exceptions import *
from utils.api import APIResponse
from models.serial import SerialSelection
from utils.db import db
from utils.dt import timestamp
from utils.event import get_event_class
from utils.serial import Queries as SerialQueries
from utils.traceability import Queries

router = APIRouter()

serials = db.collection('Serial')

@router.post('/event',
    dependencies=[Depends(auth.verify_token)])
async def record_event(event_data: EventInputModel):
  try:
    event_class = get_event_class(event_data.event_type)
    event = event_class(EventModel(**event_data.model_dump()))
    event.save()
    return APIResponse(detail=event.response)

  except (
    JobIsActiveError,
    JobHasActiveBatchError,
    JobHasNoAssigneeError,
    JobHasNoActiveBatchError,
    ValueError,
    WipNotAvailableError,
    SerialNotDeletedError,
    SerialNotUpdatedError,
    SerialNotLinkedError,
    SerialNotCreatedError,
    SerialCodeAlreadyPresent
  ) as e:
    print(e)
    raise HTTPException(
      status_code=422,
      detail=dict(
        error_type = e.__class__.__name__,
        message = len(e.args) > 0 and e.args[0] or None,
        exception = traceback.format_exc()
      )
    )

  except Exception as e:
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



@router.get('/event',
    dependencies=[Depends(auth.verify_token)])
async def get_events(
  issue_key: str | None = None,
  serial_key: str | None = None,
  job_key: str | None = None,
  work_order_key: str | None = None,
  time_from: datetime | None = None,
  time_to: datetime | None = None,
  type: EventType | None = None
):
  bind_vars = dict(
    issue_key = issue_key,
    serial_key = serial_key,
    job_key = job_key,
    work_order_key = work_order_key,
    time_from = time_from,
    time_to = time_to,
    type = type
  )
  return [e for e in db.aql.execute(Queries.GET_EVENTS, bind_vars=bind_vars)]



@router.get('/batch/{batch_key}',
    dependencies=[Depends(auth.verify_token)])
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

@router.get('/batch/{batch_key}/serials',
    dependencies=[Depends(auth.verify_token)])
async def get_batch_serials(batch_key: str):

  try:
    batch_serials_cursor = db.aql.execute(
      SerialQueries.GET_BATCH_SERIALS,
      bind_vars = dict(batch_key=batch_key)
    )

    batch_serials = [SerialSelection(**s) for s in batch_serials_cursor]

    for s in batch_serials:
      s.active = True

    return batch_serials

  except StopIteration:
    return HTTPException(
      status_code=404,
      detail=f"No serials found associated with batch {batch_key}"
    )

  except Exception as e:
    return HTTPException(
      status_code=500,
      detail=f"There was an error on our end: {traceback.format_exc()}"
    )


@router.post('/job/{job_key}/heartbeat',
    dependencies=[Depends(auth.verify_token)])
async def job_heartbeat(job_key: str, work_session_key: str | None = None):
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


@router.get('/wip',
    dependencies=[Depends(auth.verify_token)])
async def get_wip_availability_for_job(job_key: str):
  tx = db.begin_transaction()
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
