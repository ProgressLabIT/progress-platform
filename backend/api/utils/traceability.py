
class Queries:

  GET_EVENTS = """
    FOR e IN Event
    FILTER
      @work_order_key ? e.work_order_key == @work_order_key : true
      && @job_key ? e.job_key == @job_key : true
      && @issue_key ? e.issue_data._key == @issue_key : true
      && @serial_key ? e.serial_key == @serial_key : true
      && @task_key ? e.task_key == @task_key : true
      && @context_type ? e.context_type == @context_type : true
      && @context_key ? e.context_key == @context_key : true
      && @time_from ? e.timestamp >= @time_from : true
      && @time_to ? e.timestamp <= @time_to : true
      && @type ? e.event_type == @type : true

    LET task = e.context_key ? DOCUMENT(Task, e.context_key) : null // hard code the only context type for now
    LET task_type = task ? DOCUMENT(TaskType, task.task_type_key) : null
    LET context_name = task_type ? task_type.name : null
    LET context_icon = task_type ? task_type.icon : null
    SORT e.timestamp
    RETURN MERGE(e, { context_code: task.code, context_name, context_icon })
  """

  CLOSE_UNALLOWED_PARALLEL_WORK_SESSIONS = """
    FOR ws IN WorkSession
    FILTER
      ws.user_key == @user_key
      && ws.active == true
      && !DOCUMENT(Job, ws.job_key).parameters.unsupervised_work_allowed
    UPDATE ws WITH { active: false, end: @timestamp } IN WorkSession
    RETURN NEW
  """

  CREATE_WORK_SESSION = """
    LET new_ws = {
      batch_key: @batch_key,
      job_key: @job_key,
      phase_key: @phase_key,
      work_order_key: @work_order_key,
      product_key: @product_key,
      user_key: @user_key,
      hourly_cost: DOCUMENT(User, @user_key).hourly_cost,
      user_session_key: @user_session_key,
      start: @start,
      active: true,
      canceled: null,
      forced: @forced,
      end: @end
    }

    INSERT new_ws INTO WorkSession RETURN NEW
  """


  GET_BATCH_EXECUTION_DATA = """
    LET batch = FIRST( FOR b IN Batch FILTER b._key == @batch_key RETURN b )
    LET job = FIRST( FOR j IN Job FILTER j._key == batch.job_key RETURN j )

    LET batch_step_data = (
      FOR step IN job.step_sequence
      LET step_data = KEEP(step, '_key', 'type')
      LET execution_data = FIRST(
        FOR x IN StepExecutionData
        FILTER
          x.batch_key == batch._key
          && x.step_key == step._key
          && x.canceled == null
        RETURN KEEP(x, 'status', 'form_data', '_key')
      )
      LET step_done = execution_data ? execution_data.status == 'done' : false
      LET step_critical = execution_data ? execution_data.status == 'critical' : false
      LET form_data = execution_data ? execution_data.form_data : []
      RETURN MERGE(step_data, {
        done: step_done,
        critical: step_critical,
        form_data: form_data,
        execution_record_key: execution_data._key
      })
    )
    RETURN MERGE(batch, { step_data: batch_step_data })
  """


  GET_BATCH_STEP_DONE_COUNT = """
    LET step_count = COUNT(
      FOR s IN StepExecutionData
      FILTER
        s.batch_key == @batch_key
        && s.status == @status
        && s.canceled == null
      RETURN DISTINCT s.step_key
    )
    RETURN step_count
  """


  COMPLETE_JOB = """
    FOR j IN Job
    FILTER j._key == @job_key
    UPDATE j WITH {
      active: false,
      stage: @stage,
      active_batch_key: null,
      active_batch_qt: 0,
      qt_completed: @qt_completed,
      qt_released: @qt_completed,
      qt_next_batch: null,
      next_batch_available: null,
      progress: ROUND(100 * @qt_completed / j.qt_planned),
      end: @end,
      notes: @notes
    } IN Job
    RETURN NEW
  """

  UPDATE_WORK_ORDER = """
    LET now = DATE_NOW()

    FOR wo IN WorkOrder
    FILTER wo._key == @wo_key
    LET jobs = (FOR j IN Job FILTER j.wo_key == @wo_key RETURN j)

    // Update progress
    LET progress = ROUND(AVERAGE(
      FOR phase IN wo.phase_sequence
      // Do not consider quantities beyond the planned quantity for wo
      RETURN 100 * MIN([wo.qt_planned, SUM(
        FOR j IN jobs
        FILTER j.phase_key == phase
        RETURN j.progress * j.qt_planned / 100
      )]) / wo.qt_planned
    ))

    // Update active state
    LET active = TO_BOOL(SUM(
      FOR j IN jobs
      FILTER j.active
      RETURN 1
    ))

    // Update completed quantity
    LET qt_completed = SUM(
      FOR j IN jobs
      FILTER j.last_phase
      RETURN j.qt_released
    )

    // Update PT and Cost
    LET work_sessions = (
      FOR ws IN WorkSession
      FILTER ws.work_order_key == @wo_key && ws.canceled == null
      LET benchmark = ws.active ? now : ws.end
      LET duration = DATE_DIFF(ws.start, benchmark, 'f')
      LET cost = ws.hourly_cost * duration / 3600000 // No. of milliseconds in an hour: 60*60*1000
      RETURN MERGE(ws, { duration, cost })
    )

    LET processing_time = SUM(FOR ws IN work_sessions RETURN ws.duration)
    LET processing_cost = SUM(FOR ws IN work_sessions RETURN ws.cost)

    // Check if WO is open by checking if any job is not closed
    LET open = TO_BOOL(COUNT(FOR j IN jobs FILTER j.stage != 'closed' RETURN 1))

    // Check if WO is started by checking if any job is not in 'created' stage (is started or closed)
    LET started = TO_BOOL(COUNT(FOR j IN jobs FILTER j.stage != 'created' RETURN 1))

    // Define wo status
    LET status = open ? (started ? 'started' : 'created') : 'closed'

    // Update start and end if wo has been reset/started/closed
    LET start = status == 'created' ? null : (
      wo.start ? wo.start : DATE_ISO8601(now)
    )

    LET end = open ? null : DATE_ISO8601(now)

    // Apply changes and return updated record
    UPDATE wo WITH {

      progress,
      active,
      qt_completed,
      status,
      start,
      end,
      processing_time,
      processing_cost

    } IN WorkOrder RETURN NEW
  """


  UPDATE_JOB_PROGRESS = """
    LET j = DOCUMENT(Job, @job_key)
    LET should_count_step_progress = j.parameters.step_check && TO_BOOL(j.active_batch_key)

    LET step_progress = !should_count_step_progress ? 0 : FIRST(
      LET default_batch = j.parameters.production_batch_qt
      LET remaining_qt = j.qt_planned - j.qt_completed
      LET batch_qt = MIN([default_batch, remaining_qt])
      LET current_batch_total_value = batch_qt / j.qt_planned
      LET step_progress_value = current_batch_total_value / LENGTH(j.step_sequence)
      LET step_done_count = SUM(
        FOR s IN StepExecutionData
        FILTER
          s.batch_key == j.active_batch_key
          && s.status == 'done'
          && s.canceled == null
        RETURN 1
      )
      RETURN step_progress_value * step_done_count
    )

    LET batch_progress = j.qt_completed / j.qt_planned
    LET progress = ROUND(100*(batch_progress + step_progress))

    UPDATE j WITH { progress } in Job
  """


  COMPLETE_BATCH = """
    LET batch = DOCUMENT(Batch, @batch_key)

    LET work_sessions = (
      FOR ws IN WorkSession
      FILTER ws.batch_key == @batch_key && ws.canceled == null
      RETURN ws
    )

    // TODO: Update when material cost will be handled
    LET material_cost = 0

    LET processing_cost = SUM(
      FOR ws IN work_sessions
      RETURN ws.duration * ws.hourly_cost
    ) / 3600000

    UPDATE batch WITH {
      qt_pass: @qt_pass,
      active: false,
      end: @end,
      value: processing_cost + material_cost
    } in Batch
  """

  UPDATE_BATCH_QT = """
    LET batch = DOCUMENT(Batch, @batch_key)

    UPDATE batch WITH {
      qt_total: @qt_total
    } in Batch
  """

  UPDATE_JOB_QT = """
    LET job = DOCUMENT(Job, @job_key)

    UPDATE job WITH {
      active_batch_qt: @active_qt
    } in Job
  """


  CLOSE_WORK_SESSION = """
    LET ws_key = FIRST(
      FOR j IN Job
      FILTER j._key == @job_key
      RETURN j.last_work_session_started
    )

    LET ws = Document('WorkSession', ws_key)
    LET duration = DATE_DIFF(ws.start, @end, "f")

    UPDATE ws WITH {
      end: @end,
      duration,
      active: false
    } in WorkSession

    RETURN NEW
  """

  # GET_NEXT_SERIAL_NUMBER_FOR_WORK_ORDER = """
  #   LET wo_serials = (
  #     FOR s IN Serial
  #     FILTER s.wo_key == @wo_key
  #     RETURN s.counter
  #   )
  #   RETURN MAX(wo_serials) + 1
  # """

  GET_NEXT_PHASE_IN_WORK_ORDER = """
    FOR wo IN WorkOrder
    FILTER wo._key == @wo_key
    LET next_phase_index = POSITION(wo.phase_sequence, @phase_key, true) + 1

    // if last phase of process return null
    RETURN next_phase_index < LENGTH(wo.phase_sequence)
      ? wo.phase_sequence[next_phase_index]
      : null
  """

  UPDATE_NEXT_BATCH_AVAILABLE_STATE_FOR_JOBS_IN_PHASES = """
    FOR j IN Job
    FILTER j.wo_key == @wo_key && j.phase_key IN @phase_keys

    // Get input available for any job in phase
    LET input_for_phase = SUM(
      FOR w IN wip
      FILTER
        w.wo_key == @wo_key
        && w._to == CONCAT('Phase/', j.phase_key)
      RETURN w.quantity
    )

    LET qt_remaining = j.qt_planned - j.qt_completed
    LET default_batch = j.parameters.production_batch_qt
    LET qt_next_batch = default_batch == 0 ? qt_remaining : MIN([default_batch, qt_remaining])

    LET next_batch_available = j.first_phase || qt_next_batch <= input_for_phase
    UPDATE j WITH { next_batch_available } IN Job
  """

  RETRIEVE_AVAILABLE_WIP = """
    FOR w IN wip
    FILTER
      w._to == CONCAT('Phase/', @phase_key)
      && w.wo_key == @wo_key
    RETURN w
  """

  GET_AVAILABLE_WIP_UPSTREAM_AND_DOWNSTREAM_OF_JOB = """
    FOR j in Job
    FILTER j._key == @job_key
    LET current_phase_id = CONCAT('Phase/', j.phase_key)
    LET process = DOCUMENT(WorkOrder, j.wo_key).phase_sequence
    LET current_phase_index = POSITION(process, j.phase_key, true)

    LET next_phase_key = j.phase_key == LAST(process)
      ? null
      : process[current_phase_index + 1]
    LET next_phase_id = CONCAT('Phase/', next_phase_key)

    LET previous_phase_key = j.phase_key == FIRST(process)
      ? null
      : process[current_phase_index - 1]
    LET previous_phase_id = CONCAT('Phase/', previous_phase_key)

    LET free_up_down_stream_wip_records = (
      for w in wip
      filter
        w.wo_key == j.wo_key
        && w._to in [current_phase_id, next_phase_id]
      return w
    )

    LET upstream_free_wip = (
      FOR w IN free_up_down_stream_wip_records
      FILTER
        w._from == previous_phase_id
        && w._to == current_phase_id
      RETURN w
    )

    LET downstream_free_wip = (
      FOR w IN free_up_down_stream_wip_records
      FILTER
        w._from == current_phase_id
        && w._to == next_phase_id
      RETURN w
    )

    RETURN { upstream_free_wip, downstream_free_wip, next_phase_key, previous_phase_key }
  """


  ALL_BATCH_STEPS_DONE = """
    LET steps = DOCUMENT(Job, @job_key).step_sequence[*]._key

    LET steps_done = (
      FOR s IN steps
      LET done = NOT_NULL(FIRST(
        FOR x IN StepExecutionData
          FILTER
            x.batch_key == @batch_key
            && x.step_key == s
            && !x.canceled
          RETURN x.status == 'done'
        ), false)
      RETURN done
    )
    RETURN steps_done[? ALL FILTER CURRENT == true]
  """

# ------------- END OF QUERIES CLASS ----------------------------------


def _update_job_progress(db, job_key):
  db.aql.execute(Queries.UPDATE_JOB_PROGRESS, bind_vars=dict(job_key=job_key))


