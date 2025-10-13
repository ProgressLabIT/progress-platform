import traceback

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder

from models.form import SerialFormFieldValue
from models.process import PhaseData
from models.production import Job, WorkOrderNew, WorkOrderFull
from utils.bom import get_bom_from_db
from utils.process import search_step_media, Queries as ProcessQueries
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

      // Dynamically add component inventory management config to wo_bom
      LET wo_bom = (FOR b IN wo.wo_bom
        LET manage_inventory = FIRST(FOR p IN Product FILTER p._key == b.component_key RETURN p.manage_inventory)
        RETURN MERGE(b, { manage_inventory })
      )

      LET processing_time = SUM(jobs[*].processing_time)
      LET processing_cost = SUM(jobs[*].processing_cost)
      LET total_cost = processing_cost + wo.material_cost

      // Return enriched wo data
      RETURN MERGE(wo, { jobs, processing_time, processing_cost, total_cost, wo_bom })
  """

  GET_WORK_ORDER_TRACEABILITY_DATA = """
    LET wo = DOCUMENT(WorkOrder, @wo_key)
    LET execution_data = (
      FOR phase IN wo.phase_sequence[* RETURN DOCUMENT(Phase, CURRENT)]
      FOR j IN Job
      FILTER j.wo_key == wo._key && j.phase_key == phase._key
      FOR b IN Batch
      FILTER b.job_key == j._key
      LET serials = (FOR s IN 1..1 OUTBOUND b batch_serial RETURN s)
      LET has_serials = LENGTH(serials) > 0
      LET serial_loop = has_serials ? serials : [{ code: null, _key: null }]
      FOR s IN j.step_sequence
      FOR x IN StepExecutionData
      FILTER x.step_key == s._key && x.batch_key == b._key
      FOR serial IN serial_loop
      LET form_fields = (
        FOR d IN NOT_NULL(x.form_data, [])
        LET serial_field_value = FIRST(FOR f IN NOT_NULL(serial.data, []) FILTER f.step_key == s._key && f.form_field_key == d.form_field_key RETURN f.value)
        RETURN MERGE(d, {
          field_type: FIRST(FOR c IN CustomField FILTER c._key == d.custom_field_key RETURN c.type),
          field_label: FIRST(FOR f IN NOT_NULL(s.form_fields, []) FILTER f._key == d.form_field_key RETURN f.label),
          serial_field_value
        })
      )
      RETURN {
        step_key: s._key,
        step_title: s.title,
        serial_code: serial.code,
        serial_key: serial._key,
        batch_key: b._key,
        batch_qt: b.qt_pass,
        job_key: j._key,
        operator_key: x.user_key,
        timestamp: x.completed,
        phase_key: j.phase_key,
        phase_alias: j.phase_alias,
        form_fields
      }
    )
    LET operators = UNIQUE(execution_data[*].operator_key)
    LET usernames = MERGE(FOR u IN User FILTER u._key IN operators RETURN { [u._key]: u.username })
    FOR x IN execution_data
    SORT x.timestamp
    RETURN MERGE(x, { operator_username: usernames[x.operator_key] })
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
      FOR bom_line IN DOCUMENT(WorkOrder, j.wo_key).wo_bom

      LET declared_serials = (
        FOR c IN contains
          FILTER !c.replaced
          && c.component_key == bom_line.component_key
          && c.phase_key == bom_line.phase_key
          && c.batch_key == j.active_batch_key
          LET component_serial = DOCUMENT(c._to)
          RETURN {
            _key: component_serial._key,
            code: component_serial.code,
            phase_key: c.phase_key,
            component_key: c.component_key,
            parent_serial_key: PARSE_IDENTIFIER(c._from).key,
            batch_key: j.active_batch_key,
            link_key: c._key
          }
      )
      LET manage_inventory = FIRST(FOR p IN Product FILTER p._key == bom_line.component_key RETURN p.manage_inventory)
      RETURN MERGE(bom_line, { declared_serials, manage_inventory })
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


def _get_production_position(tx, wo: WorkOrderNew):
  if wo.output_position_key:
    return wo.output_position_key
  else:
    return tx.collection('Config').get('default_production_position').get('value', 'IN')


def _define_wo_bom(tx, wo: WorkOrderNew):
  if wo.wo_bom:

    product_data = tx.collection('Product').get_many([line.component_key for line in wo.wo_bom])
    phase_data = tx.collection('Phase').get_many([line.phase_key for line in wo.wo_bom])

    alien_phases = set(phase['_key'] for phase in phase_data) - set(wo.phase_sequence)
    if len(alien_phases):
      raise ValueError('Bom references phases that do not belong to the work order')

    default_consumption_position_key = tx.collection('Config').get('default_consumption_position').get('value', 'IN')

    bom = []
    for line in wo.wo_bom:
      product = next((p for p in product_data if p['_key'] == line.component_key), None)
      phase = next((p for p in phase_data if p['_key'] == line.phase_key), None)

      # Set default consumption position key if not provided
      consumption_position_key = product.get('default_consumption_position_key', default_consumption_position_key)
      if line.consumption_options.consumption_position_key is None:
        line.consumption_options.consumption_position_key = consumption_position_key

      bom.append(dict(
        **line.model_dump(),
        component_code = product['code'],
        component_description = product.get('description', ''),
        manage_inventory = product.get('manage_inventory', False),
        traceability_level = product.get('traceability_level', None),
        phase_name = phase['alias'],
      ))
    return bom

  else:
    return [line.model_dump() for line in get_bom_from_db(tx, wo.product_key)]


def _define_serial_fields(tx, product_key: str):
  phase_data = list(tx.aql.execute(ProcessQueries.GET_PRODUCTION_PROCESS, bind_vars=dict(product_key=product_key)))
  serial_fields = []
  for phase in phase_data:
    for step in phase['steps']:
      for field in step.get('form_fields', []):
        serial_fields.append(SerialFormFieldValue(
          form_field_key = field['_key'],
          custom_field_key = field['custom_field_key'],
          label = field['label'],
          hint = field['hint'],
          mandatory = field['mandatory'],
          phase_key = phase['_key'],
          step_key = step['_key']
        ))
  return serial_fields

def create_wo_record(tx, wo: WorkOrderNew):
  input_data = wo.model_dump()
  input_data.update(
    wo_docs = get_product_docs(wo.product_key),
    wo_bom = _define_wo_bom(tx, wo),
    serial_fields = _define_serial_fields(tx, wo.product_key),
    output_position_key = _get_production_position(tx, wo)
  )
  new_wo_record = WorkOrderFull(**input_data)
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
    serial_code_on_creation = wo_data.serial_code_on_creation
  )

  prepped = jsonable_encoder(new_job_data, by_alias=True)
  new_job_record = Job(**tx.collection('Job').insert(prepped, return_new=True)['new'])

  if assigned_to:
    update_target_queue(new_job_record.key, assigned_to, 'add', tx)

  return new_job_record

def close_job_and_update_queues(tx, job: Job, notes: str | None = None) -> Job:
  """Close the provided job via JobClosedEvent (removes from queues within the event)."""
  # Fetch fresh job state to ensure we pass the correct completed quantity
  current_job_data = tx.collection('Job').get(job.key)
  current_job = Job(**current_job_data)

  # Build secondary event info to run inside existing transaction
  event_info = dict(
    event_type = EventType.JOB_CLOSED,
    primary = False,
    event_group = str(uuid.uuid4()),
    job_key = current_job.key,
    completed_qt = current_job.qt_completed,
    notes = notes if notes is not None else current_job.notes,
  )

  # Lazy import to avoid circular dependency
  from events.production.job_closed import JobClosedEvent
  event = JobClosedEvent(info=event_info, tx=tx)
  closed_job = event.save()
  return closed_job


def reassign_job_in_queues(tx, job_key: str, old_assignee: str | None, new_assignee: str | None) -> None:
  """Move job between operator queues based on reassignment."""
  if old_assignee:
    update_target_queue(
      job_key=job_key,
      target_key=old_assignee,
      action='remove',
      tx=tx
    )

  if new_assignee:
    update_target_queue(
      job_key=job_key,
      target_key=new_assignee,
      action='add',
      tx=tx
    )
