import traceback

from fastapi import APIRouter, HTTPException

from models.traceability import *
from utils.event import Event
from utils.api import APIResponse
from utils.db import db
from utils.traceability import Queries



router = APIRouter()


@router.post('/event')
async def apply_production_event(data: ProductionEvent):
  try:
    event = Event(data)
    event.save()
  except:
    status_code=500
    error_str = traceback.format_exc()
    response = dict(
      status=status_code,
      message="There was a problem saving the event in the db",
      error=error_str
    )
    print(error_str)
    raise HTTPException(
      status_code=status_code,
      detail=response
    )


@router.get('/batch/{batch_key}')
async def get_batch_execution_data(batch_key: str):

  db_resp = db.aql.execute(Queries.GET_BATCH_EXECUTION_DATA, bind_vars=dict(batch_key=batch_key))
  try:
    batch_data = db_resp.next()
  except StopIteration:
    batch_data = dict()
  return APIResponse(detail=batch_data)