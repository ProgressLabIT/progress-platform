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
      LET qt_remaining = wo.qt_planned - wo.qt_completed
      LET jobs = ( FOR j IN Job FILTER !j.trash && j.wo_id == wo._id RETURN j)
      LET phases = ( FOR j IN jobs RETURN DISTINCT j.phase_id )
      LET progress = FLOOR(AVERAGE(
        FOR phase IN phases 
          RETURN AVERAGE(
            FOR j IN jobs
            FILTER j.phase_id == phase
            RETURN j.progress
          )
      ))
      LET active = TO_BOOL(SUM(FOR j IN jobs FILTER j.active RETURN 1))
      RETURN MERGE ([wo, { qt_remaining: qt_remaining, active: active, progress: progress }])  
  """

  GET_WORK_ORDER_DATA = """
    FOR wo IN WorkOrder
      FILTER wo._key == @wo_key

      // get job data
      LET jobs =  ( 
        FOR j IN Job
        FILTER j.wo_id == wo._id && !j.trash
        LET operator = KEEP(DOCUMENT(j.assigned_to), '_id', 'name', 'surname', 'active')
        RETURN MERGE( j, { assigned_to: operator } )
      )

      // check if any job is active
      LET active = TO_BOOL(COUNT(FOR j IN jobs FILTER j.active RETURN 1))

      // calculate overall progress

      LET phases = ( FOR j IN jobs RETURN DISTINCT j.phase_id )
      LET progress = FLOOR(AVERAGE(
        FOR phase IN phases 
          RETURN AVERAGE(
            FOR j IN jobs
            FILTER j.phase_id == phase
            RETURN j.progress
          )
      ))

      // Return enriched wo data
      RETURN MERGE ([
        wo, { 
        jobs: jobs, 
        active: active,
        progress: progress
      }])
  """

  REORDER_JOB_QUEUES = """
    FOR q1 IN Queue
    FILTER q1.type == 's' && q1.site_key == '0'
    LET wo_queue = q1.work_orders

    FOR q IN Queue
    FILTER q.type != 's' && q.site_key == '0' && LENGTH(q.jobs)
        LET jobs = (
            FOR j IN q.jobs
            LET wo_key = PARSE_IDENTIFIER(DOCUMENT('Job', j).wo_id).key
            RETURN { 
                job_key: j, 
                wo_key, 
                wo_in_queue: POSITION(wo_queue, wo_key)
            }
        )
            
            
        LET new_queue = REMOVE_VALUE(
            FLATTEN( 
                FOR wo_key IN wo_queue
                LET wo_job = (FOR j IN jobs FILTER j.wo_key == wo_key RETURN j.job_key)
                RETURN wo_job
            ), null
        )
        
        UPDATE q WITH { jobs: new_queue } IN Queue
  """

  GET_ASSIGNMENT_LIST = """
    LET assigned_jobs_by_operator = (
      LET user_key = @user_key ? : '%'
      FOR o IN User
      FILTER CONTAINS(o.scope, 'operator') && LIKE(o._key, user_key)
      
      LET assigned_jobs = FIRST(    
        FOR q in Queue
        FILTER q.subqueue_target_id == o._id
        LET jobs = ( FOR j IN q.jobs RETURN DOCUMENT(Job, j) )
        RETURN jobs
      )
      
      RETURN {
        operator: KEEP(o, '_id', 'name', 'surname', 'active', 'department_id'),
        assigned_jobs: assigned_jobs
      }
    )

    LET unassigned_jobs = (
      FOR j in Job
      FILTER !j.trash && j.assigned_to == null
      RETURN j
    )

    RETURN {
      assigned_jobs_by_operator: assigned_jobs_by_operator,
      unassigned_jobs: unassigned_jobs
    }  
  """

  GET_PHASE_STEP_DATA = """
    FOR p IN Phase
    FILTER p._id == @phase_id
      FOR s IN p.step_sequence
      RETURN DOCUMENT(s)
  """

  REMOVE_JOB_FROM_QUEUE = """
    FOR j IN Job
    LET job_key = PARSE_IDENTIFIER(@job_id).key 
    FILTER j._key == job_key
    LET assignee = j.assigned_to
    
    FOR q IN Queue
    FILTER q.subqueue_target_id == assignee
    UPDATE q WITH { jobs: REMOVE_VALUE(q.jobs, job_key) } in Queue
  """

  ADD_JOB_TO_QUEUE = """
    LET job_key = PARSE_IDENTIFIER(@job_id).key 
    FOR q IN Queue
    FILTER q.subqueue_target_id == @target_id
    
    // the third parameter = true makes sure the job is added only if not already present
    UPDATE q WITH { jobs: PUSH(q.jobs, job_key, true) } in Queue
  """
