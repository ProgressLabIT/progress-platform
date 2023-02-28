from models.production import Job
from models.traceability import StepStatus
from models.process import StepCheckBatch

class Queries:

  GET_EVENTS = """
    FOR e IN Event
    FILTER e.wo_key
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
      active: true
    }

    INSERT new_ws INTO WorkSession RETURN NEW
  """


  GET_BATCH_EXECUTION_DATA = """
    LET batch = FIRST( FOR b IN Batch FILTER b._key == @batch_key RETURN b )
    LET job = FIRST( FOR j IN Job FILTER j._key == batch.job_key RETURN j )
    LET procedure = DOCUMENT(Phase, job.phase_key).step_sequence

    LET batch_step_data = (
      FOR step_key IN procedure
      LET step_data = KEEP(DOCUMENT(Step, step_key), '_key', 'type')
      LET execution_data = FIRST(
        FOR s IN StepExecutionData
        FILTER s.batch_key == batch._key && s.step_key == step_key
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


  GET_BATCH_STEP_DONE_COUNT = """
    LET step_count = COUNT(
      FOR s IN StepExecutionData
      FILTER s.batch_key == @batch_key && s.status == @status
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
      RETURN SUM(
        FOR j IN jobs
        FILTER j.phase_key == phase
        RETURN j.progress * j.qt_planned
      ) / wo.qt_planned
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
      FILTER j.phase_key == LAST(wo.phase_sequence)
      RETURN j.qt_released
    )

    // Update PT and Cost
    LET processing_time = SUM(
      FOR ws IN WorkSession
      FILTER ws.work_order_key == @wo_key
      RETURN ws.duration
    )

    LET processing_cost = SUM(
      FOR ws IN WorkSession
      FILTER ws.work_order_key == @wo_key
      RETURN ws.duration * ws.hourly_cost
    )

    // Check if any WO Job is still open
    LET still_open = TO_BOOL(COUNT(FOR j IN jobs FILTER j.stage != 'closed' RETURN 1))
    LET status = still_open ? 'started' : 'closed'

    LET end = still_open ? null : DATE_ISO8601(now)

    // Calculate Throughput Time and Lead Time at Work order Closure
    LET lead_time = still_open ? null : DATE_DIFF(wo.created, now, 'f')
    LET throughput_time = still_open ? null : DATE_DIFF(wo.start, now, 'f')

    // Apply changes and return updated record
    UPDATE wo WITH {

      progress,
      active,
      qt_completed,
      status,
      end,
      processing_time,
      processing_cost,
      throughput_time,
      lead_time

    } IN WorkOrder RETURN NEW
  """


  UPDATE_JOB_PROGRESS = """
    LET j = DOCUMENT(Job, @job_key)
    LET should_count_step_progress = j.parameters.step_check && TO_BOOL(j.current_batch)

    LET step_progress = !should_count_step_progress ? 0 : FIRST(
      LET default_batch = j.parameters.production_batch_qt
      LET remaining_qt = j.qt_planned - j.qt_completed
      LET batch_qt = MIN([default_batch, remaining_qt])
      LET current_batch_total_value = batch_qt / j.qt_planned
      LET step_progress_value = current_batch_total_value / LENGTH(j.step_sequence)
      LET step_done_count = SUM(
        FOR s IN StepExecutionData
        FILTER s.batch_key == j.current_batch && s.status == 'done'
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
      FILTER ws.batch_key == @batch_key
      RETURN ws
    )

    LET unit_processing_time = SUM(
      FOR ws IN work_sessions
      RETURN ws.duration
    ) / @qt_pass

    // To be added when material cost will be handled
    LET material_cost = 0

    LET processing_cost = SUM(
      FOR ws IN work_sessions
      RETURN ws.duration * ws.hourly_cost
    )


    UPDATE batch WITH {
      qt_pass: @qt_pass,
      active: false,
      end: @end,
      unit_processing_time,
      unit_processing_cost: processing_cost / @qt_pass,
      value: processing_cost + material_cost

    } in Batch
  """


  CLOSE_WORK_SESSION = """
    LET ws_key = (
      FOR j IN Job
      FILTER j._key == @job_key
      RETURN j.last_work_session_started
    )[0]

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

  UPDATE_NEXT_BATCH_AVAILABLE_STATE_FOR_JOBS_IN_PHASE = """
    // Get input available for any job in phase
    LET input_for_phase = SUM(
      FOR w IN wip
      FILTER
        w.wo_key == @wo_key
        && w._to == CONCAT('Phase/', @phase_key)
      RETURN w.quantity
    )

    FOR j IN Job
    FILTER j.wo_key == @wo_key && j.phase_key == @phase_key

    // Get input available from that already booked for the job
    LET input_for_job = SUM(
      FOR w IN wip
      FILTER
        w.wo_key == @wo_key
        && w._to == j._id
        && !w.active
      RETURN w.quantity
    )

    LET total_input_available = input_for_phase + input_for_job
    LET next_batch_available = j.first_phase || j.qt_next_batch <= total_input_available
    UPDATE j WITH { next_batch_available } IN Job
  """

  RETRIEVE_AVAILABLE_WIP = """
    FOR w IN wip
    FILTER w._to == CONCAT('Phase/', @phase_key)
    SORT w.batch_key
    RETURN w
  """


# ------------- END OF QUERIES CLASS ----------------------------------


def update_job_progress(db, job_key):
  db.aql.execute(Queries.UPDATE_JOB_PROGRESS, bind_vars=dict(job_key=job_key))


