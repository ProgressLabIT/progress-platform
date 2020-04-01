from typing import List
from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from .models import WorkOrderNew, WorkOrderFull, TargetActualTimeDelta, Job, JobAssignment, AssignmentsResponse, WorkOrderDetails
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
  product_coll = tx.collection('Product')

  # Create WO record
  def create_wo_record(wo: WorkOrderNew, collection):
    data_in = jsonable_encoder(wo)
    new_wo_record = WorkOrderFull(**data_in)
    prepped = jsonable_encoder(new_wo_record, by_alias=True, include_none=False)
    new_wo_record.id = collection.insert(prepped)['_id']
    return new_wo_record

  try:
    product_data = product_coll.get(new_wo.product_id)
    new_wo.product_code = product_data['code']
    new_wo.product_description = product_data['description']
    new_wo_record = create_wo_record(new_wo, wo_coll)
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
      product_description = wo_data.product_description,
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
      LET qt_remaining = wo.qt_planned - wo.qt_completed
      LET jobs = ( FOR j IN Job FILTER j.wo_id == wo._id RETURN j)
      LET phases = ( FOR j IN jobs RETURN DISTINCT j.phase_alias )
      LET active = TO_BOOL(SUM(FOR j IN jobs FILTER j.active RETURN 1))
      RETURN MERGE ([wo, { qt_remaining: qt_remaining, phase_sequence: phases, active: active }])  
  """

  # wo_list = [WorkOrderFull(**wo) for wo in db.collection('WorkOrder').all()]
  wo_list = [wo for wo in db.aql.execute(query)]
  return APIResponse(detail=wo_list)


@router.get('/work-order/{wo_key}')
async def get_wo_data(wo_key: str):
  
  query = """
    FOR wo IN WorkOrder
      FILTER wo._key == @wo_key
      
      LET qt_remaining = wo.qt_planned - wo.qt_completed
      
      // get phases in order from product data
      LET phases = FIRST( FOR p IN Product FILTER p._id == wo.product_id RETURN p.process_phases )

      // get job data
      LET phase_jobs = MERGE( 
        FOR j IN Job
        FILTER j.wo_id == wo._id
        COLLECT phase_id = j.phase_id, alias = j.phase_alias INTO jobs = j
        LET active = TO_BOOL(COUNT(FOR j IN jobs FILTER j.active RETURN 1))
        RETURN { 
          [phase_id] : { phase_alias: alias, active: active, jobs: jobs } 
        }
      )

      // check if any job is active
      LET active = TO_BOOL(COUNT(FOR j IN Job FILTER j.wo_id == wo._id && j.active RETURN 1))

      // Return enriched wo data
      RETURN MERGE ([
        wo, { 
        qt_remaining: qt_remaining, 
        phase_sequence: phases, 
        phase_jobs: phase_jobs, 
        active: active 
      }])
  """

  wo_data = db.aql.execute(query, bind_vars={ 'wo_key': wo_key }).next()
  return APIResponse(detail=WorkOrderDetails(**wo_data))

@router.get('/job')
async def get_job_list():

  # db_resp = db.aql.execute("""
  #   FOR j IN Job
  #   LET assignee = FIRST(FOR v in 1..1 OUTBOUND j assigned_to RETURN v)
  #   RETURN MERGE(j, { assigned_to: assignee })
  # """)

  job_list = [Job(**j) for j in db.collection('Job').all()]

  return APIResponse(detail=job_list)


@router.get('/job-assignment')
async def get_assignment_list():

  result = db.aql.execute("""
    LET assigned_jobs_by_operator = (
      FOR o IN User
      FILTER o.roles.operator == true
      LET assigned_jobs = (    
        FOR v,e IN 1..1 INBOUND o assigned_to
        FILTER e.rel_type == 'JobOperator'
        RETURN v
      )
      
      RETURN {
        operator: o,
        assigned_jobs: assigned_jobs
      }
    )

    LET unassigned_jobs = (
      FOR j in Job
      LET assignments = SUM(
        FOR a IN assigned_to 
        FILTER a.rel_type == 'JobOperator' && a._from == j._id
        RETURN 1
      )
      FILTER assignments == 0
      RETURN j
    )

    RETURN {
      assigned_jobs_by_operator: assigned_jobs_by_operator,
      unassigned_jobs: unassigned_jobs
    }  
  """).next()

  return APIResponse(detail=AssignmentsResponse(**result))
  # cursor = db.collection('assigned_to').find({ 'rel_type': 'JobOperator'})
  # assignment_list = [JobAssignment(**a) for a in cursor]
  # return APIResponse(detail=assignment_list)
