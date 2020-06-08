import traceback

from fastapi import APIRouter, HTTPException

from models.traceability import *
from utils.event import Event
from utils.api import APIResponse
from utils.db import db



router = APIRouter()

@router.post('/event')
async def apply_production_event(data: ProductionEvent):
  print(data)
  try:
    event = Event(data)
    event.save()
  except:
    status_code=500
    error_str = traceback.format_exc()
    response = {
      'status': status_code,
      'message': "There was a problem saving the event in the db",
      'error': error_str
    }
    print(error_str)
    raise HTTPException(
      status_code=status_code,
      detail=response
    )


@router.get('/batch/{batch_key}')
async def get_batch_execution_data(batch_key: str):

  print(batch_key)
  query = """
    LET batch = FIRST( FOR b IN Batch FILTER b._key == @batch_key RETURN b )
    LET job = FIRST( FOR j IN Job FILTER j._id == batch.job_id RETURN j )
    LET procedure = DOCUMENT(job.phase_id).step_sequence

    LET batch_step_data = (
      FOR step_id IN procedure
      LET step_data = KEEP(DOCUMENT(step_id), '_id', 'type')
      LET execution_data = FIRST(
        FOR s IN StepExecutionData 
        FILTER s.batch_id == batch._id && s.step_id == step_id
        RETURN KEEP(s, 'status', 'user_data')
      )
      LET step_done = execution_data ? execution_data.status == 'done' : false
      LET step_critical = execution_data ? execution_data.status == 'critical' : false
      LET user_data = execution_data ? execution_data.user_data : []
      RETURN MERGE( step_data, { 
        done: step_done,
        critical: step_critical,
        user_data: user_data
      })
    )
    RETURN MERGE(batch, { step_data: batch_step_data })
  """

  db_resp = db.aql.execute(query, bind_vars={ 'batch_key': batch_key })
  try:
    batch_data = db_resp.next()
  except StopIteration:
    batch_data = {}
  return APIResponse(detail=batch_data)