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
      LET jobs = ( FOR j IN Job FILTER !j.trash && j.wo_key == wo._key RETURN j)
      LET phases = ( FOR j IN jobs RETURN DISTINCT j.phase_key )
      LET active = TO_BOOL(SUM(FOR j IN jobs FILTER j.active RETURN 1))
      RETURN MERGE ([wo, { qt_remaining: qt_remaining, active: active }])  
  """

  GET_WORK_ORDER_DATA = """
    FOR wo IN WorkOrder
      FILTER wo._key == @wo_key

      // get job data
      LET jobs =  ( 
        FOR j IN Job
        FILTER j.wo_key == wo._key && !j.trash
        LET operator = KEEP(DOCUMENT(User, j.assigned_to), '_key', 'name', 'surname', 'active')
        RETURN MERGE( j, { assigned_to: operator } )
      )

      // Return enriched wo data
      RETURN MERGE(wo, { jobs })
  """


  REORDER_JOB_QUEUES = """
    FOR q1 IN Queue
    FILTER q1.type == 's' && q1.site_key == '0'
    LET wo_queue = q1.work_orders

    FOR q IN Queue
    FILTER q.type != 's' && q.site_key == '0' && LENGTH(q.jobs)
      LET jobs = (
        FOR j IN q.jobs
        LET wo_key = DOCUMENT('Job', j).wo_key
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
        FILTER q.subqueue_target_key == o._key
        LET jobs = ( FOR j IN q.jobs RETURN DOCUMENT(Job, j) )
        RETURN jobs
      )
      
      RETURN {
        operator: KEEP(o, '_key', 'name', 'surname', 'active', 'department_key'),
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
