from typing import List
from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from .models import WorkOrderNew, WorkOrderFull, TargetActualTimeDelta, Job
from modules.process.models import PhaseProcedure
from utils.db import db
from utils.api import APIResponse
import traceback

router = APIRouter()
# work_orders = db.collection('WorkOrder')
# jobs = db.collection('Job')


@router.post('/work-order')
async def create_work_order(new_wo: WorkOrderNew):

  # Initialize transaction
  tx = db.begin_transaction(write=['WorkOrder', 'Job'], read=['Phase', 'Product'])
  wo_coll = tx.collection('WorkOrder')
  job_coll = tx.collection('Job')
  # Create WO record
  def create_wo_record(wo: WorkOrderNew, collection):
    data_in = jsonable_encoder(wo)
    new_wo_record = WorkOrderFull(**data_in)
    prepped = jsonable_encoder(new_wo_record, by_alias=True, include_none=False)
    new_wo_record.id = collection.insert(prepped)['_id']
    return new_wo_record

  try:
    new_wo_record = create_wo_record(new_wo, wo_coll)
    print(new_wo_record)
  except:
    status_code=500
    response = {
      'status': status_code,
      'message': "There was a problem creating the work order record in the db",
      'error': traceback.format_exc()
    }
    raise HTTPException(
      status_code=status_code,
      detail=response
    )


  # Get phase data from products & phase parameters from phase
  # Create Jobs
  process = tx.document(new_wo_record.product_id)['process_phases']

  def create_job_record(wo_data, phase_id, collection):
    phase = PhaseProcedure(**tx.document(phase_id))
    new_job_record = Job(
      wo_id = new_wo_record.id,
      wo_code = new_wo_record.wo_code,
      wo_line_no = new_wo_record.wo_line_no,
      phase_id = phase_id,
      phase_alias = phase.alias,
      product_id = wo_data.product_id,
      product_code = wo_data.product_code,
      operation_id = phase.operation_id,
      parameters = phase.params,
      qt_planned = wo_data.qt_planned
    )
    prepped = jsonable_encoder(new_job_record, by_alias=True, include_none=False)
    new_job_record.id = collection.insert(prepped)['_id']
    return new_job_record
  
  try:
    new_job_records = [create_job_record(new_wo_record, p_id, job_coll) for p_id in process]
  except:
    status_code=500
    response = {
      'status': status_code,
      'message': "There was a problem creating job records in the db",
      'error': traceback.format_exc()
    }
    raise HTTPException(
      status_code=status_code,
      detail=response
    )

  # Commit transaction
  tx.commit_transaction()
  return APIResponse(
    message="Work order and jobs created",
    details={
      'work_order': new_wo_record,
      'jobs': new_job_records
    }
  )


@router.get('/work-order')
async def get_wo_list():

  query = """
    FOR wo IN WorkOrder
      LET qt_remaining = wo.qt_planned - wo.qt_total
      LET active_phases = (
        FOR j IN Job
        FILTER j.wo_id == wo._id && j.active == true
        RETURN DISTINCT j.phase_alias
      )
      RETURN MERGE ([wo, { qt_remaining: qt_remaining, active_phases: active_phases }])
  """

  # wo_list = [WorkOrderFull(**wo) for wo in db.collection('WorkOrder').all()]
  wo_list = [wo for wo in db.aql.execute(query)]
  return APIResponse(detail=wo_list)


@router.get('/job')
async def get_job_list():

  job_list = [Job(**j) for j in db.collection('Job').all()]
  return APIResponse(detail=job_list)
