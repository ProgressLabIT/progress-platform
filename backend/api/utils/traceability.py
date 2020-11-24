from models.production import Job
from models.traceability import StepStatus
from models.process import StepCheckBatch

class Queries:

  GET_EVENTS = """
    FOR e IN Event
    FILTER e.wo_key
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


  CLOSE_JOB = """
    FOR j IN Job
    FILTER j._key == @job_key
    UPDATE j WITH {
      active: false,
      stage: @stage,
      current_batch: null,
      qt_completed: @qt_completed,
      qt_released: @qt_completed,
      progress: ROUND(100 * @qt_completed / j.qt_planned),
      end: @end
    } IN Job
  """

  UPDATE_WORK_ORDER = """
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

    // Check if any WO Job is still open
    LET still_open = TO_BOOL(COUNT(FOR j IN jobs FILTER j.stage != 'closed' RETURN 1))
    LET status = still_open ? 'started' : 'closed'

    UPDATE wo WITH { progress, active, qt_completed, status } IN WorkOrder

    // Return updated work order to allow further processing based on update
    LET updated_wo = NEW
    RETURN updated_wo
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

  NO_MORE_OPEN_JOBS_FOR_WORK_ORDER = """
    LET any_open_job = TO_BOOL(SUM(
      FOR j IN Job
      FILTER j.wo_key == @wo_key && j.status != 'closed'
      RETURN 1
    ))
    RETURN !any_open_job
  """

  GET_NEXT_SERIAL_NUMBER_FOR_WORK_ORDER = """
    LET wo_serials = (
      FOR s IN Serial
      FILTER s.wo_key == @wo_key
      RETURN s.counter
    )
    RETURN MAX(wo_serials) + 1
  """

  GET_NEXT_PHASE_IN_WORK_ORDER = """
    FOR wo IN WorkOrder
    FILTER wo._key == @wo_key
    LET next_phase_index = POSITION(wo.phase_sequence, @phase_key, true) + 1
    
    // if last phase of process return null
    RETURN next_phase_index < LENGTH(wo.phase_sequence) 
      ? wo.phase_sequence[next_phase_index]
      : null
  """

  UPDATE_INPUT_AVAILABLE_STATE_FOR_JOBS_IN_PHASE = """
    LET input_for_this_phase = SUM(
      FOR wip IN WIP
      FILTER wip.wo_key == @wo_key && wip._to == CONCAT('Phase/', @phase)
      RETURN wip.quantity
    )

    FOR j IN Job
    FILTER j.wo_key == @wo_key && j.phase_key == @phase
    LET next_batch_qt = MIN([j.qt_planned - j.qt_completed, j.parameters.production_batch_qt])
    LET input_available = next_batch_qt <= input_for_this_phase
    UPDATE j WITH { input_available } IN Job
  """

  RETRIEVE_AVAILABLE_WIP = """
    FOR wip IN WIP
    FILTER wip._to == CONCAT('Phase/', @phase)
    SORT wip.batch_key
    RETURN wip
  """


# ------------- END OF QUERIES CLASS ----------------------------------

def get_batch_step_done_count(batch_key, db):
  step_done_count = db.collection('StepExecutionData').find(dict(
    batch_key=batch_key,
    status=StepStatus.DONE
  )).count()

  return step_done_count
    

def get_job_progress(job_key, db): 
  job = Job(**db.collection('Job').get(job_key))
  progress = job.qt_completed / job.qt_planned

  if job.parameters.step_check != StepCheckBatch.NONE and job.current_batch:
    default_batch = job.parameters.production_batch_qt
    remaining_qt = job.qt_planned - job.qt_completed
    batch_qt = min([default_batch, remaining_qt])
    current_batch_total_value = batch_qt / job.qt_planned

    step_progress_value = current_batch_total_value / len(job.step_sequence)

    step_done_count = get_batch_step_done_count(
      batch_key=job.current_batch,
      db=db
    )
    
    progress += step_progress_value * step_done_count

  return round(progress*100)


def update_job_progress(db, job_key):
  db.aql.execute(Queries.UPDATE_JOB_PROGRESS, bind_vars=dict(job_key=job_key))



def get_phase_progress(wo_key, phase_key, db):
  phase_jobs_cursor = db.collection('Job').find(dict(
    wo_key=wo_key, 
    phase_key=phase_key)
  )
  phase_jobs = [Job(j) for j in phase_jobs_cursor]
  phase_weighted_average_progress = sum(j.progress * j.qt_planned for j in phase_jobs) / sum(j.qt_planned for j in phase_jobs)
  return phase_weighted_average_progress


