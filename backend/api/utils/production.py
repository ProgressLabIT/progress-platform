import traceback

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder

from models.process import PhaseData
from models.production import Job, WorkOrderNew, WorkOrderFull
from utils.bom import get_bom_from_db
from utils.process import search_step_media
from utils.product import get_product_docs


class Queries:
  ADD_WORK_ORDER_TO_QUEUE = """
    FOR q IN Queue
    FILTER q.type == 's' && q.site_key == '0'
    UPDATE q WITH { work_orders: PUSH(q.work_orders, @new_wo_key) } IN Queue
  """

  GET_SITE_WORK_ORDER_DATA = """
    LET queue = FIRST(
      FOR q IN Queue
      FILTER q.type == 's' && q.site_key == @site_key
      RETURN q.work_orders
    )

    FOR wo_key IN queue
      LET wo = DOCUMENT(WorkOrder, wo_key)
      FILTER wo != null // Prevent bugs in case queue has inexistent keys
      LET qt_remaining = wo.qt_planned - wo.qt_completed
      LET issue_count = COUNT(FOR i IN issue_rel FILTER i._to == wo._id RETURN 1)
      RETURN MERGE (wo, { qt_remaining: qt_remaining, issue_count })
  """

  # See endpoints/production.py@search_work_orders
  GET_WORK_ORDER_DATA = """
    LET now = DATE_NOW()

    FOR wo IN WorkOrder
      FILTER wo._key == @wo_key

      // get job data
      LET jobs = (
        FOR j IN Job
        FILTER j.wo_key == wo._key && !j.trash
        LET operator = KEEP(DOCUMENT(User, j.assigned_to), '_key', 'name', 'surname', 'active')
        LET work_sessions = (
          FOR ws IN WorkSession
          FILTER ws.job_key == j._key && ws.canceled == null
          LET duration = ws.active ? DATE_DIFF(ws.start, now, 'f') : ws.duration
          LET cost = ws.hourly_cost * duration / 3600000
          RETURN MERGE({ duration, cost })
        )
        LET processing_time = SUM(work_sessions[*].duration)
        LET processing_cost = SUM(work_sessions[*].cost)
        LET issue_count = COUNT(FOR i IN issue_rel FILTER i._to == j._id RETURN 1)

        RETURN MERGE( j, { assigned_to: operator, processing_time, processing_cost, issue_count } )
      )

      LET processing_time = SUM(jobs[*].processing_time)
      LET processing_cost = SUM(jobs[*].processing_cost)
      LET total_cost = processing_cost + wo.material_cost

      // Return enriched wo data
      RETURN MERGE(wo, { jobs, processing_time, processing_cost, total_cost })
  """


  GET_WORK_ORDER_SEARCH_OPTIONS = """
    LET phases = (FOR j IN Job
       FILTER j.stage != 'closed'
       COLLECT phase_alias = j.phase_alias OPTIONS { method: "sorted" }
       return { "_key": phase_alias, "name": phase_alias})

    LET products = (FOR j IN Job
       FILTER j.stage != 'closed'
       COLLECT product_code = j.product_code, product_key = j.product_key OPTIONS { method: "sorted" }
       return { "_key": product_key, "name": product_code})

    LET wo_codes = (FOR j IN Job
       FILTER j.stage != 'closed'
       COLLECT wo_code = j.wo_code, wo_key = j.wo_key OPTIONS { method: "sorted" }
       return { "_key": wo_key, "name": wo_code})

    return {phases, products, wo_codes}
  """


  GET_WORKING_JOB_DATA = """
    FOR j IN Job
    FILTER j._key == @job_key

    LET wo_bom = (
      FOR bom_component IN DOCUMENT(WorkOrder, j.wo_key).wo_bom

      LET declared_serials = (
        FOR linked_serial IN contains
          FILTER linked_serial.replaced == false
          && linked_serial.component_key == bom_component.component_key
          && linked_serial.wo_key == j.wo_key
          && (linked_serial.batch_key == j.active_batch_key || linked_serial._from == CONCAT('Batch/', j.active_batch_key))
          return linked_serial
      )
      RETURN MERGE(bom_component, { declared_serials })
    )

    LET issue_count = COUNT(FOR i IN issue_rel FILTER i._to == j._id RETURN 1)
    LET product_notes = DOCUMENT(Product, j.product_key).production_notes
    LET phase_notes = DOCUMENT(Phase, j.phase_key).notes
    LET order_notes = DOCUMENT(WorkOrder, j.wo_key).notes
    LET message_count = COUNT(FOR m IN message FILTER m._to == CONCAT('WorkOrder/', j.wo_key) RETURN 1)
    RETURN MERGE(j, { wo_bom, issue_count, product_notes, phase_notes, order_notes, message_count })
  """


  GET_ACTIVE_WORK_SESSION_FOR_JOB = """
    LET ws_key = FIRST(
      FOR j IN Job
      FILTER j._key == @job_key
      RETURN j.last_work_session_started
    )

    LET ws = Document('WorkSession', ws_key)

    RETURN ws
  """


  REORDER_JOB_QUEUES = """
    LET wo_queue = (
      FOR q1 IN Queue
      FILTER
        q1.type == 's'
        && (q1.site_key == @site_key || "0")
        FOR wo in q1.work_orders
        RETURN {
          _key: wo,
          phase_sequence: DOCUMENT(WorkOrder, wo).phase_sequence
        }
    )

    // Process Job queues
    FOR q IN Queue
      FILTER
        q.type == "o"
        && q.independent != true
        && (q.site_key == @site_key || "0")
        && (@target_key ? (IS_ARRAY(@target_key) ? q.subqueue_target_key IN @target_key : q.subqueue_target_key == @target_key) : true)
        && LENGTH(q.jobs)

      LET new_queue = REMOVE_VALUE(
        FLATTEN(
          FOR wo IN wo_queue
            FOR phase IN wo.phase_sequence
              FOR j IN Job
              FILTER
                j.wo_key == wo._key
                && j.phase_key == phase
                && j.assigned_to == q.subqueue_target_key
                && j.stage != 'closed'
              RETURN j._key
        ),
        null
      )

      UPDATE q WITH { jobs: new_queue } in Queue
  """

  GET_ASSIGNMENT_LIST = """
    LET assigned_jobs_by_operator = (
      LET user_key = @user_key ? : '%'
      FOR operator IN User
      FILTER CONTAINS(operator.scope, 'operator') && LIKE(operator._key, user_key)

      LET operator_queue = FIRST(
        FOR q IN Queue
        FILTER q.type == 'o' && q.subqueue_target_key == operator._key
        RETURN q
      )

      LET assigned_jobs = (
        FOR j IN (operator_queue.jobs || [])
        LET job_data = DOCUMENT(Job, j)
        FILTER job_data != null // Prevent bugs in case queue has inexistent keys
        LET wo_data = DOCUMENT(WorkOrder, job_data.wo_key)
        LET issues = (FOR v IN 1..1 INBOUND wo_data._id issue_rel RETURN v)
        LET issues_open = LENGTH(issues[* FILTER CURRENT.open])
        LET due_by = wo_data.due_by
        RETURN MERGE(job_data, { issues_open, issues_total: LENGTH(issues), due_by })
      )

      RETURN {
        operator: KEEP(operator, '_key', 'name', 'surname', 'active', 'department_key'),
        assigned_jobs: assigned_jobs,
        independent: operator_queue.independent || false
      }
    )

    LET unassigned_jobs = (
      LET wo_queue = FIRST(FOR q IN Queue FILTER q.type == 's' RETURN q.work_orders)

      FOR j in Job
        FILTER
          !j.trash
          && j.assigned_to == null // unassigned
          && j.stage != 'closed' // prevent bugs in case of jobs being closed before being assigned

        // Order by WorkOrder Queue position and Phase sequence
        LET wo_data = DOCUMENT(WorkOrder, j.wo_key)
        LET issues = (FOR v IN 1..1 INBOUND wo_data._id issue_rel RETURN v)
        LET issues_open = LENGTH(issues[* FILTER CURRENT.open])
        LET wo_queue_index = POSITION(wo_queue, j.wo_key, true)
        LET wo_phase_sequence = wo_data.phase_sequence
        LET due_by = wo_data.due_by
        LET job_phase_index = POSITION(wo_phase_sequence, j.phase_key, true)
        SORT wo_queue_index, job_phase_index

        RETURN MERGE(j, { issues_open, issues_total: LENGTH(issues), due_by })
    )

    RETURN {
      assigned_jobs_by_operator,
      unassigned_jobs
    }
  """

  GET_PHASE_STEP_DATA = """
    FOR p IN Phase
    FILTER p._key == @phase_key
      FOR s IN p.step_sequence
      RETURN DOCUMENT(Step, s)
  """

  REMOVE_JOB_FROM_QUEUE = """
    FOR q IN Queue
    FILTER q.subqueue_target_key == @target_key
    UPDATE q WITH { jobs: REMOVE_VALUE(q.jobs, @job_key) } in Queue
  """

  ADD_JOB_TO_QUEUE = """
    FOR q IN Queue
    FILTER q.subqueue_target_key == @target_key

    // the third parameter = true makes sure the job is added only if not already present
    UPDATE q WITH { jobs: PUSH(q.jobs, @job_key, true) } in Queue
  """

  REMOVE_WORK_ORDER_FROM_QUEUE = """
    FOR q IN Queue
    FILTER q.type == 's' && q.site_key == '0'
    UPDATE q WITH { work_orders: REMOVE_VALUE(q.work_orders, @wo_key) } in Queue
  """


  CLOSE_JOB = """
    FOR j in Job
    FILTER j._key == @job_key
    UPDATE j WITH {
      active: false,
      stage: @stage,
      qt_planned: j.qt_completed,
      progress: 100,
      end: @end,
      notes: @notes
    } in Job
    RETURN NEW
  """

  GET_JOB_ELAPSED_TIME = """
    LET now = DATE_NOW()
    RETURN SUM(
      FOR ws IN WorkSession
      FILTER ws.job_key == @job_key && ws.canceled == null
      LET duration = ws.active ? DATE_DIFF(ws.start, now, 'f') : ws.duration
      RETURN duration
    )
    // returns milliseconds
  """


def update_target_queue(job_key, target_key, action, tx):
  """Add or remove jobs in a queue"""
  try:
    if action == 'remove':
      tx.aql.execute(
        Queries.REMOVE_JOB_FROM_QUEUE,
        bind_vars=dict(job_key=job_key, target_key=target_key)
      )

    if action == 'add':
      queue_match = dict(
        subqueue_target_key = target_key,
        site_key = '0'
      )
      operator_queue_exists = tx.collection('Queue').find(queue_match).count()

      if operator_queue_exists:
        # The query is defined so that the job is added only if not already present
        tx.aql.execute(
          Queries.ADD_JOB_TO_QUEUE,
          bind_vars = dict(
            target_key = target_key,
            job_key = job_key
          )
        )

        tx.aql.execute(
          Queries.REORDER_JOB_QUEUES,
          bind_vars = dict(
            site_key = '0',
            target_key = target_key
          )
        )

      else:
        tx.collection('Queue').insert(dict(
          **queue_match,
          type='o',
          jobs=[job_key]
        ))

  except:
    tx.abort_transaction()
    status_code = 500
    response =dict(
     status_code=status_code,
     message="Couldn't update queue on the db",
     error=traceback.format_exc()
    )
    raise HTTPException(status_code=status_code, detail=response)


def _get_procedure_for_new_job(tx, phase_key):
  try:
    db_steps = tx.aql.execute(
      Queries.GET_PHASE_STEP_DATA,
      bind_vars=dict(phase_key=phase_key)
    )
    job_steps = [s for s in db_steps]

  except:
    tx.abort_transaction()
    status_code=500
    response=dict(
      status_code=status_code,
      message=f"Couldn't retrieve data from the DB about Phase {phase_key}",
      error=traceback.format_exc()
    )
    raise HTTPException(status_code=status_code, detail=response)

  for s in job_steps:
    try:
      filenames = search_step_media(s['_key'])
      s['media'] = [media_name for media_name in filenames]
    except:
      tx.abort_transaction()
      status_code=500
      response=dict(
        status_code=status_code,
        message=f"Error while retrieving media info about Step {s['_key']}",
        error=traceback.format_exc()
      )
      raise HTTPException(status_code=status_code, detail=response)

  return job_steps


def _get_default_production_position(tx):
  return tx.collection('Config').get('default_production_position').get('value', 'IN')


def create_wo_record(tx, wo: WorkOrderNew):
  new_wo_record = WorkOrderFull(
    **wo.model_dump(),
    wo_docs = get_product_docs(wo.product_key),
    wo_bom = get_bom_from_db(tx, wo.product_key),
    output_position_key = _get_default_production_position(tx)
  )
  prepped = jsonable_encoder(new_wo_record, by_alias=True)
  db_resp = tx.collection('WorkOrder').insert(prepped)
  new_wo_record.id = db_resp['_id']
  new_wo_record.key = db_resp['_key']
  return new_wo_record

def create_job_record(
  tx,
  wo_data: WorkOrderFull,
  phase_key: str,
  qt_planned: float,
  assigned_to: str | None = None,
  **kwargs
  ):
  if phase_key == 'default':
    phase = PhaseData(alias='default')
  else:
    phase = PhaseData(**tx.document(f'Phase/{phase_key}'))

  first_phase = phase_key == wo_data.phase_sequence[0]
  last_phase = phase_key == wo_data.phase_sequence[-1]

  new_job_data = Job(
    wo_key = wo_data.key,
    wo_code = wo_data.wo_code,
    start_from = wo_data.start_from,
    phase_key = phase_key,
    phase_alias = phase.alias,
    first_phase = first_phase,
    last_phase = last_phase,
    product_key = wo_data.product_key,
    product_code = wo_data.product_code,
    product_description = wo_data.product_description,
    project_code = wo_data.project_code,
    operation_key = phase.operation_key,
    parameters = phase.params,
    qt_planned = qt_planned,
    next_batch_available = True if first_phase else False,
    step_sequence = _get_procedure_for_new_job(tx, phase_key),
    job_docs = wo_data.wo_docs,
    assigned_to = assigned_to,
    notes = kwargs.get('notes', None),
    traceability_level = wo_data.traceability_level,
    serialcode_on_batchstart = wo_data.serialcode_on_batchstart
  )

  prepped = jsonable_encoder(new_job_data, by_alias=True)
  new_job_record = Job(**tx.collection('Job').insert(prepped, return_new=True)['new'])

  if assigned_to:
    update_target_queue(new_job_record.key, assigned_to, 'add', tx)

  return new_job_record
