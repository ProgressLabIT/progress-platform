class Queries:

  GET_BATCH_EXECUTION_DATA = """
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