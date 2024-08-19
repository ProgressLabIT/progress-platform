from collections import deque

from events.base import BaseEvent
from events.shared import EventMeta
from models.production import Job, WorkStatus
from commons.models.traceability import Batch, WIP, WorkSession
from commons.utils.serial import Queries as SerialQueries

from utils.exceptions import (
  JobHasActiveBatchError,
  JobHasNoActiveBatchError,
  JobHasNoAssigneeError,
  JobIsNotStartedError,
  JobIsActiveError,
  QuantityOverrideForSerialsNotAllowed,
  WipNotAvailableError
)
from utils.production import Queries as ProductionQueries
from utils.traceability import Queries as TraceabilityQueries


class Queries:
  CANCEL_JOB_WORK_SESSIONS = """
    FOR ws IN WorkSession
    FILTER ws.job_key == @job_key && !ws.canceled
    UPDATE ws WITH { canceled: @event_id } IN WorkSession
    RETURN NEW
  """
  NON_CANCELED_BATCHES_BY_JOB = """
    LET now = DATE_NOW()

    FOR b IN Batch
    FILTER b.job_key == @job_key && !b.canceled
    SORT b.end DESC
    RETURN b
    """

class ProductionAdminEvent(BaseEvent):

  # =====================================================================================
  # UTILITIES
  # =====================================================================================
  
  def flag_job_as_forced(self):
    job_update = dict(_key=self.info.job_key, forced=self.info.id)
    self.tx.collection('Job').update(job_update)

  # =====================================================================================
  # TIME OVERRIDE
  # =====================================================================================

  TIME_OVERRIDE_REQUESTED = EventMeta(
    collections=['Job', 'Batch', 'WorkSession', 'WorkOrder', 'Queue'],
    action="override_time",
    post_processing=['update_work_order', 'flag_job_as_forced'],
    event_first = True
  )

  # -----------------------------------------------------

  def override_time(self):
    job_key = self.info.job_key

    self.job = Job(**self.tx.document(f'Job/{job_key}'))

    if self.job.active:
      raise JobIsActiveError("You can't override processing time while the job is still active")

    if self.job.stage == WorkStatus.CREATED:
      raise JobIsNotStartedError("You can't override processing time if the job hasn't started yet")

    # Store work order key for later update
    if not 'work_order_key' in self.info:
      self.info.work_order_key = self.job.wo_key

    # Cancel existing job work sessions, while fetching data
    # for calculation of weighted average hourly cost
    self.tx.aql.execute(
      Queries.CANCEL_JOB_WORK_SESSIONS,
      bind_vars=dict(job_key=job_key, event_id=self.info.id)
    )

    # Define hourly cost as defined for the operator
    operator_data = self.tx.collection('User').get(self.job.assigned_to)
    hourly_cost = operator_data.get('hourly_cost', 0)

    # Get job batches to update
    match = dict(job_key=job_key, canceled=None)
    cursor = self.tx.collection('Batch').find(match)
    job_batches = [Batch(**b) for b in cursor]

    # Define new duration, either the one provided or using unit standard time for phase
    if hasattr(self.info, 'new_job_duration'):
      new_job_duration = self.info.new_job_duration
    else: #
      new_job_duration = self.job.parameters.std_processing_time * self.job.qt_completed

    # Insert manual work session for each batch of the job
    new_work_sessions = []
    batch_updates = []

    for b in job_batches:
      try:
        batch_quota = b.qt_total / self.job.qt_completed
      # Handle cases where there's active quantity but no completed quantity
      except ZeroDivisionError:
        batch_quota = 1

      batch_duration = int(new_job_duration * batch_quota) # it's milliseconds, no need for decimals here

      batch_update = dict(
        _key = b.key,
        forced = self.info.id
      )

      batch_updates.append(batch_update)

      forced_work_session = WorkSession(
        batch_key = b.key,
        job_key = job_key,
        work_order_key = self.info.work_order_key,
        phase_key = self.job.phase_key,
        product_key = self.job.product_key,
        duration = batch_duration,
        forced = self.info.id,
        hourly_cost = hourly_cost
      )

      new_work_sessions.append(forced_work_session.dict(exclude={'key', 'id', 'rev'}))

    self.tx.collection('WorkSession').insert_many(new_work_sessions)
    self.tx.collection('Batch').update_many(batch_updates)

  # =========================================================================
  # PROGRESS OVERRIDE
  # =========================================================================

  PROGRESS_OVERRIDE_REQUESTED = EventMeta(
    collections=['Job', 'Batch', 'Queue', 'WorkSession', 'WorkOrder', 'wip', 'requires'],
    action='override_progress',
    post_processing=['update_work_order', 'flag_job_as_forced'],
    event_first = True
  )

  # -----------------------------------------------------

  def _calculate_avg_unit_processing_time(self):
    return self.tx.aql.execute(
      """
      RETURN AVG(
        FOR b IN Batch
        FILTER b.job_key == @job_key && !b.canceled
        SORT b.end DESC
        LET total_duration = SUM(
          FOR ws IN WorkSession
          FILTER ws.batch_key == b._key && !ws.canceled
          RETURN ws.duration
        )
        RETURN total_duration / b.qt_pass
      )
      """,
      bind_vars=dict(job_key=self.job.key)
    ).next()

  def _create_forced_traceability_records(self, quantity, duration=None, unit_processing_time=None):
    """
    1. Create new batch with:
    - qt_pass/qt_total: provided quantity
    - start/end: timestamp
    - forced: event id
    - unit_processing_time: average if available or standard time
    - unit_processing_cost: average if available or 0

    2. Create associated work session with:
    - start/end/user_key/user_session_key = None
    - duration: as provided or standard time * quantity_update
    - hourly cost based on user input or weighted average of other sessions
    - forced: event id

    3. Create free wip downstream, if not last phase

    ASSUMPTION: Event id, job data etc are already stored in the event class
    """
    if not unit_processing_time:
      unit_processing_time = self._calculate_avg_unit_processing_time() or self.job.parameters.std_processing_time

    operator_data = self.tx.collection('User').get(self.job.assigned_to)
    hourly_cost = operator_data.get('hourly_cost', 0)

    unit_processing_cost = (0 if hourly_cost is None else hourly_cost) * unit_processing_time
    batch_value = unit_processing_cost * quantity

    new_batch_data = Batch(
      job_key = self.job.key,
      work_order_key = self.job.wo_key,
      phase_key = self.job.phase_key,
      active = False,
      start = self.info.timestamp,
      end = self.info.timestamp,
      qt_pass = quantity,
      qt_total = quantity,
      value = batch_value,
      forced = self.info.id
    )

    new_batch_key = self.tx.collection('Batch').insert(new_batch_data)['_key']

    new_work_sessions_data = WorkSession(
      batch_key = new_batch_key,
      job_key = self.job.key,
      phase_key = self.job.phase_key,
      work_order_key = self.job.wo_key,
      product_key = self.job.product_key,
      hourly_cost = hourly_cost,
      duration = duration or (unit_processing_time * quantity),
      forced = self.info.id
    )

    self.tx.collection('WorkSession').insert(new_work_sessions_data)

    if not self.job.last_phase:
      new_wip = WIP(
        _from = f"Phase/{self.job.phase_key}",
        _to = f"Phase/{self.wip['next_phase_key']}",
        batch_key = new_batch_key,
        wo_key = self.job.wo_key,
        product_key = self.job.product_key,
        quantity = quantity,
        value = batch_value,
        active = False,
      )

      self.tx.collection('wip').insert(new_wip)

    return new_batch_key, batch_value

  # -----------------------------------------------------

  def override_progress(self):
    # TODO: handle StepExecutionData
    # shouldn't be able to increase the quantity if required fields are present in the process
    # decreasing the quantity should cancel StepExecutionData of the canceled batches

    self.job = Job(**self.tx.collection('Job').get(self.info.job_key))

    if self.job.assigned_to == None:
      raise JobHasNoAssigneeError("You can't declare progress without associating it to a user. Assign the job first.")

    if self.job.active:
      raise JobIsActiveError("You can't override progress while the job is active")

    if self.job.active_batch_qt:
      raise JobHasActiveBatchError("You can't override progress if the job has an active batch. Cancel the current batch first.")
    
    if self.job.traceability_level:
      raise QuantityOverrideForSerialsNotAllowed("You can't override progress with traceability enabled, you can reset the job instead.")

    # Initialize job update.
    # Will save at the end after enrichment based on override type

    new_job_progress = round(100 * self.info.new_job_qt_completed / self.job.qt_planned)

    job_update = dict(
      _key = self.job.key,
      qt_completed = self.info.new_job_qt_completed,
      qt_released = self.info.new_job_qt_completed,
      progress = new_job_progress,
      forced = self.info.id
    )

    # Get available wip data
    bind_vars = dict(job_key=self.info.job_key)
    self.wip = self.tx.aql.execute(
      TraceabilityQueries.GET_AVAILABLE_WIP_UPSTREAM_AND_DOWNSTREAM_OF_JOB,
      bind_vars = bind_vars
    ).next()

    free_wip_qt_upstream = sum(w['quantity'] for w in self.wip['upstream_free_wip'])
    free_wip_qt_downstream = sum(w['quantity'] for w in self.wip['downstream_free_wip'])

    # Check quantity delta
    quantity_update = self.info.new_job_qt_completed - self.job.qt_completed

    # No quantity change
    if not quantity_update:
      raise ValueError('No quantity change')

    elif self.info.new_job_qt_completed > self.job.qt_planned:
      raise ValueError('Quantity is higher than the total planned')

    total_duration = self.tx.aql.execute(
      """
      RETURN SUM(
        FOR ws IN WorkSession
        FILTER ws.job_key == @job_key && !ws.canceled
        RETURN ws.duration
      )
      """,
      bind_vars = dict(job_key=self.job.key)
    ).next()

    # Progress increase: check there's wip available to pick from
    if quantity_update > 0:
      if quantity_update > free_wip_qt_upstream and not self.job.first_phase:
        raise WipNotAvailableError("The previous phase has not made enough progress to make this change")

      # Set job as started if not already
      if self.job.stage == WorkStatus.CREATED:
        job_update['stage'] = WorkStatus.STARTED
        job_update['start'] = self.info.timestamp

      # Set job as closed and remove it from queues if necessary
      if self.info.new_job_qt_completed == self.job.qt_planned:
        job_update['stage'] = WorkStatus.CLOSED
        job_update['end'] = self.info.timestamp
        self.tx.aql.execute(
          ProductionQueries.REMOVE_JOB_FROM_QUEUE,
          bind_vars = dict(
            target_key = self.job.assigned_to,
            job_key = self.job.key
          )
        )

      # 2. Create forced batch, work_session and downstream wip:
      if self.info.should_adjust_duration:
        new_batch_key, batch_value = self._create_forced_traceability_records(quantity_update)
      else:
        # Cancel all work sessions to recreate them with the new durations
        ws_cursor = self.tx.aql.execute(
          Queries.CANCEL_JOB_WORK_SESSIONS,
          bind_vars = dict(
            job_key = self.job.key,
            event_id = self.info.id
          )
        )
        canceled_work_sessions = [WorkSession(**ws) for ws in ws_cursor]

        # distribute total processing time evenly per each batch
        # create a new work session for each existing batch with the split duration
        active_batches_cursor = self.tx.aql.execute(
          Queries.NON_CANCELED_BATCHES_BY_JOB,
          bind_vars=dict(job_key=self.job.key)
        )
        active_batches = [Batch(**b) for b in active_batches_cursor]

        work_session_amount_ratio = 1 if not active_batches else len(canceled_work_sessions) / len(active_batches)
        average_hourly_cost = 0 if not canceled_work_sessions else sum(ws.hourly_cost or 0 for ws in canceled_work_sessions) / len(canceled_work_sessions) * work_session_amount_ratio
        new_work_sessions = []
        for batch in active_batches:
          quantity_ratio = batch.qt_pass / self.info.new_job_qt_completed
          work_session = WorkSession(
            batch_key = batch.key,
            job_key = self.job.key,
            phase_key = self.job.phase_key,
            work_order_key = self.job.wo_key,
            product_key = self.job.product_key,
            hourly_cost = average_hourly_cost,
            duration = int(total_duration * quantity_ratio),
            forced = self.info.id
          )
          new_work_sessions.append(
            work_session.dict(exclude={'key', 'id', 'rev'})
          )

        self.tx.collection('WorkSession').insert_many(new_work_sessions)

        # For the increased quantity, create a new batch/work session/wip, use the leftover duration
        quantity_ratio = quantity_update / self.info.new_job_qt_completed
        new_batch_key, batch_value = self._create_forced_traceability_records(
          quantity=quantity_update,
          duration=total_duration * quantity_ratio
        )

      # 3. Delete free wip from previous phase to current (if not first phase)
      if not self.job.first_phase:
        remaining_wip_to_remove = abs(quantity_update)
        wip_records = deque(self.wip['upstream_free_wip'])
        records_to_delete = deque()

        while remaining_wip_to_remove:
          current_wip = wip_records.popleft()

          if current_wip['quantity'] <= remaining_wip_to_remove:
            records_to_delete.append(current_wip)
            remaining_wip_to_remove -= current_wip['quantity']

          else:
            leftover_wip = current_wip['quantity'] - remaining_wip_to_remove
            wip_update = dict(_key=current_wip['_key'], quantity=leftover_wip)
            self.tx.collection('wip').update(wip_update)
            remaining_wip_to_remove = 0

        self.tx.collection('wip').delete_many(records_to_delete)

    else: # quantity_update < 0, Progress decrease: check enough wip downstream has not already been booked/used
      if abs(quantity_update) > free_wip_qt_downstream and not self.job.last_phase:
        raise WipNotAvailableError("You can't reduce the released quantity of this phase below that already completed/started/booked from the following phase")

      # Reopen job and restore it into queue if closed
      if self.job.stage == WorkStatus.CLOSED:
        job_update['stage'] = WorkStatus.STARTED
        job_update['end'] = None

      # Reset job to created status if necessary
      if self.info.new_job_qt_completed == 0:
        job_update['stage'] = WorkStatus.CREATED

      # 2. Flag last N batches with `canceled: true`
      job_batches_cursor = self.tx.aql.execute(
        Queries.NON_CANCELED_BATCHES_BY_JOB,
        bind_vars=dict(job_key=self.job.key)
      )
      job_batches = deque(Batch(**b) for b in job_batches_cursor)
      remaining_qt_to_remove = abs(quantity_update)
      batches_to_cancel = deque()

      # Here we'll cancel only full batches.
      # remaining_qt_to_remove can become negative, will compensate later on
      while remaining_qt_to_remove > 0:
        current_batch = job_batches.popleft()
        current_batch.canceled = self.info.id
        batches_to_cancel.append(current_batch)
        remaining_qt_to_remove -= current_batch.qt_pass

      avg_unit_processing_time = None
      # If we will end up canceling all batches, calculate the average unit processing time before executing the canceling query
      if not job_batches:
        avg_unit_processing_time = self._calculate_avg_unit_processing_time()

      batch_updates = [b.dict(by_alias=True) for b in batches_to_cancel]
      self.tx.collection('Batch').update_many(batch_updates)
      canceled_batches_keys = [b.key for b in batches_to_cancel]

      if self.info.should_adjust_duration:
        # 3. Flag the work sessions of the canceled batches with `canceled: true`
        self.tx.aql.execute(
          """
          FOR ws IN WorkSession
          FILTER ws.batch_key IN @canceled_batches_keys
          UPDATE ws WITH { canceled: @event_id } in WorkSession
          """,
          bind_vars = dict(
            canceled_batches_keys = canceled_batches_keys,
            event_id = self.info.id
          )
        )
      else:
        # 3. Flag all work sessions with `canceled: true`
        ws_cursor = self.tx.aql.execute(
          Queries.CANCEL_JOB_WORK_SESSIONS,
          bind_vars = dict(
            job_key = self.job.key,
            event_id = self.info.id
          )
        )
        canceled_work_sessions = [WorkSession(**ws) for ws in ws_cursor]

        # distribute total processing time evenly per each batch
        # create a new work session for each existing batch with the split duration
        active_batches_cursor = self.tx.aql.execute(
          Queries.NON_CANCELED_BATCHES_BY_JOB,
          bind_vars=dict(job_key=self.job.key)
        )
        active_batches = [Batch(**b) for b in active_batches_cursor]

        # Split the total processing time evenly per each non-canceled batch
        # and create a new work session for each one with the split duration
        work_session_amount_ratio = 1 if not active_batches else len(canceled_work_sessions) / len(active_batches)
        average_hourly_cost = 0 if not canceled_work_sessions else sum(ws.hourly_cost or 0 for ws in canceled_work_sessions) / len(canceled_work_sessions) * work_session_amount_ratio
        new_work_sessions = []
        for batch in job_batches:
          quantity_ratio = batch.qt_pass / self.info.new_job_qt_completed
          work_session = WorkSession(
            batch_key = batch.key,
            job_key = self.job.key,
            phase_key = self.job.phase_key,
            work_order_key = self.job.wo_key,
            product_key = self.job.product_key,
            hourly_cost = average_hourly_cost,
            duration = total_duration * quantity_ratio,
            forced = self.info.id
          )
          new_work_sessions.append(work_session.dict(exclude={'key', 'id', 'rev'}))

        self.tx.collection('WorkSession').insert_many(new_work_sessions)

        # If remaining_qt_to_remove < 0, we'll have to create a new batch with lesser quantity than the others
        # So, while splitting the total processing time, we'll have to account for that (see #5 below)

      # 4. Delete wip to next phase related to canceled batches (if not last phase)
      if not self.job.last_phase:
        self.tx.aql.execute(
          """
          FOR w IN wip
          FILTER
            w.batch_key IN @canceled_batches_keys
            && PARSE_IDENTIFIER(w._to).collection == 'Phase'
          REMOVE w IN wip
          """,
          bind_vars = dict(canceled_batches_keys=canceled_batches_keys)
        )

      # 5. If we canceled more than required, create a forced batch/work session/wip to compensate
      if remaining_qt_to_remove < 0:
        quantity_ratio = abs(remaining_qt_to_remove) / self.info.new_job_qt_completed
        duration_to_preserve_total = total_duration * quantity_ratio
        new_batch_key, batch_value = self._create_forced_traceability_records(
          quantity=abs(remaining_qt_to_remove),
          duration=duration_to_preserve_total if not self.info.should_adjust_duration else None,
          unit_processing_time=avg_unit_processing_time
        )

        # Update potential booked wip from canceled batches
        self.tx.aql.execute(
          """
          FOR w IN wip
          FILTER
            w.batch_key IN @canceled_batches_keys
            && PARSE_IDENTIFIER(w._to).collection == "Job"
          UPDATE w WITH { batch_key: @new_batch_key } in wip
          """,
          bind_vars = dict(
            canceled_batches_keys = canceled_batches_keys,
            new_batch_key = new_batch_key
          )
        )

      # 6. Add free wip from previous phase to current (If not first phase)
      # New wip must be associated to batches from the previous phase,
      # starting from the last completed and going backwards
      if not self.job.first_phase:
        cursor = self.tx.aql.execute(
          """
          FOR b IN Batch
          FILTER
            b.work_order_key == @work_order_key
            && b.phase_key == @phase_key
            && !b.canceled
          SORT b.end DESC
          RETURN b
          """,
          bind_vars = dict(
            work_order_key = self.job.wo_key,
            phase_key = self.wip['previous_phase_key']
          )
        )
        batches_from_previous_phase = deque(Batch(**b) for b in cursor)
        wip_to_add = abs(quantity_update)

        while wip_to_add:
          wip_batch = batches_from_previous_phase.popleft()
          # Wip quantity can be less than batch quantity
          wip_quantity = min([wip_to_add, wip_batch.qt_pass])

          new_wip = WIP(
            _from = f"Phase/{self.wip['previous_phase_key']}",
            _to = f"Phase/{self.job.phase_key}",
            batch_key = wip_batch.key,
            wo_key = self.job.wo_key,
            product_key = self.job.product_key,
            quantity = wip_quantity,
            value = wip_batch.value * wip_quantity / wip_batch.qt_pass,
            active = False,
          )
          self.tx.collection('wip').insert(new_wip)
          wip_to_add -= wip_quantity


    self.tx.collection('Job').update(job_update)

    if self.job.stage == WorkStatus.CLOSED and quantity_update < 0:
      self.tx.aql.execute(ProductionQueries.ADD_JOB_TO_QUEUE,
        bind_vars = dict(
          job_key = self.job.key,
          target_key = self.job.assigned_to
        )
      )
      self.tx.aql.execute(
        ProductionQueries.REORDER_JOB_QUEUES,
        bind_vars = dict(
          site_key = '0',
          target_key = self.job.assigned_to
        )
      )

    # Update batch available state for current and next phase (if present)
    wip_phases = [self.job.phase_key]

    if not self.job.last_phase:
      wip_phases.append(self.wip['next_phase_key'])

    self.tx.aql.execute(
      TraceabilityQueries.UPDATE_NEXT_BATCH_AVAILABLE_STATE_FOR_JOBS_IN_PHASES,
      bind_vars=dict(
        wo_key = self.job.wo_key,
        phase_keys = wip_phases
      )
    )



  # ========================================================================

  BATCH_CANCELED = EventMeta(
    collections = ['Batch', 'batch_serial', 'Job', 'Serial', 'StepExecutionData', 'wip', 'WorkOrder', 'WorkSession'],
    action='cancel_batch',
    post_processing=['update_work_order', 'flag_job_as_forced'],
    event_first = True
  )

  def cancel_batch(self):
    self.get_job_data()

    if self.job.active:
      raise JobIsActiveError("You can't cancel a batch while it's being worked on")

    if self.job.active_batch_qt == 0:
      raise JobHasNoActiveBatchError("The job has no active batch to cancel")

    # Cancel batch
    batch_key = self.job.active_batch_key
    batch_update = dict(
      _key = batch_key,
      active = False,
      end = self.info.timestamp,
      canceled = self.info.id
    )
    self.tx.collection('Batch').update(batch_update)

    # Cancel StepExecutionData & WorkSession records
    match = dict(batch_key = batch_key)
    update = dict(canceled = self.info.id)
    self.tx.collection('StepExecutionData').update_match(match, update)
    self.tx.collection('WorkSession').update_match(match, update)

    # Free booked wip
    if not self.job.first_phase:
      wip_match = dict(_to=f'Job/{self.job.key}', active=True)
      wip_update = dict(_to=f'Phase/{self.job.phase_key}', active=False)
      self.tx.collection('wip').update_match(wip_match, wip_update)
      self.tx.aql.execute(
        TraceabilityQueries.UPDATE_NEXT_BATCH_AVAILABLE_STATE_FOR_JOBS_IN_PHASES,
        bind_vars=dict(
          wo_key = self.job.wo_key,
          phase_keys = [self.job.phase_key]
        )
      )
    elif self.job.traceability_level: 
      # self.job.first_phase = True
      # Remove incomplete serials and the relative link. 
      # TODO: use a named graph to avoid deleting links explicitly
      self.tx.aql.execute("""
        FOR serial IN 1..1 OUTBOUND CONCAT('Batch/', @batch_key) batch_serial
        REMOVE serial IN Serial
      """, bind_vars=dict(batch_key=batch_key))

    if self.job.traceability_level: # both first and following phases
      # Remove obsolete batch_serial records and reset phase serial data
      # Remember that serials documents have already been removed
      serials_cursor = self.tx.aql.execute("""
        FOR s, bs IN 1..1 OUTBOUND CONCAT('Batch/', @batch_key) batch_serial
        REMOVE bs IN batch_serial                 
        LET removed = OLD
        RETURN PARSE_IDENTIFIER(OLD._to).key
      """, bind_vars=dict(batch_key=batch_key))

      batch_serial_keys = [serial_key for serial_key in serials_cursor]
      
      self.tx.aql.execute(
        SerialQueries.REMOVE_PHASE_DATA_FROM_SERIALS,
        bind_vars = dict(
          serial_keys = batch_serial_keys,
          phase_keys = [self.job.phase_key]
        )
      )

    # Update Job, removing progress from steps, if any, of former active batch
    job_update = dict(
      _key = self.job.key,
      active_batch_key = None,
      active_batch_qt = 0,
      progress = round(100 * self.job.qt_completed / self.job.qt_planned)
    )

    # Reset as created if batch is first
    if self.job.qt_completed == 0:
      job_update['stage'] = 'created'
      job_update['start'] = None

    self.tx.collection('Job').update(job_update)



  # ========================================================================

  JOB_RESET = EventMeta(
    collections = ['Batch', 'batch_serial', 'Job', 'Serial', 'StepExecutionData', 'wip', 'WorkOrder', 'WorkSession'],
    action='reset_job',
    post_processing=['update_work_order', 'flag_job_as_forced'],
    event_first = True
  )


  def reset_job(self):
    self.get_job_data()

    # Cancel Batches
    job_batches_cursor = self.tx.aql.execute("""
      FOR b IN Batch
      FILTER b.job_key == @job_key
      UPDATE b WITH { canceled: @event_key } IN Batch
      LET updated = NEW
      RETURN updated._key                                             
    """, bind_vars = dict(
      job_key = self.job.key, 
      event_key = self.info.id
    ))
    job_batch_keys = [b for b in job_batches_cursor]

    # Check there's enough free available downstream wip of job.last_phase before resetting the job
    available_wip = self.tx.aql.execute(
      TraceabilityQueries.GET_AVAILABLE_WIP_UPSTREAM_AND_DOWNSTREAM_OF_JOB,
      bind_vars = dict(job_key=self.job.key)
    ).next()

    free_wip_qt_downstream = sum(w['quantity'] for w in available_wip['downstream_free_wip'])

    if self.job.traceability_level:
      # Updates will be rolled back if the availability check will fail.

      # Delete Serial Links
      cursor = self.tx.aql.execute("""
        FOR b IN @batch_keys
        FOR s, e IN 1..1 OUTBOUND CONCAT('Batch/', b) batch_serial
        LET serial_key = s._key
        REMOVE e IN batch_serial
        RETURN serial_key
      """, bind_vars=dict(batch_keys=job_batch_keys))
      job_serial_keys = [s for s in cursor]

      # Check all serials are available in the phase buffer downstream
      wip_serials_count = self.tx.aql.execute("""
        FOR w IN wip
        FILTER 
          w.serial_key IN @job_serial_keys
          AND w._from == CONCAT('Phase/', @phase_key)
        RETURN 1
        """,
        bind_vars = dict(
          job_serial_keys = job_serial_keys,
          phase_key = self.job.phase_key
        ),
        count=True
      ).count()

      # Cancel Serials (if first phase)
      if self.job.first_phase:
        serial_updates = [dict(_key=s, deleted=True) for s in job_serial_keys]
        self.tx.collection('Serial').update_many(serial_updates)

      else:
        # Delete data from serials
        self.tx.aql.execute(
          SerialQueries.REMOVE_PHASE_DATA_FROM_SERIALS,
          bind_vars = dict(
            serial_keys = job_serial_keys,
            phase_keys = [self.job.phase_key]
          )
        )

        # Make serials available as wip from previous phase
        new_wip_records = [dict(
          _from = f"Phase/{available_wip['previous_phase_key']}",
          _to = f"Phase/{self.job.phase_key}",
          batch_key = None,
          wo_key = self.job.wo_key,
          product_key = self.job.product_key,
          quantity = 1,
          serial_key = s,
          forced = self.info.id
        ) for s in job_serial_keys]

        self.tx.collection('wip').insert_many(new_wip_records)

    else: # No traceability - updates will be rolled back if there's no availability
      # Add upstream wip
      self.tx.collection('wip').insert(dict(
        _from = f"Phase/{available_wip['previous_phase_key']}",
        _to = f"Phase/{self.job.phase_key}",
        batch_key = None,
        wo_key = self.job.wo_key,
        product_key = self.job.product_key,
        quantity = self.job.qt_released,
        forced = self.info.id
      ))

    availability_check_ref = wip_serials_count if self.job.traceability_level else free_wip_qt_downstream

    if not self.job.last_phase and availability_check_ref < self.job.qt_released:
      raise WipNotAvailableError("You can't reset the job because its output is being worked on in following phases. Reset those jobs first.")

    # Cancel StepExecutionData and WorkSession records
    match = dict(job_key = self.info.job_key)
    update = dict(canceled = self.info.id)
    self.tx.collection('StepExecutionData').update_match(match, update)
    self.tx.collection('WorkSession').update_match(match, update)

    # Delete downstream wip
    if not self.job.last_phase:
      self.tx.aql.execute("""
        FOR w IN wip
        FILTER w.batch_key in @batch_keys
        REMOVE w IN wip
      """, bind_vars=dict(batch_keys=job_batch_keys))

    # Update job as created
    job_update = dict(
      _key = self.info.job_key,
      qt_completed = 0,
      qt_released = 0,
      stage = 'created',
      start = None,
      end = None,
      progress = 0
    )
    self.tx.collection('Job').update(job_update)

