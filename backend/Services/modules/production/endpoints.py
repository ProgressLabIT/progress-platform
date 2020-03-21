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

  # Create WO record
  def create_wo_record(wo: WorkOrderNew, tx):
    data_in = jsonable_encoder(wo)
    new_wo_record = WorkOrderFull(**data_in)
    prepped = jsonable_encoder(new_wo_record, by_alias=True, include_none=False)
    collection = tx.collection('WorkOrder')
    new_wo_record.id = collection.insert(prepped)['_id']
    return new_wo_record

  try:
    new_wo_record = create_wo_record(new_wo, tx)
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
  print(process)

  def create_job_record(wo_data, phase_id, tx):
    phase = PhaseProcedure(**tx.document(phase_id))
    new_job_record = Job(
      wo_id = new_wo_record.id,
      phase_id = phase_id,
      phase_alias = phase.alias,
      product_id = wo_data.product_id,
      operation_id = phase.operation_id,
      parameters = phase.params,
      qt_planned = wo_data.qt_planned, 
    )
    prepped = jsonable_encoder(new_job_record, by_alias=True, include_none=False)
    collection = tx.collection('Job')
    new_job_record.id = collection.insert(prepped)['_id']
    return new_job_record
  
  try:
    new_job_records = [create_job_record(new_wo_record, p_id, tx) for p_id in process]
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
