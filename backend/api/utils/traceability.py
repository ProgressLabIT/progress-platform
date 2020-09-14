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