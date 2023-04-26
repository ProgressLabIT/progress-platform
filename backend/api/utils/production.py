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
      LET jobs = (FOR j IN Job FILTER !j.trash && j.wo_key == wo._key RETURN j)
      LET phases = (FOR j IN jobs RETURN DISTINCT j.phase_key)
      LET issue_count = COUNT(FOR i IN issue_rel FILTER i._to == wo._id RETURN 1)
      RETURN MERGE (wo, { qt_remaining: qt_remaining, issue_count })
  """

  GET_WORK_ORDER_DATA = """
    LET now = DATE_NOW()

    FOR wo IN WorkOrder
      FILTER wo._key == @wo_key

      // get job data
      LET jobs =  ( 
        FOR j IN Job
        FILTER j.wo_key == wo._key && !j.trash
        LET operator = KEEP(DOCUMENT(User, j.assigned_to), '_key', 'name', 'surname', 'active')
        LET work_sessions = (
          FOR ws IN WorkSession
          FILTER ws.job_key == j._key && !ws.canceled
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

    LET jobs = (
        FOR j IN Job
        FILTER j.stage != 'closed'
        RETURN j
    )

    // Process Job queues
    FOR q IN Queue
    FILTER
      q.type == "o"
      && (q.site_key == @site_key || "0")
      && (@target_key ? q.subqueue_target_key == @target_key : true)
      && LENGTH(q.jobs)

    LET new_queue = REMOVE_VALUE(
      FLATTEN(
        FOR wo IN wo_queue
          FOR phase IN wo.phase_sequence
            FOR j IN jobs
            FILTER
              j.wo_key == wo._key
              && j.phase_key == phase
              && j.assigned_to == q.subqueue_target_key
            RETURN j._key
      ), null
    )

    UPDATE q WITH { jobs: new_queue } in Queue
  """

  GET_ASSIGNMENT_LIST = """
    LET assigned_jobs_by_operator = (
      LET user_key = @user_key ? : '%'
      FOR o IN User
      FILTER CONTAINS(o.scope, 'operator') && LIKE(o._key, user_key)

      LET assigned_jobs = FIRST(
        FOR q in Queue
        FILTER q.subqueue_target_key == o._key
        LET jobs = (
          FOR j IN q.jobs
          LET issue_count = COUNT(FOR i IN issue_rel FILTER i._to == CONCAT('Job/', j) RETURN 1)
          RETURN MERGE(DOCUMENT(Job, j), { issue_count })
        )
        RETURN jobs
      )
      
      RETURN {
        operator: KEEP(o, '_key', 'name', 'surname', 'active', 'department_key'),
        assigned_jobs: assigned_jobs
      }
    )

    LET unassigned_jobs = (
      LET wo_queue = FIRST(FOR q IN Queue FILTER q.type == 's' RETURN q.work_orders)
      
      FOR j in Job
        FILTER !j.trash && j.assigned_to == null
        
        // Order by WorkOrder Queue position and Phase sequence
        LET wo_queue_index = POSITION(wo_queue, j.wo_key, true)
        LET wo_phase_sequence = DOCUMENT(WorkOrder, j.wo_key).phase_sequence
        LET job_phase_index = POSITION(wo_phase_sequence, j.phase_key, true)
        SORT wo_queue_index, job_phase_index
      
        RETURN MERGE(j, { issue_count: 0 })
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
